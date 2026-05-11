#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_REPO_URL = "https://github.com/betonglg-ux/Agentglg.git"
DEFAULT_BRANCH = "main"
TOKEN_FILE_RELATIVE = Path("memory/agentglg-github-token.txt")
PRIVATE_TOKEN_FILE_RELATIVE = Path("memory/automation/private/agentglg-github-token.txt")
SYNC_STATE_FILE_RELATIVE = Path("memory/agentglg-sync-state.txt")
MEMORY_SNAPSHOTS_DIR_RELATIVE = Path("memory/snapshots")
WORKSPACE_EXCLUDE_TOP_LEVEL = {".git", "user_files"}
WORKSPACE_EXCLUDE_DIR_NAMES = {".git", ".arcade", "__pycache__"}
WORKSPACE_EXCLUDE_FILE_NAMES = {"agentglg-github-token.txt", "agentglg-sync-state.txt"}
REQUIRED_MEMORY_FILES = [
    "confirmed-error-patterns.md",
    "missed-findings-log.md",
    "template-notes.md",
    "user-confirmed-corrections.md",
]
PROTECTED_MEMORY_FILES = REQUIRED_MEMORY_FILES + [
    "user-preferences.md",
    "slack-user-corrections.md",
    "memory-save-log.md",
]


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        details = (result.stderr or result.stdout or f"exit code {result.returncode}").strip()
        raise RuntimeError(f"Команда не выполнилась: {' '.join(cmd)}\n{details}")
    return result


def workspace_uses_git(workspace: Path) -> bool:
    return (workspace / ".git").exists()


def detect_repo_url(workspace: Path) -> str:
    if not workspace_uses_git(workspace):
        return DEFAULT_REPO_URL
    result = run(["git", "remote", "get-url", "origin"], cwd=workspace, check=False)
    repo_url = result.stdout.strip()
    return repo_url or DEFAULT_REPO_URL


def repo_uses_direct_github(repo_url: str) -> bool:
    return "github.com" in repo_url and "chatgpt.com/backend-api/git-authed/" not in repo_url


def detect_branch(workspace: Path) -> str:
    if workspace_uses_git(workspace):
        current = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=workspace, check=False).stdout.strip()
        if current and current != "HEAD":
            return current
        origin_head = run(["git", "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"], cwd=workspace, check=False).stdout.strip()
        if origin_head.startswith("refs/remotes/origin/"):
            return origin_head.removeprefix("refs/remotes/origin/")
    return DEFAULT_BRANCH


def should_skip_workspace_relative(rel: Path) -> bool:
    parts = rel.parts
    if not parts:
        return False
    rel_text = rel.as_posix()
    if parts[0] in WORKSPACE_EXCLUDE_TOP_LEVEL:
        return True
    if rel_text.startswith("memory/automation/private/"):
        return True
    if rel_text.startswith("memory/snapshots/"):
        return True
    if any(part in WORKSPACE_EXCLUDE_DIR_NAMES for part in parts[:-1]):
        return True
    if parts[-1] in WORKSPACE_EXCLUDE_FILE_NAMES:
        return True
    if parts[-1].startswith("agentglg-github-token"):
        return True
    return False


def list_workspace_files(workspace: Path) -> list[Path]:
    return [
        path
        for path in sorted(workspace.rglob("*"))
        if path.is_file() and not should_skip_workspace_relative(path.relative_to(workspace))
    ]


def compute_workspace_fingerprint(workspace: Path) -> str:
    digest = hashlib.sha256()
    for path in list_workspace_files(workspace):
        rel = path.relative_to(workspace).as_posix().encode("utf-8")
        digest.update(rel)
        digest.update(b"\0")
        digest.update(str(path.stat().st_size).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def read_sync_state(workspace: Path) -> str | None:
    state_path = workspace / SYNC_STATE_FILE_RELATIVE
    if not state_path.exists():
        return None
    for line in state_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("fingerprint="):
            value = line.partition("=")[2].strip()
            return value or None
    return None


def write_sync_state(workspace: Path, fingerprint: str, commit_sha: str) -> None:
    state_path = workspace / SYNC_STATE_FILE_RELATIVE
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        f"fingerprint={fingerprint}\ncommit={commit_sha}\nupdated_at={dt.datetime.now(dt.UTC).isoformat()}\n",
        encoding="utf-8",
    )


