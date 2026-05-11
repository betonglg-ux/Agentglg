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
            "- `protocols/` хранит шаблоны протоколов, на которых держится сверка PDF;",
            "- `agent-development/` хранит материалы для воспроизведения и развития агента;",
            "- `xl/` хранит технические ресурсы, связанные с табличными материалами.",
            "",
            "## 5. Приоритеты зеркалирования",
            "1. все шаблоны из `protocols/`;",
            "2. служебные материалы из `agent-development/`;",
            "3. память агента и экспорт устойчивых правил;",
            "4. технические файлы, если они реально нужны для восстановления среды.",
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
            "- структуру `agent-development/`;
            - папку `protocols/` с шаблонами;",
            "- память и экспорт подтвержденных правил.",
        ]
    )
    return "\n".join(lines)


def build_memory_export_readme() -> str:
    return "\n".join(
        [
            "# Memory Exports",
            "",
            "Эта папка хранит переносимые выгрузки из памяти агента.",
            "",
            "Правило:",
            "- если в памяти уже есть устойчивое знание, его нужно дублировать сюда в читаемом виде;",
            "- если память ещё не заполнена, здесь остаются заготовки для будущих экспортов.",
        ]
    )


def build_skills_index_readme() -> str:
    return "\n".join(
        [
            "# Индекс навыков для переноса",
            "",
            "Назначение: этот файл фиксирует навыки, которые используются текущим агентом, и описывает, что нужно восстановить при создании будущего похожего агента.",
            "",
            "## 1. Обязательный навык",
            "",
            "### `glavlab-protocol-review`",
            "- Тип: прикреплённый загруженный навык",
            "- Роль: основной регламент проверки строительных PDF-протоколов",
            "- Статус: критически важен для корректной работы агента",
            "",
            "## 2. За что отвечает навык",
            "",
            "Навык `glavlab-protocol-review` используется как главный регламент проверки и определяет базовую логику работы агента при анализе PDF-протоколов.",
            "",
            "Он нужен для задач вида:",
            "- проверка одного или нескольких PDF-протоколов;",
            "- разбиение PDF на отдельные протоколы;",
            "- проверка оформления, структуры и расчётов;",
            "- поиск дефектов в колонтитулах, таблицах, рамках, нумерации и полях;",
            "- формирование постраничного отчёта по ошибкам и замечаниям.",
            "",
            "## 3. Почему этот навык обязателен",
            "",
            "Без этого навыка агент теряет основной регламент проверки.",
            "",
            "Даже если инструкции агента сохранены отдельно, именно этот навык остаётся главным источником специализированной логики:",
            "- как интерпретировать задачу проверки;",
            "- как находить и классифицировать ошибки;",
            "- как работать с несколькими протоколами в одном PDF;",
            "- как формировать структурированный результат.",
            "",
            "## 4. Что нужно перенести вместе с навыком",
            "",
            "При восстановлении похожего агента нужно перенести не только само упоминание навыка, но и связанный с ним контекст:",
            "",
            "1. сам навык `glavlab-protocol-review`;
            2. инструкции агента, которые ссылаются на этот навык как на основной регламент;
            3. шаблоны и файлы из папки `protocols/`, с которыми навык работает совместно;
            4. накопленные паттерны ошибок и заметки по шаблонам, если они влияют на применение навыка;
            5. материалы GitHub-зеркала, если навык или его рабочая логика там были дополнены.",
            "",
            "## 5. Минимальный комплект для клонирования агента",
            "",
            "Если создаётся новый похожий агент, нужно восстановить в первую очередь:",
            "- `agent-development/current-agent-instructions.md`",
            "- навык `glavlab-protocol-review`",
            "- папку `protocols/`",
            "- ключевые данные из Memory и GitHub-зеркала",
            "",
            "## 6. Что стоит добавить позже",
            "",
            "При следующем этапе инвентаризации желательно дополнить этот индекс:",
            "- экспортом текста самого навыка;",
            "- структурой внутренних файлов навыка, если она доступна;",
            "- списком связанных шаблонов и примеров, которые особенно важны для его работы.",
            "",
            "## 7. Вывод",
            "",
            "Для будущих агентов навык `glavlab-protocol-review` нужно считать обязательным компонентом ядра. Новый агент без него не будет полноценной копией текущего.",
        ]
    )


