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


REPO_URL = "https://github.com/betonglg-ux/Agentglg.git"
DEFAULT_BRANCH = "main"
SKILL_PATH = Path("/root/.codex/skills/hermes/glavlab-protocol-review/SKILL.md")
TOKEN_FILE_RELATIVE = Path("memory/agentglg-github-token.txt")
PRIVATE_TOKEN_FILE_RELATIVE = Path("memory/automation/private/agentglg-github-token.txt")
SYNC_STATE_FILE_RELATIVE = Path("memory/agentglg-sync-state.txt")
MEMORY_FILES = [
    "confirmed-error-patterns.md",
    "missed-findings-log.md",
    "template-notes.md",
    "user-confirmed-corrections.md",
]
SOURCE_DOCS = [
    "github-mirror-manifest.md",
    "github-export-bundle.md",
    "recovery-plan.md",
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


def list_tracked_memory_files(memory_dir: Path) -> list[Path]:
    return [memory_dir / name for name in MEMORY_FILES if (memory_dir / name).exists()]


def format_attached_files_index(agent_files_dir: Path) -> str:
    protocols_dir = agent_files_dir / "protocols"
    xl_files = rel_files(agent_files_dir / "xl") if (agent_files_dir / "xl").exists() else []

    lines = [
        "# Индекс текущих файлов агента",
        "",
        "Назначение: этот файл автоматически собирается из рабочей среды агента и помогает быстро понять, что именно выгружается в GitHub-зеркало.",
        "",
        "## 1. Канонические источники в рабочей среде",
    ]
    lines.extend(
        [
            "- `AGENTS.md`",
            "- `automation/README.md`",
            "- `automation/run_agentglg_sync.sh`",
            "- `automation/setup_github_auth.sh`",
            "- `automation/sync_agentglg_mirror.py`",
            "- `memory/confirmed-error-patterns.md`",
            "- `memory/missed-findings-log.md`",
            "- `memory/template-notes.md`",
            "- `memory/user-confirmed-corrections.md`",
            "- `glavlab-protocol-review/SKILL.md`",
            "",
            "## 2. Папка `protocols/`",
        ]
    )
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
            "- `protocols/` хранит шаблоны протоколов, на которых держится сверка PDF;",
            "- `agent-development/` хранит канонические материалы для воспроизведения и развития агента;",
            "- `xl/` показан только как технический источник локальной среды и не должен дублироваться в корень зеркала.",
            "",
            "## 5. Приоритеты зеркалирования",
            "1. инструкции агента и automation-скрипты;",
            "2. четыре канонических файла памяти;",
            "3. все шаблоны из `protocols/`;",
            "4. ключевой навык и служебные индексы `agent-development/`.",
        ]
    )
    return "\n".join(lines)


def build_agent_summary(protocols_dir: Path) -> str:
    categories = sorted(p.name for p in protocols_dir.iterdir() if p.is_dir()) if protocols_dir.exists() else []
    lines = [
        "# Краткая карточка агента",
        "",
        "Название: `Проверка PDF-протоколов`",
        "",
        "Назначение:",
        "- проверка строительных PDF-протоколов;",
        "- поиск ошибок оформления, логики, расчетов, колонтитулов, рамок и заполнения полей;",
        "- перенос устойчивых знаний и шаблонов в GitHub-зеркало.",
        "",
        "Основные источники истины:",
        "- инструкции агента из `AGENTS.md`;",
        "- навык `glavlab-protocol-review`;",
        "- Excel-шаблоны и связанные файлы из `agent_files/protocols/`;",
        "- память агента из папки `memory/`.",
        "",
        "Типы шаблонов, найденные в текущей среде:",
    ]
    if categories:
        for category in categories:
            lines.append(f"- {category}")
    else:
        lines.append("- шаблоны не обнаружены")
    lines.extend(
        [
            "",
            "Что нужно воспроизводить в будущем:",
            "- инструкции агента;",
            "- структуру `agent-development/`;",
            "- папку `protocols/` с шаблонами;",
            "- память и экспорт подтвержденных правил.",
        ]
    )
    return "\n".join(lines)


