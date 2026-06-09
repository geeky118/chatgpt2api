from __future__ import annotations

import os
import argparse
import posixpath
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import paramiko


ROOT = Path(__file__).resolve().parents[1]
SSH_HOST = "111.230.202.235"
SSH_USER = "root"


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def run_local(args: list[str], *, cwd: Path = ROOT) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deploy chatgpt2api to the production server.")
    parser.add_argument("--ssh-key", required=True, help="Path to the SSH private key.")
    parser.add_argument("--ssh-key-passphrase", default="", help="Optional passphrase for the SSH key.")
    parser.add_argument("--port", type=int, default=22, help="SSH port. Default: 22")
    return parser.parse_args()


def ssh_client(*, key_path: str, key_passphrase: str = "", port: int = 22) -> paramiko.SSHClient:
    key_passphrase = key_passphrase.strip() or None

    kwargs: dict[str, object] = {
        "hostname": SSH_HOST,
        "username": SSH_USER,
        "port": port,
        "timeout": 20,
        "banner_timeout": 20,
        "auth_timeout": 20,
    }
    kwargs["key_filename"] = key_path
    if key_passphrase:
        kwargs["passphrase"] = key_passphrase

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(**kwargs)
    return client


def exec_remote(client: paramiko.SSHClient, command: str, *, timeout: int = 600) -> str:
    print(f"$ {command}", flush=True)
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    if out:
        print(out.rstrip(), flush=True)
    if err:
        print(err.rstrip(), file=sys.stderr, flush=True)
    if code != 0:
        raise RuntimeError(f"Remote command failed ({code}): {command}")
    return out.strip()


def main() -> int:
    args = parse_args()
    remote_dir = env("CHATGPT2API_REMOTE_DIR", "/opt/chatgpt2api")
    image_tag = env("CHATGPT2API_IMAGE_TAG", "chatgpt2api:local")
    git_ref = env("CHATGPT2API_GIT_REF", "HEAD")
    compose_file = env("CHATGPT2API_COMPOSE_FILE", f"{remote_dir}/docker-compose.yml")
    build_arg_canvas_url = env("NEXT_PUBLIC_INFINITE_CANVAS_URL", "https://canvas.hello4am.com/canvas")
    mode = env("CHATGPT2API_DEPLOY_MODE", "build").lower()
    app_container = env("CHATGPT2API_APP_CONTAINER", "chatgpt2api-prod-app")
    patch_paths = [item.strip().replace("\\", "/") for item in env("CHATGPT2API_PATCH_PATHS").split(",") if item.strip()]

    commit = run_local(["git", "rev-parse", "--short=12", git_ref])
    release_name = f"{commit}-{int(time.time())}"
    remote_releases = posixpath.join(remote_dir, "releases")
    remote_archive = posixpath.join(remote_releases, f"{release_name}.tar")
    remote_release = posixpath.join(remote_releases, release_name)

    with tempfile.TemporaryDirectory() as tmp:
        archive_path = Path(tmp) / f"chatgpt2api-{release_name}.tar"
        run_local(["git", "archive", "--format=tar", "-o", str(archive_path), git_ref])

        client = ssh_client(key_path=args.ssh_key, key_passphrase=args.ssh_key_passphrase, port=args.port)
        try:
            exec_remote(client, f"mkdir -p {shlex.quote(remote_releases)}")
            print(f"Uploading {archive_path.name} -> {remote_archive}", flush=True)
            with client.open_sftp() as sftp:
                sftp.put(str(archive_path), remote_archive)

            exec_remote(
                client,
                "set -euo pipefail; "
                f"mkdir -p {shlex.quote(remote_release)}; "
                f"tar -xf {shlex.quote(remote_archive)} -C {shlex.quote(remote_release)}; "
                f"rm -f {shlex.quote(remote_archive)}",
            )
            if mode == "patch":
                if not patch_paths:
                    raise SystemExit("CHATGPT2API_PATCH_PATHS is required when CHATGPT2API_DEPLOY_MODE=patch")
                backup_tag = f"{image_tag}-before-{commit}-{int(time.time())}"
                exec_remote(client, f"docker tag {shlex.quote(image_tag)} {shlex.quote(backup_tag)}")
                for rel_path in patch_paths:
                    quoted_rel = shlex.quote(rel_path)
                    source = posixpath.join(remote_release, rel_path)
                    target = f"/app/{rel_path}"
                    exec_remote(
                        client,
                        "set -euo pipefail; "
                        f"test -f {shlex.quote(source)}; "
                        f"docker exec {shlex.quote(app_container)} mkdir -p {shlex.quote(posixpath.dirname(target))}; "
                        f"docker cp {shlex.quote(source)} {shlex.quote(app_container)}:{shlex.quote(target)}; "
                        f"case {quoted_rel} in *.py) docker exec {shlex.quote(app_container)} python -m py_compile {shlex.quote(target)} ;; esac",
                    )
                exec_remote(client, f"docker commit {shlex.quote(app_container)} {shlex.quote(image_tag)}", timeout=600)
            else:
                exec_remote(
                    client,
                    "set -euo pipefail; "
                    f"docker build --target app "
                    f"--build-arg NEXT_PUBLIC_INFINITE_CANVAS_URL={shlex.quote(build_arg_canvas_url)} "
                    f"-t {shlex.quote(image_tag)} {shlex.quote(remote_release)}",
                    timeout=1800,
                )
            exec_remote(
                client,
                "set -euo pipefail; "
                f"cd {shlex.quote(remote_dir)}; "
                f"{'docker rm -f ' + shlex.quote(app_container) + ' >/dev/null 2>&1 || true; ' if mode == 'patch' else ''}"
                f"docker compose -f {shlex.quote(compose_file)} up -d {'--force-recreate ' if mode != 'patch' else ''}app",
                timeout=600,
            )
            exec_remote(client, "docker ps --filter name=chatgpt2api-prod-app --format '{{.Names}} {{.Image}} {{.Status}}'")
            exec_remote(client, f"find {shlex.quote(remote_releases)} -mindepth 1 -maxdepth 1 -type d | sort | head -n -5 | xargs -r rm -rf")
        finally:
            client.close()

    print(f"Deployed {commit} to {remote_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