def refresh_agent_files_service_dir(
    target_dir: Path,
    source_dir: Path,
    workspace: Path,
    protocols_dir: Path,
    memory_dir: Path,
    changelog_text: str | None,
) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)

    for file_name in ["github-export-bundle.md", "github-mirror-manifest.md", "recovery-plan.md"]:
        source_path = source_dir / file_name
        target_path = target_dir / file_name
        if source_path.resolve() == target_path.resolve():
            continue
        copy_file(source_path, target_path)

    if changelog_text is not None:
        write_text(target_dir / "CHANGELOG.md", changelog_text)
    else:
        source_path = source_dir / "CHANGELOG.md"
        target_path = target_dir / "CHANGELOG.md"
        if source_path.resolve() != target_path.resolve():
            copy_file(source_path, target_path)

    copy_file(workspace / "AGENTS.md", target_dir / "current-agent-instructions.md")
    source_agent_summary = source_dir / "agent-summary.md"
    if source_agent_summary.exists():
        copy_file(source_agent_summary, target_dir / "agent-summary.md")
    else:
        write_text(target_dir / "agent-summary.md", build_agent_summary(protocols_dir))

    memory_exports_dir = target_dir / "memory-exports"
    memory_exports_dir.mkdir(parents=True, exist_ok=True)
    source_memory_exports_readme = source_dir / "memory-exports" / "README.md"
    if source_memory_exports_readme.exists():
        copy_file(source_memory_exports_readme, memory_exports_dir / "README.md")
    else:
        write_text(memory_exports_dir / "README.md", build_memory_export_readme())
    export_map = {
        "confirmed-error-patterns.md": "confirmed-error-patterns-export.md",
        "missed-findings-log.md": "missed-findings-export.md",
        "template-notes.md": "template-notes-export.md",
        "user-confirmed-corrections.md": "user-corrections-export.md",
        "user-preferences.md": "user-preferences-export.md",
        "memory-save-log.md": "memory-save-log-export.md",
    }
    for memory_name, export_name in export_map.items():
        source = memory_dir / memory_name
        target = memory_exports_dir / export_name
        if source.exists():
            copy_file(source, target)
        else:
            write_text(target, build_placeholder(export_name.replace("-", " ").replace(".md", "").title(), memory_name))

    skills_dir = target_dir / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    source_skills_readme = source_dir / "skills" / "README.md"
    if source_skills_readme.exists():
        copy_file(source_skills_readme, skills_dir / "README.md")
    else:
        write_text(skills_dir / "README.md", build_skills_index_readme())

    files_index_dir = target_dir / "files-index"
    files_index_dir.mkdir(parents=True, exist_ok=True)
    write_text(files_index_dir / "attached-files-index.md", format_attached_files_index(workspace / "agent_files", target_dir))
    write_text(files_index_dir / "templates-index.md", format_protocols(protocols_dir))


def build_memory_index(memory_dir: Path) -> str:
    files = list_memory_markdown_files(memory_dir)
    lines = [
        "# Memory Index",
        "",
        "Этот файл автоматически показывает, какие markdown-файлы реально есть в памяти агента и были выгружены в зеркало.",
        "",
    ]
    if not files:
        lines.append("- markdown-файлы в памяти пока не найдены")
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