def snapshot_memory_files(workspace: Path) -> Path | None:
    memory_dir = workspace / "memory"
    files_to_copy = [memory_dir / name for name in PROTECTED_MEMORY_FILES if (memory_dir / name).exists()]
    if not files_to_copy:
        return None

    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    snapshot_dir = workspace / MEMORY_SNAPSHOTS_DIR_RELATIVE / stamp
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    for source in files_to_copy:
        shutil.copy2(source, snapshot_dir / source.name)

    manifest = ["# Memory Snapshot", "", f"- created_at_utc: `{stamp}`", "- files:"]
    manifest.extend(f"  - `{source.name}`" for source in files_to_copy)
    (snapshot_dir / "README.md").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    return snapshot_dir


def normalize_significant_lines(text: str) -> set[str]:
    return {line.strip() for line in text.splitlines() if line.strip()}


def detect_memory_regressions(repo_root: Path, workspace: Path) -> list[str]:
    regressions: list[str] = []
    memory_dir = workspace / "memory"
    repo_memory_dir = repo_root / "memory"

    for file_name in PROTECTED_MEMORY_FILES:
        local_path = memory_dir / file_name
        remote_path = repo_memory_dir / file_name
        if not local_path.exists() and remote_path.exists():
            regressions.append(
                f"{file_name}: в зеркале есть файл, которого нет в локальной памяти. Сначала проверь локальную память и подтвержденные правки."
            )
            continue
        if not local_path.exists() or not remote_path.exists():
            continue

        local_lines = normalize_significant_lines(local_path.read_text(encoding="utf-8"))
        remote_lines = normalize_significant_lines(remote_path.read_text(encoding="utf-8"))
        missing = [line for line in sorted(remote_lines - local_lines) if len(line) > 4]
        if not missing:
            continue
        preview = "; ".join(missing[:3])
        if len(missing) > 3:
            preview += f"; и ещё {len(missing) - 3}"
        regressions.append(f"{file_name}: в зеркале есть строки, которых нет в локальной памяти: {preview}")

    return regressions


def load_token(workspace: Path) -> str | None:
    env_token = os.getenv("AGENTGLG_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")
    if env_token:
        return env_token.strip()
    for rel in (PRIVATE_TOKEN_FILE_RELATIVE, TOKEN_FILE_RELATIVE):
        path = workspace / rel
        if path.exists():
            token = path.read_text(encoding="utf-8").strip()
            if token:
                return token
    return None


def ensure_git_auth(token: str) -> None:
    run(["git", "config", "--global", "credential.helper", "store"])
    payload = f"protocol=https\nhost=github.com\nusername=x-access-token\npassword={token}\n\n"
    subprocess.run(["git", "credential", "approve"], input=payload, text=True, capture_output=True, check=True)


def has_git_github_credentials() -> bool:
    result = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0 and "username=" in result.stdout and "password=" in result.stdout


def clone_or_update_repo(repo_root: Path, branch: str, repo_url: str) -> None:
    if not repo_root.exists():
        run(["git", "clone", "--branch", branch, repo_url, str(repo_root)])
        return
    run(["git", "remote", "set-url", "origin", repo_url], cwd=repo_root)
    run(["git", "fetch", "origin", branch], cwd=repo_root)
    run(["git", "checkout", branch], cwd=repo_root, check=False)
    if run(["git", "rev-parse", "--verify", branch], cwd=repo_root, check=False).returncode != 0:
        run(["git", "checkout", "-B", branch, f"origin/{branch}"], cwd=repo_root)
        return
    run(["git", "pull", "--ff-only", "origin", branch], cwd=repo_root)


def mirror_workspace(repo_root: Path, workspace: Path) -> None:
    tracked_top_level: set[str] = set()
    for child in sorted(workspace.iterdir()):
        name = child.name
        if name in WORKSPACE_EXCLUDE_TOP_LEVEL:
            continue
        rel = Path(name)
        if should_skip_workspace_relative(rel):
            continue
        tracked_top_level.add(name)
        target = repo_root / name
        if child.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(child, target, ignore=_build_ignore(workspace))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(child, target)

    for child in list(repo_root.iterdir()):
        if child.name == ".git":
            continue
        if child.name not in tracked_top_level:
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()


def _build_ignore(workspace: Path):
    def _ignore(dir_path: str, names: list[str]) -> set[str]:
        current = Path(dir_path)
        ignored: set[str] = set()
        for name in names:
            rel = (current / name).relative_to(workspace)
            if should_skip_workspace_relative(rel):
                ignored.add(name)
        return ignored

    return _ignore


def git_has_changes(repo_root: Path) -> bool:
    return bool(run(["git", "status", "--porcelain"], cwd=repo_root).stdout.strip())