def build_memory_export_readme() -> str:
    return "\n".join(
        [
            "# Memory Exports",
            "",
            "Эта папка хранит экспортные и зеркальные материалы по памяти агента.",
            "",
            "Канонический источник истины в GitHub:",
            "- `agent-development/confirmed-error-patterns.md`",
            "- `agent-development/missed-findings-log.md`",
            "- `agent-development/template-notes.md`",
            "- `agent-development/user-confirmed-corrections.md`",
            "",
            "Что лежит здесь:",
            "- `*-export.md` — короткие экспортные указатели на канонические файлы;",
            "- `raw-memory/` — прямое зеркало markdown-файлов из рабочей памяти агента;",
            "- `memory-index.md` — список реально найденных markdown-файлов памяти.",
        ]
    )


def build_memory_index(memory_dir: Path) -> str:
    files = list_tracked_memory_files(memory_dir)
    lines = [
        "# Memory Index",
        "",
        "Этот файл автоматически показывает, какие канонические файлы памяти реально есть в памяти агента и были выгружены в зеркало.",
        "",
    ]
    if not files:
        lines.append("- канонические файлы памяти пока не найдены")
        return "\n".join(lines)
    for path in files:
        rel = path.relative_to(memory_dir).as_posix()
        lines.append(f"- `memory/{rel}`")
    return "\n".join(lines)


def build_placeholder(title: str, source_name: str) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            f"Статус на {dt.date.today().isoformat()}: подтвержденные данные пока не выгружены в отдельный файл.",
            "",
            "Этот файл создан автоматически как точка для дальнейшего накопления знаний.",
            f"Основной источник для следующего заполнения: `{source_name}`.",
        ]
    )


def build_export_pointer(title: str, canonical_path: str, raw_path: str) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            "Канонический файл памяти находится здесь:",
            f"- `{canonical_path}`",
            "",
            "Прямое зеркало рабочего файла памяти находится здесь:",
            f"- `{raw_path}`",
            "",
            "Этот экспортный файл оставлен как совместимый указатель, чтобы в репозитории не было второго конкурирующего текста.",
        ]
    )


def build_canonical_memory_readme() -> str:
    return "\n".join(
        [
            "# Canonical Memory",
            "",
            "Канонические файлы памяти агента в GitHub:",
            "- `agent-development/confirmed-error-patterns.md`",
            "- `agent-development/missed-findings-log.md`",
            "- `agent-development/template-notes.md`",
            "- `agent-development/user-confirmed-corrections.md`",
            "",
            "Правило:",
            "- именно эти файлы считаются основным источником истины в зеркале;",
            "- `agent-development/memory-exports/raw-memory/` хранит прямые копии файлов из рабочей памяти;",
            "- `agent-development/memory-exports/*-export.md` больше не дублируют содержимое, а только указывают на канонические файлы.",
        ]
    )


def build_memory_sync_status(memory_dir: Path) -> str:
    tracked = [
        "confirmed-error-patterns.md",
        "missed-findings-log.md",
        "template-notes.md",
        "user-confirmed-corrections.md",
    ]
    lines = [
        "# Memory Sync Status",
        "",
        f"Обновлено: {dt.datetime.now(dt.UTC).isoformat()}",
        "",
        "Этот файл показывает контрольные суммы канонических файлов памяти, собранных из рабочей памяти агента.",
        "",
    ]
    for name in tracked:
        source = memory_dir / name
        if source.exists():
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            lines.append(f"- `{name}`: `{digest}`")
        else:
            lines.append(f"- `{name}`: MISSING")
    return "\n".join(lines)