def append_sync_changelog(changelog_path: Path) -> None:
    today = dt.datetime.now(dt.UTC).date().isoformat()
    sync_line = f"- выполнен автоматический экспорт в GitHub-зеркало и пересборка служебных индексов."
    if changelog_path.exists():
        existing = changelog_path.read_text(encoding="utf-8")
    else:
        existing = "# CHANGELOG GitHub-зеркала\n\nРепозиторий зеркала: `betonglg-ux/Agentglg`\n"

    marker = f"## {today}"
    if marker not in existing:
        existing = existing.rstrip() + f"\n\n## {today}\n\n### Экспорт в зеркало\n{sync_line}\n"
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


def list_workspace_paths(workspace: Path) -> list[Path]:
    paths: list[Path] = []
    for path in sorted(workspace.rglob("*")):
        rel = path.relative_to(workspace)
        if should_skip_workspace_relative(rel):
            continue
        paths.append(path)
    return paths


def build_workspace_copy_ignore(workspace: Path):
    def _ignore(dir_path: str, names: list[str]) -> set[str]:
        current = Path(dir_path)
        ignored: set[str] = set()
        for name in names:
            rel = (current / name).relative_to(workspace)
            if should_skip_workspace_relative(rel):
                ignored.add(name)
        return ignored

    return _ignore


def iter_sync_inputs(workspace: Path) -> list[Path]:
    files: list[Path] = []
    for path in list_workspace_paths(workspace):
        if path.is_file():
            files.append(path)
    return files


def compute_workspace_fingerprint(workspace: Path) -> str:
    digest = hashlib.sha256()
    for path in iter_sync_inputs(workspace):
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


