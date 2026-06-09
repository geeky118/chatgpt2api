from __future__ import annotations

import os
import posixpath
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import paramiko


ROOT = Path(__file__).resolve().parents[1]


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def require(name: str) -> str:
    value = env(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def run_local(args: list[str], *, cwd: Path = ROOT) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def ssh_client() -> paramiko.SSHClient:
    host = require("CHATGPT2API_SSH_HOST")
    user = env("CHATGPT2API_SSH_USER", "root")
    port = int(env("CHATGPT2API_SSH_PORT", "22"))
    password = env("CHATGPT2API_SSH_PASSWORD")
    key_path = env("CHATGPT2API_SSH_KEY")
    key_passphrase = env("CHATGPT2API_SSH_KEY_PASSPHRASE") or None

    kwargs: dict[str, object] = {
        "hostname": host,
        "username": user,
        "port": port,
        "timeout": 20,
        "banner_timeout": 20,
        "auth_timeout": 20,
    }
    if key_path:
        kwargs["key_filename"] = key_path
        if key_passphrase:
            kwargs["passphrase"] = key_passphrase
    elif password:
        kwargs["password"] = password
    else:
        raise SystemExit("Set CHATGPT2API_SSH_KEY or CHATGPT2API_SSH_PASSWORD")

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
    remote_dir = env("CHATGPT2API_REMOTE_DIR", "/opt/chatgpt2api")
    image_tag = env("CHATGPT2API_IMAGE_TAG", "chatgpt2api:local")
    git_ref = env("CHATGPT2API_GIT_REF", "HEAD")
    compose_file = env("CHATGPT2API_COMPOSE_FILE", f"{remote_dir}/docker-compose.yml")
    build_arg_canvas_url = env("NEXT_PUBLIC_INFINITE_CANVAS_URL", "https://canvas.hello4am.com/canvas")

    commit = run_local(["git", "rev-parse", "--short=12", git_ref])
    release_name = f"{commit}-{int(time.time())}"
    remote_releases = posixpath.join(remote_dir, "releases")
    remote_archive = posixpath.join(remote_releases, f"{release_name}.tar")
    remote_release = posixpath.join(remote_releases, release_name)

    with tempfile.TemporaryDirectory() as tmp:
        archive_path = Path(tmp) / f"chatgpt2api-{release_name}.tar"
        run_local(["git", "archive", "--format=tar", "-o", str(archive_path), git_ref])

        client = ssh_client()
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
                f"(docker compose -f {shlex.quote(compose_file)} up -d app "
                f"|| docker-compose -f {shlex.quote(compose_file)} up -d app)",
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