def append_sync_changelog(changelog_path: Path) -> None:
    today = dt.date.today().isoformat()
    sync_line = f"- выполнена автоматическая синхронизация GitHub-зеркала и пересборка служебных индексов."
    if changelog_path.exists():
        existing = changelog_path.read_text(encoding="utf-8")
    else:
        existing = "# CHANGELOG GitHub-зеркала\n\nРепозиторий зеркала: `betonglg-ux/Agentglg`\n"

    marker = f"## {today}"
    if marker not in existing:
        existing = existing.rstrip() + f"\n\n## {today}\n\n### Синхронизация\n{sync_line}\n"
    elif sync_line not in existing:
        existing = existing.rstrip() + f"\n{sync_line}\n"
    changelog_path.write_text(existing.rstrip() + "\n", encoding="utf-8")


def load_token(workspace: Path) -> str | None:
    env_token = os.getenv("AGENTGLG_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")
    if env_token:
        return env_token.strip()
    private_token_file = workspace / PRIVATE_TOKEN_FILE_RELATIVE
    if private_token_file.exists():
        token = private_token_file.read_text(encoding="utf-8").strip()
        if token:
            return token
    token_file = workspace / TOKEN_FILE_RELATIVE
    if token_file.exists():
        token = token_file.read_text(encoding="utf-8").strip()
        if token:
            return token
    return None


def ensure_git_auth(token: str) -> None:
    run(["git", "config", "--global", "credential.helper", "store"])
    payload = f"protocol=https\nhost=github.com\nusername=x-access-token\npassword={token}\n\n"
    subprocess.run(
        ["git", "credential", "approve"],
        input=payload,
        text=True,
        check=True,
        capture_output=True,
    )


def has_git_github_credentials() -> bool:
    result = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return False
    output = result.stdout
    return "username=" in output and "password=" in output


def iter_sync_inputs(workspace: Path) -> list[Path]:
    files: list[Path] = []
    candidate_files = [
        workspace / "AGENTS.md",
        workspace / "automation" / "README.md",
        workspace / "automation" / "run_agentglg_sync.sh",
        workspace / "automation" / "setup_github_auth.sh",
        workspace / "automation" / "sync_agentglg_mirror.py",
        SKILL_PATH,
    ]
    candidate_files.extend(workspace / "memory" / name for name in MEMORY_FILES)
    candidate_files.extend((workspace / "agent_files" / "agent-development" / name) for name in SOURCE_DOCS)

    protocols_dir = workspace / "agent_files" / "protocols"
    if protocols_dir.exists():
        candidate_files.extend(path for path in sorted(protocols_dir.rglob("*")) if path.is_file())

    for path in candidate_files:
        if path.exists() and path.is_file():
            files.append(path)
    return sorted(set(files))


def compute_workspace_fingerprint(workspace: Path) -> str:
    digest = hashlib.sha256()
    for path in iter_sync_inputs(workspace):
        if path.is_relative_to(workspace):
            rel_text = path.relative_to(workspace).as_posix()
        else:
            rel_text = f"external:{path.as_posix()}"
        rel = rel_text.encode("utf-8")
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
    value = state_path.read_text(encoding="utf-8").strip()
    return value or None


def write_sync_state(workspace: Path, fingerprint: str, commit_sha: str) -> None:
    state_path = workspace / SYNC_STATE_FILE_RELATIVE
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        f"fingerprint={fingerprint}\ncommit={commit_sha}\nupdated_at={dt.datetime.now(dt.UTC).isoformat()}\n",
        encoding="utf-8",
    )