def prepare_repo(repo_root: Path, workspace: Path) -> None:
    agent_files = workspace / "agent_files"
    memory_dir = workspace / "memory"
    protocols_dir = agent_files / "protocols"
    agent_dev_src = agent_files / "agent-development"
    agent_dev_dst = repo_root / "agent-development"

    ignore_workspace = build_workspace_copy_ignore(workspace)
    tracked_top_level = set()
    for child in sorted(workspace.iterdir()):
        name = child.name
        if name in WORKSPACE_EXCLUDE_TOP_LEVEL:
            continue
        tracked_top_level.add(name)
        target = repo_root / name
        if child.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(
                child,
                target,
                ignore=ignore_workspace,
            )
        else:
            copy_file(child, target)

    for child in repo_root.iterdir():
        name = child.name
        if name in REPO_PROTECTED_TOP_LEVEL:
            continue
        if name not in tracked_top_level:
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

    preserved_changelog = None
    changelog_path = agent_dev_dst / "CHANGELOG.md"
    if changelog_path.exists():
        preserved_changelog = changelog_path.read_text(encoding="utf-8")
    if agent_dev_dst.exists():
        shutil.rmtree(agent_dev_dst)
    agent_dev_dst.mkdir(parents=True, exist_ok=True)

    for file_name in ["github-mirror-manifest.md", "github-export-bundle.md", "recovery-plan.md"]:
        copy_file(agent_dev_src / file_name, agent_dev_dst / file_name)
    if preserved_changelog is not None:
        write_text(agent_dev_dst / "CHANGELOG.md", preserved_changelog)
    else:
        copy_file(agent_dev_src / "CHANGELOG.md", agent_dev_dst / "CHANGELOG.md")

    refresh_agent_files_service_dir(
        target_dir=repo_root / "agent_files" / "agent-development",
        source_dir=agent_dev_src,
        workspace=workspace,
        protocols_dir=protocols_dir,
        memory_dir=memory_dir,
        changelog_text=preserved_changelog,
    )

    copy_tree(protocols_dir, agent_dev_dst / "protocols")
    write_text(agent_dev_dst / "protocols" / "README.md", "# Protocols\n\nЭта папка автоматически собирается из локальной папки `agent_files/protocols/`.")

    memory_exports_dir = agent_dev_dst / "memory-exports"
    memory_exports_dir.mkdir(parents=True, exist_ok=True)
    source_memory_exports_readme = agent_dev_src / "memory-exports" / "README.md"
    if source_memory_exports_readme.exists():
        copy_file(source_memory_exports_readme, memory_exports_dir / "README.md")
    else:
        write_text(memory_exports_dir / "README.md", build_memory_export_readme())
    write_text(memory_exports_dir / "memory-index.md", build_memory_index(memory_dir))
    export_map = {
        "confirmed-error-patterns.md": "confirmed-error-patterns-export.md",
        "missed-findings-log.md": "missed-findings-export.md",
        "template-notes.md": "template-notes-export.md",
        "user-confirmed-corrections.md": "user-corrections-export.md",
        "user-preferences.md": "user-preferences-export.md",
        "memory-save-log.md": "memory-save-log-export.md",
    }
    for memory_name, export_name in export_map.items():
        source = memory_dir / memory_name
        target = memory_exports_dir / export_name
        if source.exists():
            copy_file(source, target)
        else:
            write_text(target, build_placeholder(export_name.replace("-", " ").replace(".md", "").title(), memory_name))

    raw_memory_dir = memory_exports_dir / "raw-memory"
    raw_memory_dir.mkdir(parents=True, exist_ok=True)
    for source in list_memory_markdown_files(memory_dir):
        target = raw_memory_dir / source.relative_to(memory_dir)
        copy_file(source, target)

    copy_file(workspace / "AGENTS.md", agent_dev_dst / "current-agent-instructions.md")
    source_agent_summary = agent_dev_src / "agent-summary.md"
    if source_agent_summary.exists():
        copy_file(source_agent_summary, agent_dev_dst / "agent-summary.md")
    else:
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
    write_text(
        agent_dev_dst / "user-preferences.md",
        (memory_dir / "user-preferences.md").read_text(encoding="utf-8")
        if (memory_dir / "user-preferences.md").exists()
        else build_placeholder("User Preferences", "memory/user-preferences.md"),
    )
    write_text(
        agent_dev_dst / "slack-user-corrections.md",
        (memory_dir / "slack-user-corrections.md").read_text(encoding="utf-8")
        if (memory_dir / "slack-user-corrections.md").exists()
        else build_placeholder("Slack User Corrections", "memory/slack-user-corrections.md"),
    )
    write_text(
        agent_dev_dst / "memory-save-log.md",
        (memory_dir / "memory-save-log.md").read_text(encoding="utf-8")
        if (memory_dir / "memory-save-log.md").exists()
        else build_placeholder("Memory Save Log", "memory/memory-save-log.md"),
    )

    skills_dir = agent_dev_dst / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    source_skills_readme = agent_dev_src / "skills" / "README.md"
    if source_skills_readme.exists():
        copy_file(source_skills_readme, skills_dir / "README.md")
    else:
        write_text(
            skills_dir / "README.md",
            "# Skills\n\nЭта папка автоматически собирает ключевые навыки, которые нужно переносить вместе с агентом.",
        )
    if SKILL_PATH.exists():
        copy_file(SKILL_PATH, skills_dir / "glavlab-protocol-review" / "SKILL.md")

    files_index_dir = agent_dev_dst / "files-index"
    files_index_dir.mkdir(parents=True, exist_ok=True)
    write_text(files_index_dir / "README.md", "# Files Index\n\nЭтот раздел автоматически собирается при экспорте в зеркало.")
    write_text(files_index_dir / "attached-files-index.md", format_attached_files_index(agent_files, agent_dev_dst))
    write_text(files_index_dir / "templates-index.md", format_protocols(protocols_dir))

    manifest_src = agent_dev_src / "github-mirror-manifest.md"
    if manifest_src.exists():
        copy_file(manifest_src, repo_root / "github-mirror-manifest.md")

    for rel_path in [TOKEN_FILE_RELATIVE, PRIVATE_TOKEN_FILE_RELATIVE, SYNC_STATE_FILE_RELATIVE]:
        mirrored = repo_root / rel_path
        if mirrored.exists():
            mirrored.unlink()


