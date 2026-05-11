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
SKILL_PATH = Path("/root/.codex/skills/hermes/glavlab-protocol-review/SKILL.md")
TOKEN_FILE_RELATIVE = Path("memory/agentglg-github-token.txt")
PRIVATE_TOKEN_FILE_RELATIVE = Path("memory/automation/private/agentglg-github-token.txt")
SYNC_STATE_FILE_RELATIVE = Path("memory/agentglg-sync-state.txt")
MEMORY_SNAPSHOTS_DIR_RELATIVE = Path("memory/snapshots")
WORKSPACE_EXCLUDE_TOP_LEVEL = {
    ".git",
    "user_files",
}
REPO_PROTECTED_TOP_LEVEL = {
    ".git",
    "agent-development",
    "github-mirror-manifest.md",
}
WORKSPACE_EXCLUDE_DIR_NAMES = {
    ".git",
    ".arcade",
    "__pycache__",
}
WORKSPACE_EXCLUDE_FILE_NAMES = {
    "agentglg-github-token.txt",
    "agentglg-sync-state.txt",
}
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
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        details = stderr or stdout or f"exit code {result.returncode}"
        raise RuntimeError(f"Команда не выполнилась: {' '.join(cmd)}\n{details}")
    return result


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def copy_tree(src: Path, dst: Path, ignore: shutil.IgnorePattern | None = None) -> None:
    if not src.exists():
        return
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=ignore)


def copy_file(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def workspace_uses_git(workspace: Path) -> bool:
    return (workspace / ".git").exists()


def get_workspace_origin_url(workspace: Path) -> str:
    if not workspace_uses_git(workspace):
        return ""
    result = run(["git", "remote", "get-url", "origin"], cwd=workspace, check=False)
    return result.stdout.strip()


def normalize_repo_url(repo_url: str) -> str:
    url = repo_url.strip()
    if url.endswith(".git"):
        url = url[:-4]
    if url.startswith("git@github.com:"):
        url = "https://github.com/" + url.removeprefix("git@github.com:")
    return url.rstrip("/")


def is_target_mirror_repo_url(repo_url: str) -> bool:
    normalized = normalize_repo_url(repo_url)
    return normalized.endswith("github.com/betonglg-ux/Agentglg")


def detect_repo_url(workspace: Path) -> str:
    repo_url = get_workspace_origin_url(workspace)
    if repo_url and is_target_mirror_repo_url(repo_url):
        return repo_url
    return DEFAULT_REPO_URL


def repo_uses_direct_github(repo_url: str) -> bool:
    return "github.com" in repo_url and "chatgpt.com/backend-api/git-authed/" not in repo_url


def detect_branch(workspace: Path) -> str:
    if workspace_uses_git(workspace):
        current_branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=workspace, check=False).stdout.strip()
        if current_branch and current_branch != "HEAD":
            return current_branch

        origin_head = run(
            ["git", "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"],
            cwd=workspace,
            check=False,
        ).stdout.strip()
        if origin_head.startswith("refs/remotes/origin/"):
            return origin_head.removeprefix("refs/remotes/origin/")

    return DEFAULT_BRANCH


def normalize_significant_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lines.append(line)
    return lines


def snapshot_memory_files(workspace: Path) -> Path | None:
    memory_dir = workspace / "memory"
    files_to_copy = [memory_dir / name for name in PROTECTED_MEMORY_FILES if (memory_dir / name).exists()]
    if not files_to_copy:
        return None

    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    snapshot_dir = workspace / MEMORY_SNAPSHOTS_DIR_RELATIVE / stamp
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    for source in files_to_copy:
        copy_file(source, snapshot_dir / source.name)

    manifest_lines = [
        "# Memory Snapshot",
        "",
        f"- created_at_utc: `{stamp}`",
        "- files:",
    ]
    for source in files_to_copy:
        manifest_lines.append(f"  - `{source.name}`")
    write_text(snapshot_dir / "README.md", "\n".join(manifest_lines))
    return snapshot_dir