def prepare_repo(repo_root: Path, workspace: Path) -> None:
    agent_files = workspace / "agent_files"
    memory_dir = workspace / "memory"
    protocols_dir = agent_files / "protocols"
    agent_dev_src = agent_files / "agent-development"
    agent_dev_dst = repo_root / "agent-development"

    for child in list(repo_root.iterdir()):
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()

    copy_file(workspace / "AGENTS.md", repo_root / "AGENTS.md")
    copy_file(agent_dev_src / "github-mirror-manifest.md", repo_root / "github-mirror-manifest.md")

    automation_dst = repo_root / "automation"
    automation_dst.mkdir(parents=True, exist_ok=True)
    for file_name in ["README.md", "run_agentglg_sync.sh", "setup_github_auth.sh", "sync_agentglg_mirror.py"]:
        copy_file(workspace / "automation" / file_name, automation_dst / file_name)

    if agent_dev_dst.exists():
        shutil.rmtree(agent_dev_dst)
    agent_dev_dst.mkdir(parents=True, exist_ok=True)

    for file_name in ["github-mirror-manifest.md", "github-export-bundle.md", "recovery-plan.md"]:
        copy_file(agent_dev_src / file_name, agent_dev_dst / file_name)

    copy_tree(protocols_dir, agent_dev_dst / "protocols")
    write_text(agent_dev_dst / "protocols" / "README.md", "# Protocols\n\nЭта папка автоматически собирается из локальной папки `agent_files/protocols/`.")

    files_index_dir = agent_dev_dst / "files-index"
    files_index_dir.mkdir(parents=True, exist_ok=True)
    write_text(files_index_dir / "README.md", "# Files Index\n\nЭтот раздел автоматически собирается при синхронизации зеркала.")
    write_text(files_index_dir / "attached-files-index.md", format_attached_files_index(agent_files))
    write_text(files_index_dir / "templates-index.md", format_protocols(protocols_dir))

    memory_exports_dir = agent_dev_dst / "memory-exports"
    memory_exports_dir.mkdir(parents=True, exist_ok=True)
    write_text(memory_exports_dir / "README.md", build_memory_export_readme())
    write_text(memory_exports_dir / "memory-index.md", build_memory_index(memory_dir))
    export_map = {
        "confirmed-error-patterns.md": "confirmed-error-patterns-export.md",
        "missed-findings-log.md": "missed-findings-export.md",
        "template-notes.md": "template-notes-export.md",
        "user-confirmed-corrections.md": "user-corrections-export.md",
    }
    for memory_name, export_name in export_map.items():
        source = memory_dir / memory_name
        target = memory_exports_dir / export_name
        canonical = f"agent-development/{memory_name}"
        raw = f"agent-development/memory-exports/raw-memory/{memory_name}"
        title = export_name.replace("-export.md", "").replace("-", " ").title()
        write_text(target, build_export_pointer(title, canonical, raw))

    raw_memory_dir = memory_exports_dir / "raw-memory"
    raw_memory_dir.mkdir(parents=True, exist_ok=True)
    for source in list_tracked_memory_files(memory_dir):
        target = raw_memory_dir / source.relative_to(memory_dir)
        copy_file(source, target)

    write_text(agent_dev_dst / "current-agent-instructions.md", (workspace / "AGENTS.md").read_text(encoding="utf-8"))
    write_text(agent_dev_dst / "agent-summary.md", build_agent_summary(protocols_dir))
    write_text(
        agent_dev_dst / "confirmed-error-patterns.md",
        (memory_dir / "confirmed-error-patterns.md").read_text(encoding="utf-8")
        if (memory_dir / "confirmed-error-patterns.md").exists()
        else build_placeholder("Confirmed Error Patterns", "memory/confirmed-error-patterns.md"),
    )
    write_text(
        agent_dev_dst / "missed-findings-log.md",
        (memory_dir / "missed-findings-log.md").read_text(encoding="utf-8")
        if (memory_dir / "missed-findings-log.md").exists()
        else build_placeholder("Missed Findings Log", "memory/missed-findings-log.md"),
    )
    write_text(
        agent_dev_dst / "template-notes.md",
        (memory_dir / "template-notes.md").read_text(encoding="utf-8")
        if (memory_dir / "template-notes.md").exists()
        else build_placeholder("Template Notes", "memory/template-notes.md"),
    )
    write_text(
        agent_dev_dst / "user-confirmed-corrections.md",
        (memory_dir / "user-confirmed-corrections.md").read_text(encoding="utf-8")
        if (memory_dir / "user-confirmed-corrections.md").exists()
        else build_placeholder("User Confirmed Corrections", "memory/user-confirmed-corrections.md"),
    )
    write_text(agent_dev_dst / "CANONICAL-MEMORY.md", build_canonical_memory_readme())
    write_text(agent_dev_dst / "MEMORY-SYNC-STATUS.md", build_memory_sync_status(memory_dir))

    skills_dir = agent_dev_dst / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    write_text(
        skills_dir / "README.md",
        "# Skills\n\nЭта папка автоматически собирает ключевые навыки, которые нужно переносить вместе с агентом.",
    )
    if SKILL_PATH.exists():
        copy_file(SKILL_PATH, skills_dir / "glavlab-protocol-review" / "SKILL.md")

    append_sync_changelog(agent_dev_dst / "CHANGELOG.md")
    manifest_src = agent_dev_src / "github-mirror-manifest.md"
    if manifest_src.exists():
        copy_file(manifest_src, repo_root / "github-mirror-manifest.md")

