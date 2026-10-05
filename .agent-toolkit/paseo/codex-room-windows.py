#!/usr/bin/env python3
"""Launch one Codex Room role with a native Windows CODEX_HOME.

Windows port of the runtime generation contract in hoangnb24/codex-room-setup
commit 348129092cb1bf92176f062bca0ca0ddda3cfbfe. The role overlays and
shared instructions are installed separately from that pinned commit.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


ROLES = ("supervisor", "lead", "peer")
OVERRIDE_KEYS = {
    "model", "model_reasoning_effort", "sandbox_mode", "approval_policy",
    "approvals_reviewer", "model_instructions_file",
}
REQUIRED_SHARED = ("auth.json",)
OPTIONAL_SHARED = ("AGENTS.md", "hooks.json", "skills", "plugins")


def fail(message: str) -> None:
    raise SystemExit(f"codex-room-windows: {message}")


def canonical_home() -> Path:
    return Path(os.environ.get("CODEX_ROOM_CANONICAL_HOME", Path.home() / ".codex")).resolve()


def room_home() -> Path:
    return Path(os.environ.get("CODEX_ROOM_CONFIG_HOME", Path.home() / ".config" / "codex-room")).resolve()


def runtime_root() -> Path:
    return Path(os.environ.get("CODEX_ROOM_RUNTIME_ROOT", Path.home() / ".codex-runtime")).absolute()


def top_level_offset(content: str) -> int:
    match = re.search(r"(?m)^\[", content)
    return match.start() if match else len(content)


def developer_block(content: str) -> str:
    match = re.search(r'(?ms)^developer_instructions\s*=\s*""".*?^"""\s*$', content)
    if not match:
        fail("role overlay has no developer_instructions block")
    return match.group(0).rstrip() + "\n"


def scalar_overrides(content: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in content[:top_level_offset(content)].splitlines():
        match = re.match(r"^([A-Za-z0-9_]+)\s*=\s*(.+)$", line)
        if match and match.group(1) in OVERRIDE_KEYS:
            values[match.group(1)] = match.group(2)
    return values


def apply_scalar_overrides(base_head: str, values: dict[str, str]) -> str:
    # Remove an inherited top-level developer block before adding the role one.
    base_head = re.sub(r'(?ms)^developer_instructions\s*=\s*""".*?^"""\s*\n?', "", base_head)
    lines = base_head.rstrip().splitlines()
    seen: set[str] = set()
    rendered: list[str] = []
    for line in lines:
        match = re.match(r"^([A-Za-z0-9_]+)\s*=", line)
        if match and match.group(1) in values:
            key = match.group(1)
            if key not in seen:
                rendered.append(f"{key} = {values[key]}")
                seen.add(key)
        else:
            rendered.append(line)
    for key, value in values.items():
        if key not in seen:
            rendered.append(f"{key} = {value}")
    return "\n".join(rendered).rstrip() + "\n\n"


def table_pattern(table: str) -> str:
    return rf"(?m)^\[{re.escape(table)}\][ \t]*(?:#[^\n]*)?$"


def set_table_scalar(content: str, table: str, key: str, value: str) -> str:
    match = re.search(table_pattern(table), content)
    if not match:
        offset = top_level_offset(content)
        head = content[:offset]
        dotted_key = f"{table}.{key}"
        dotted_key_pattern = rf"(?m)^[ \t]*{re.escape(dotted_key)}[ \t]*=.*$"
        if re.search(dotted_key_pattern, head):
            head = re.sub(
                dotted_key_pattern,
                f"{dotted_key} = {value}",
                head,
                count=1,
            )
            return head + content[offset:]
        dotted_table_pattern = rf"(?m)^[ \t]*{re.escape(table)}\.[^=\n]+[ \t]*="
        if re.search(dotted_table_pattern, head):
            return (
                head.rstrip()
                + f"\n{dotted_key} = {value}\n\n"
                + content[offset:].lstrip()
            )
        return content.rstrip() + f"\n\n[{table}]\n{key} = {value}\n"
    next_table = re.search(r"(?m)^\[", content[match.end():])
    end = match.end() + (next_table.start() if next_table else len(content[match.end():]))
    section = content[match.end():end]
    key_pattern = rf"(?m)^{re.escape(key)}\s*=.*$"
    if re.search(key_pattern, section):
        section = re.sub(key_pattern, f"{key} = {value}", section, count=1)
    else:
        section = section.rstrip() + f"\n{key} = {value}\n\n"
    return content[:match.end()] + section + content[end:]


def merged_config(base: str, overlay: str, runtime: Path, shared: Path) -> str:
    offset = top_level_offset(base)
    values = scalar_overrides(overlay)
    values["model_catalog_json"] = json.dumps(str(runtime / "model-catalog.no-native-agents.json"))
    values["model_instructions_file"] = json.dumps(str(runtime / "model-instructions.md"))
    block = developer_block(overlay).replace(
        "~/.config/codex-room/", shared.as_posix() + "/"
    )
    result = apply_scalar_overrides(base[:offset], values) + block + "\n" + base[offset:].lstrip()
    result = set_table_scalar(result, "agents", "enabled", "false")
    result = set_table_scalar(result, "features", "multi_agent", "false")
    if re.search(table_pattern("features.multi_agent_v2"), result):
        result = set_table_scalar(result, "features.multi_agent_v2", "enabled", "false")
    else:
        result = set_table_scalar(result, "features", "multi_agent_v2", "false")
    return result


def codex_binary() -> str:
    binary = os.environ.get("CODEX_BIN") or shutil.which("codex.cmd") or shutil.which("codex")
    if not binary:
        fail("Codex CLI is not on the daemon PATH; set CODEX_BIN")
    return binary


def model_catalog(binary: str, canonical: Path) -> str:
    fixture = os.environ.get("CODEX_ROOM_MODEL_CATALOG")
    if fixture:
        catalog = json.loads(Path(fixture).read_text(encoding="utf-8"))
    else:
        env = os.environ.copy()
        env["CODEX_HOME"] = str(canonical)
        completed = subprocess.run(
            [binary, "debug", "models"], env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True
        )
        catalog = json.loads(completed.stdout)
    models = catalog.get("models")
    if not isinstance(models, list) or not models or not all(isinstance(m, dict) for m in models):
        fail("Codex model catalog is empty or malformed")
    for model in models:
        model["multi_agent_version"] = None
    return json.dumps(catalog, separators=(",", ":")) + "\n"


def is_redirect(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def link_shared(runtime: Path, name: str, target: Path) -> None:
    path = runtime / name
    if not target.exists():
        fail(f"missing shared resource: {target}")
    if path.exists() or is_redirect(path):
        if target.is_dir() and is_redirect(path) and path.resolve() == target.resolve():
            return
        if target.is_file() and path.is_file() and not is_redirect(path) and path.samefile(target):
            return
        fail(f"shared path differs from canonical resource: {path}; inspect it before repair")
    if target.is_dir():
        helper = Path(__file__).with_name("new-junction.ps1")
        powershell = Path(os.environ.get("SystemRoot", "C:/Windows")) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
        completed = subprocess.run(
            [str(powershell), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
             "-File", str(helper), "-Link", str(path), "-Target", str(target)],
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        if completed.returncode:
            fail(f"could not create junction {path}: {completed.stderr.strip()}")
    else:
        os.link(target, path)


def write_atomic(path: Path, content: str) -> None:
    if path.is_file() and path.read_text(encoding="utf-8") == content:
        return
    descriptor, temp = tempfile.mkstemp(prefix=path.stem + ".", suffix=path.suffix, dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def sync(role: str) -> tuple[Path, str]:
    canonical = canonical_home()
    shared = room_home()
    root = runtime_root()
    runtime = root / role
    if is_redirect(root) or is_redirect(runtime):
        fail("runtime root or role directory is a redirect")
    if root.resolve() == canonical or canonical in root.resolve().parents:
        fail("runtime root overlaps canonical Codex home")
    base_path = canonical / "config.toml"
    overlay_path = shared / "overlays" / f"{role}.config.toml"
    for item in (base_path, overlay_path, shared / "model-instructions.md",
                 shared / "workflow" / "WORKSPACE_PROTOCOL.md"):
        if not item.is_file():
            fail(f"required source is missing: {item}")
    names = list(REQUIRED_SHARED)
    names += [name for name in OPTIONAL_SHARED if (canonical / name).exists()]
    for name in names:
        if not (canonical / name).exists():
            fail(f"required shared resource is missing: {canonical / name}")
    for name in ("config.toml", "model-catalog.no-native-agents.json"):
        if is_redirect(runtime / name):
            fail(f"managed runtime output is a redirect: {runtime / name}")
    binary = codex_binary()
    catalog = model_catalog(binary, canonical)
    merged = merged_config(base_path.read_text(encoding="utf-8"),
                           overlay_path.read_text(encoding="utf-8"), runtime, shared)
    root.mkdir(exist_ok=True)
    runtime.mkdir(exist_ok=True)
    write_atomic(runtime / "model-catalog.no-native-agents.json", catalog)
    write_atomic(runtime / "config.toml", merged)
    for name in names:
        link_shared(runtime, name, canonical / name)
    link_shared(runtime, "model-instructions.md", shared / "model-instructions.md")
    return runtime, binary


def main() -> int:
    argv = sys.argv[1:]
    sync_only = bool(argv and argv[0] == "--sync-only")
    if sync_only:
        argv.pop(0)
    if not argv or argv[0] not in ROLES:
        fail("usage: codex-room-windows.py [--sync-only] <supervisor|lead|peer> [codex args...]")
    role = argv.pop(0)
    runtime, binary = sync(role)
    if sync_only:
        print(f"SYNC_OK role={role} runtime={runtime}", file=sys.stderr)
        return 0
    env = os.environ.copy()
    env["CODEX_HOME"] = str(runtime)
    return subprocess.call([binary, *argv], env=env)


if __name__ == "__main__":
    sys.exit(main())
