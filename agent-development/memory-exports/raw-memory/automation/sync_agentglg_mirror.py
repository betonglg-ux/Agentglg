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


def paths_overlap(left: Path, right: Path) -> bool:
    try:
        common = os.path.commonpath([str(left.resolve()), str(right.resolve())])
    except ValueError:
        return False
    return common in {str(left.resolve()), str(right.resolve())}


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


def memory_dir_has_required_files(path: Path) -> bool:
    return path.exists() and all((path / name).exists() for name in REQUIRED_MEMORY_FILES)


def resolve_source_context(workspace: Path) -> tuple[Path, Path, Path]:
    source_roots: list[Path] = []
    if workspace not in source_roots:
        source_roots.append(workspace)
    mirror_checkout = detect_mirror_checkout(workspace)
    if mirror_checkout and mirror_checkout not in source_roots:
        source_roots.append(mirror_checkout)

    checked_contexts: list[str] = []
    for source_root in source_roots:
        instructions_path = source_root / "AGENTS.md"
        agent_files_dir = source_root / "agent_files"
        memory_candidates = [
            source_root / "memory" / "memory",
            source_root / "memory",
        ]
        checked_contexts.append(
            f"{source_root} -> instructions={instructions_path}, agent_files={agent_files_dir}, memory={', '.join(str(path) for path in memory_candidates)}"
        )

        if not instructions_path.exists() or not agent_files_dir.exists():
            continue

        for candidate in memory_candidates:
            if memory_dir_has_required_files(candidate):
                return instructions_path, agent_files_dir, candidate

    checked = "\n".join(f"- {item}" for item in checked_contexts)
    raise RuntimeError(
        "Не удалось определить актуальные инструкции, agent_files и локальную память.\n"
        "Проверены контексты:\n"
        f"{checked}"
    )


def resolve_agent_development_source(workspace: Path, agent_files_dir: Path) -> Path:
    candidates = [
        workspace / "memory" / "agent-development",
        workspace / "agent-development",
        agent_files_dir / "agent-development",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    return agent_files_dir / "agent-development"


def workspace_uses_git(workspace: Path) -> bool:
    return (workspace / ".git").exists()


def detect_mirror_checkout(workspace: Path) -> Path | None:
    candidates = [workspace, workspace / "memory"]
    for candidate in candidates:
        if workspace_uses_git(candidate) and workspace_looks_like_mirror_checkout(candidate):
            return candidate
    return None


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


def workspace_looks_like_mirror_checkout(workspace: Path) -> bool:
    required_paths = [
        workspace / "github-mirror-manifest.md",
        workspace / "agent-development",
        workspace / "memory" / "automation" / "sync_agentglg_mirror.py",
    ]
    return all(path.exists() for path in required_paths)


def detect_repo_url(workspace: Path) -> str:
    env_repo_url = os.getenv("AGENTGLG_REPO_URL")
    if env_repo_url:
        return env_repo_url.strip()
    repo_url = get_workspace_origin_url(workspace)
    if repo_url and is_target_mirror_repo_url(repo_url):
        return repo_url
    if repo_url and workspace_looks_like_mirror_checkout(workspace):
        return repo_url
    mirror_checkout = detect_mirror_checkout(workspace)
    if mirror_checkout and mirror_checkout != workspace:
        repo_url = get_workspace_origin_url(mirror_checkout)
        if repo_url:
            return repo_url
    return DEFAULT_REPO_URL


def repo_uses_direct_github(repo_url: str) -> bool:
    return "github.com" in repo_url and "chatgpt.com/backend-api/git-authed/" not in repo_url


def detect_branch(workspace: Path) -> str:
    env_branch = os.getenv("AGENTGLG_BRANCH")
    if env_branch:
        return env_branch.strip()

    if workspace_uses_git(workspace):
        current_branch = run(
            ["git", "branch", "--show-current"],
            cwd=workspace,
            check=False,
        ).stdout.strip()
        if current_branch:
            return current_branch

        remote_head = run(
            ["git", "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
            cwd=workspace,
            check=False,
        ).stdout.strip()
        if remote_head.startswith("origin/"):
            return remote_head.removeprefix("origin/")

    mirror_checkout = detect_mirror_checkout(workspace)
    if mirror_checkout and mirror_checkout != workspace:
        return detect_branch(mirror_checkout)

    return DEFAULT_BRANCH


def normalize_significant_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lines.append(line)
    return lines


def snapshot_memory_files(memory_dir: Path) -> Path | None:
    files_to_copy = [memory_dir / name for name in PROTECTED_MEMORY_FILES if (memory_dir / name).exists()]
    if not files_to_copy:
        return None

    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    snapshot_dir = memory_dir / "snapshots" / stamp
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


def detect_memory_regressions(repo_root: Path, memory_dir: Path) -> list[str]:
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
            if rel.as_posix() == "files-index/attached-files-index.md":
                continue
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
    if target_dir.exists():
        shutil.rmtree(target_dir)
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