def clone_or_update_repo(repo_root: Path, branch: str) -> None:
    if not repo_root.exists():
        run(["git", "clone", "--branch", branch, REPO_URL, str(repo_root)])
        return
    run(["git", "fetch", "origin", branch], cwd=repo_root)
    run(["git", "checkout", branch], cwd=repo_root)
    run(["git", "pull", "--ff-only", "origin", branch], cwd=repo_root)


def git_has_changes(repo_root: Path) -> bool:
    result = run(["git", "status", "--porcelain"], cwd=repo_root)
    return bool(result.stdout.strip())


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
    parser = argparse.ArgumentParser(description="Синхронизация GitHub-зеркала агента betonglg-ux/Agentglg")
    parser.add_argument("--workspace", default="/workspace", help="Корень рабочей среды агента")
    parser.add_argument("--repo-dir", default="", help="Путь до локального клона репозитория")
    parser.add_argument("--branch", default=DEFAULT_BRANCH, help="Ветка для синхронизации")
    parser.add_argument("--message", default="Sync agent mirror from workspace", help="Сообщение коммита")
    parser.add_argument("--no-push", action="store_true", help="Подготовить и закоммитить изменения без push")
    parser.add_argument("--only-if-changed", action="store_true", help="Запускать синхронизацию только если рабочие файлы изменились")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace).resolve()
    if not workspace.exists():
        print(f"Не найден workspace: {workspace}", file=sys.stderr)
        return 1

    fingerprint = compute_workspace_fingerprint(workspace)
    if args.only_if_changed:
        previous = read_sync_state(workspace)
        if previous == fingerprint:
            print("Новых изменений нет. Синхронизация не требуется.")
            return 0

    token = load_token(workspace)
    if token:
        ensure_git_auth(token)
    elif has_git_github_credentials():
        pass
    elif not args.no_push:
        print(
            "Не найден токен GitHub. Задайте AGENTGLG_GITHUB_TOKEN/GITHUB_TOKEN "
            f"или сохраните токен в {workspace / PRIVATE_TOKEN_FILE_RELATIVE} "
            f"или {workspace / TOKEN_FILE_RELATIVE}.",
            file=sys.stderr,
        )
        return 1

    repo_dir = Path(args.repo_dir).resolve() if args.repo_dir else Path(tempfile.gettempdir()) / "agentglg-mirror-repo"
    clone_or_update_repo(repo_dir, args.branch)
    prepare_repo(repo_dir, workspace)
    git_commit_and_push(repo_dir, args.branch, args.message, do_push=not args.no_push)

    head = run(["git", "rev-parse", "--short", "HEAD"], cwd=repo_dir).stdout.strip()
    write_sync_state(workspace, fingerprint, head)
    print(f"Синхронизация завершена. Локальный репозиторий: {repo_dir}")
    print(f"Текущий коммит: {head}")
    if args.no_push:
        print("Push не выполнялся.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