def git_commit_and_push(repo_root: Path, branch: str, message: str, do_push: bool) -> None:
    run(["git", "add", "-A"], cwd=repo_root)
    if not git_has_changes(repo_root):
        print("Изменений для коммита нет.")
        return
    run(["git", "config", "user.name", "OpenAI Codex"], cwd=repo_root)
    run(["git", "config", "user.email", "codex@openai.com"], cwd=repo_root)
    run(["git", "commit", "-m", message], cwd=repo_root)
    if do_push:
        run(["git", "push", "origin", branch], cwd=repo_root)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Экспорт текущей рабочей среды агента в GitHub-зеркало betonglg-ux/Agentglg")
    parser.add_argument("--workspace", default="/workspace/memory", help="Корень рабочей среды агента")
    parser.add_argument("--repo-dir", default="", help="Путь до локального клона репозитория")
    parser.add_argument("--branch", default="", help="Ветка для экспорта. По умолчанию определяется автоматически.")
    parser.add_argument("--message", default="Export agent mirror from workspace", help="Сообщение коммита")
    parser.add_argument("--no-push", action="store_true", help="Подготовить и закоммитить изменения без отправки в GitHub")
    parser.add_argument("--only-if-changed", action="store_true", help="Запускать экспорт только если рабочие файлы изменились")
    parser.add_argument("--allow-memory-overwrite", action="store_true", help="Разрешить экспорт даже если в зеркале найдены строки памяти, которых нет локально")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace).resolve()
    if not workspace.exists():
        print(f"Не найден workspace: {workspace}", file=sys.stderr)
        return 1

    missing_memory = [name for name in REQUIRED_MEMORY_FILES if not (workspace / "memory" / name).exists()]
    if missing_memory:
        joined = ", ".join(missing_memory)
        raise RuntimeError(
            "Экспорт остановлен: отсутствуют обязательные локальные файлы памяти.\n"
            f"Не найдены: {joined}\n"
            "Экспорт работает только от текущей локальной памяти к зеркалу и не подставляет старые копии из служебных файлов."
        )

    branch = args.branch or detect_branch(workspace)
    repo_url = detect_repo_url(workspace)
    fingerprint = compute_workspace_fingerprint(workspace)
    if args.only_if_changed and read_sync_state(workspace) == fingerprint:
        print("Новых изменений нет. Экспорт в зеркало не требуется.")
        return 0

    token = load_token(workspace)
    if token:
        ensure_git_auth(token)
    elif repo_uses_direct_github(repo_url) and has_git_github_credentials():
        pass
    elif not args.no_push and repo_uses_direct_github(repo_url):
        print(
            "Не найден токен GitHub. Задайте AGENTGLG_GITHUB_TOKEN/GITHUB_TOKEN "
            f"или сохраните токен в {workspace / PRIVATE_TOKEN_FILE_RELATIVE} или {workspace / TOKEN_FILE_RELATIVE}.",
            file=sys.stderr,
        )
        return 1

    snapshot_dir = snapshot_memory_files(workspace)
    repo_dir = Path(args.repo_dir).resolve() if args.repo_dir else Path(tempfile.gettempdir()) / "agentglg-mirror-repo"
    clone_or_update_repo(repo_dir, branch, repo_url)

    regressions = detect_memory_regressions(repo_dir, workspace)
    if regressions and not args.allow_memory_overwrite:
        details = "\n".join(f"- {item}" for item in regressions)
        snapshot_hint = f"\nЗащитный снимок памяти сохранен в: {snapshot_dir}" if snapshot_dir else ""
        raise RuntimeError(
            "Экспорт остановлен: в GitHub-зеркале найдены строки памяти, которых нет локально.\n"
            "Это похоже на расхождение источников или потерю наработок перед зеркалированием.\n"
            f"{details}{snapshot_hint}\n"
            "Не обновляйте локальную память автоматически из зеркала.\n"
            "Сначала вручную сравните локальную память, защитный снимок и подтвержденные пользователем правки, затем повторите запуск."
        )

    mirror_workspace(repo_root=repo_dir, workspace=workspace)
    git_commit_and_push(repo_root=repo_dir, branch=branch, message=args.message, do_push=not args.no_push)

    head = run(["git", "rev-parse", "--short", "HEAD"], cwd=repo_dir).stdout.strip()
    write_sync_state(workspace, fingerprint, head)
    print(f"Экспорт в зеркало завершен. Локальный репозиторий: {repo_dir}")
    print(f"Текущий коммит: {head}")
    if args.no_push:
        print("Отправка в GitHub не выполнялась.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())