def clone_or_update_repo(repo_root: Path, branch: str, repo_url: str, workspace: Path) -> None:
    if not repo_root.exists():
        if workspace_uses_git(workspace):
            run(["git", "clone", str(workspace), str(repo_root)])
            run(["git", "remote", "set-url", "origin", repo_url], cwd=repo_root)
            run(["git", "fetch", "origin", branch], cwd=repo_root)
            run(["git", "checkout", "-B", branch, f"origin/{branch}"], cwd=repo_root)
            return
        run(["git", "clone", "--branch", branch, repo_url, str(repo_root)])
        return
    run(["git", "remote", "set-url", "origin", repo_url], cwd=repo_root)
    run(["git", "fetch", "origin", branch], cwd=repo_root)
    run(["git", "checkout", branch], cwd=repo_root, check=False)
    if run(["git", "rev-parse", "--verify", branch], cwd=repo_root, check=False).returncode != 0:
        run(["git", "checkout", "-B", branch, f"origin/{branch}"], cwd=repo_root)
        return
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
    parser = argparse.ArgumentParser(description="Экспорт текущей рабочей среды агента в GitHub-зеркало betonglg-ux/Agentglg")
    parser.add_argument("--workspace", default="/workspace/memory", help="Корень рабочей среды агента")
    parser.add_argument("--repo-dir", default="", help="Путь до локального клона репозитория")
    parser.add_argument("--branch", default="", help="Ветка для экспорта. По умолчанию определяется из локального зеркала.")
    parser.add_argument("--message", default="Export agent mirror from workspace", help="Сообщение коммита")
    parser.add_argument("--no-push", action="store_true", help="Подготовить и закоммитить изменения без отправки в GitHub")
    parser.add_argument("--only-if-changed", action="store_true", help="Запускать экспорт только если рабочие файлы изменились")
    parser.add_argument(
        "--allow-memory-overwrite",
        action="store_true",
        help="Разрешить экспорт даже если в зеркале найдены строки памяти, которых нет локально",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace).resolve()
    if not workspace.exists():
        print(f"Не найден workspace: {workspace}", file=sys.stderr)
        return 1

    branch = args.branch or detect_branch(workspace)
    repo_url = detect_repo_url(workspace)

    fingerprint = compute_workspace_fingerprint(workspace)
    if args.only_if_changed:
        previous = read_sync_state(workspace)
        if previous == fingerprint:
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
            f"или сохраните токен в {workspace / PRIVATE_TOKEN_FILE_RELATIVE} "
            f"или {workspace / TOKEN_FILE_RELATIVE}.",
            file=sys.stderr,
        )
        return 1

    missing_memory_files = [name for name in REQUIRED_MEMORY_FILES if not (workspace / "memory" / name).exists()]
    if missing_memory_files:
        joined = ", ".join(missing_memory_files)
        raise RuntimeError(
            "Экспорт остановлен: отсутствуют обязательные локальные файлы памяти.\n"
            f"Не найдены: {joined}\n"
            "Экспорт работает только от текущей локальной памяти к зеркалу и не подставляет старые копии из служебных файлов."
        )

    snapshot_dir = snapshot_memory_files(workspace)
    repo_dir = Path(args.repo_dir).resolve() if args.repo_dir else Path(tempfile.gettempdir()) / "agentglg-mirror-repo"
    clone_or_update_repo(repo_dir, branch, repo_url, workspace)
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
    prepare_repo(repo_dir, workspace)
    if git_has_changes(repo_dir):
        append_sync_changelog(repo_dir / "agent-development" / "CHANGELOG.md")
    git_commit_and_push(repo_dir, branch, args.message, do_push=not args.no_push)

    head = run(["git", "rev-parse", "--short", "HEAD"], cwd=repo_dir).stdout.strip()
    write_sync_state(workspace, fingerprint, head)
    print(f"Экспорт в зеркало завершен. Локальный репозиторий: {repo_dir}")
    print(f"Текущий коммит: {head}")
    if args.no_push:
        print("Отправка в GitHub не выполнялась.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())