def detect_memory_regressions(repo_root: Path, workspace: Path) -> list[str]:
    memory_dir = workspace / "memory"
    regressions: list[str] = []

    for file_name in PROTECTED_MEMORY_FILES:
        local_path = memory_dir / file_name
        remote_path = repo_root / "agent-development" / file_name
        if not local_path.exists() and remote_path.exists():
            regressions.append(
                f"{file_name}: в зеркале есть файл, которого нет в локальной памяти. "
                "Нужно сначала проверить локальную память и подтвержденные правки, а не удалять зеркальную запись автоматически."
            )
            continue
        if not local_path.exists() or not remote_path.exists():
            continue

        local_lines = set(normalize_significant_lines(local_path.read_text(encoding="utf-8")))
        remote_lines = set(normalize_significant_lines(remote_path.read_text(encoding="utf-8")))
        missing_lines = [line for line in sorted(remote_lines - local_lines) if len(line) > 4]
        if not missing_lines:
            continue

        preview = "; ".join(missing_lines[:3])
        if len(missing_lines) > 3:
            preview += f"; и ещё {len(missing_lines) - 3}"
        regressions.append(f"{file_name}: в зеркале есть строки, которых нет в локальной памяти: {preview}")

    return regressions


def rel_files(base: Path) -> list[Path]:
    return sorted(path.relative_to(base) for path in base.rglob("*") if path.is_file())


def format_protocols(protocols_dir: Path) -> str:
    lines = [
        "# Индекс шаблонов протоколов",
        "",
        "Назначение: этот файл автоматически собирается из рабочей папки `protocols/` и показывает, какие шаблоны нужно зеркалить в GitHub.",
        "",
    ]
    for index, category in enumerate(sorted(p for p in protocols_dir.iterdir() if p.is_dir()), start=1):
        lines.append(f"## {index}. {category.name}")
        for file_path in sorted(category.iterdir()):
            if file_path.is_file():
                lines.append(f"- `protocols/{category.name}/{file_path.name}`")
        lines.append("")
    lines.extend(
        [
            "## Как использовать этот индекс",
            "- использовать как контрольный список обязательных шаблонов при синхронизации;",
            "- использовать как опорный список при восстановлении похожего агента;",
            "- использовать для проверки, не потерялись ли шаблоны при обновлениях.",
        ]
    )
    return "\n".join(lines)


def list_memory_markdown_files(memory_dir: Path) -> list[Path]:
    if not memory_dir.exists():
        return []
    files: list[Path] = []
    for path in sorted(memory_dir.rglob("*.md")):
        if not path.is_file():
            continue
        rel = path.relative_to(memory_dir).as_posix()
        if rel.startswith(".git/") or rel.startswith(".arcade/"):
            continue
        if rel.startswith("snapshots/"):
            continue
        files.append(path)
    return files


def format_attached_files_index(agent_files_dir: Path, service_dir: Path | None = None) -> str:
    protocols_dir = agent_files_dir / "protocols"
    service_root = service_dir if service_dir and service_dir.exists() else agent_files_dir / "agent-development"
    service_files: list[Path] = []
    if service_root.exists():
        for path in service_root.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(service_root)
            if rel.parts and rel.parts[0] == "protocols":
                continue
            service_files.append(rel)
        service_files.sort()
    xl_files = rel_files(agent_files_dir / "xl") if (agent_files_dir / "xl").exists() else []

    lines = [
        "# Индекс текущих файлов агента",
        "",
        "Назначение: этот файл автоматически собирается из рабочей среды агента и помогает быстро понять, что именно выгружается в GitHub-зеркало.",
        "",
        "## 1. Служебные файлы развития агента",
    ]
    if service_files:
        for file_path in service_files:
            lines.append(f"- `agent-development/{file_path.as_posix()}`")
    else:
        lines.append("- служебные файлы не найдены")
    lines.extend(["", "## 2. Папка `protocols/`"])
    if protocols_dir.exists():
        for category in sorted(p for p in protocols_dir.iterdir() if p.is_dir()):
            lines.append(f"### `protocols/{category.name}`")
            for file_path in sorted(category.iterdir()):
                if file_path.is_file():
                    lines.append(f"- `{file_path.name}`")
            lines.append("")
    else:
        lines.append("- папка `protocols/` не найдена")
        lines.append("")
    lines.extend(["## 3. Папка `xl/`", f"- файлов найдено: {len(xl_files)}", ""])
    if xl_files:
        preview = xl_files[:20]
        lines.append("Первые файлы:")
        for file_path in preview:
            lines.append(f"- `xl/{file_path.as_posix()}`")
        if len(xl_files) > len(preview):
            lines.append(f"- и ещё {len(xl_files) - len(preview)} файлов")
        lines.append("")
    lines.extend(
        [
            "## 4. Что означает эта структура",
            "- `protocols/` хранит шаблоны приприа хранилогиит proҀ