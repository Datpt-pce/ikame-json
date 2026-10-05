#!/usr/bin/env python3
"""Install three Codex Room Paseo profiles with role-specific model choices.

The default is a read-only plan. --apply owns the host transition and keeps a
timestamped backup. --reload asks the running Paseo daemon to load the result.

Upstream role overlays are validated against the Windows role contract first.
An optional local-policy.toml beside this script is applied afterwards, so a
host may narrow role permissions or the fallback heartbeat cadence without
editing generated files or weakening the upstream contract check.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from urllib.request import Request, urlopen


COMMIT = "348129092cb1bf92176f062bca0ca0ddda3cfbfe"
REPOSITORY = "hoangnb24/codex-room-setup"
SOURCES = {
    "overlays/supervisor.config.toml": "3d967e6174720419857441f5ac882dc4f8ae4e8ef3d84107ad41a44794bc0e53",
    "overlays/lead.config.toml": "6d63286b9973553473224ebc39b6f9f4475ab217e339ca2c93d95a4193a4f89a",
    "overlays/peer.config.toml": "5abc3d39e62b0f70f70753ce85736b6218a4e3bb60fa0161ba3b75edcb22fbb1",
    "workflow/WORKSPACE_PROTOCOL.md": "9ab615ded7039431f9a5d235fbfb84b91c489fae35bd2bf314bd9efae3ec387c",
    "model-instructions.md": "5960b54e1d3904788d184d2650f91cd09d6e2cbcfd8509d5d90f3a530e1ba7c9",
}
ROLES = ("supervisor", "lead", "peer")
ALIASES = tuple(f"codex-{role}" for role in ROLES)
ROLE_OPTIONS = {
    "supervisor": (("gpt-5.6-sol", "medium"),),
    "lead": (("gpt-5.6-sol", "high"), ("gpt-5.6-sol", "xhigh"), ("gpt-6-sol", "medium")),
    "peer": (("gpt-5.6-terra", "high"), ("gpt-5.6-terra", "xhigh"), ("gpt-5.6-terra", "max")),
}
PROFILE_IDS = tuple(f"codex-room-{role}" for role in ROLES)
NAMES = {"supervisor": "Codex Room Supervisor", "lead": "Codex Room Lead", "peer": "Codex Room Peer"}
NOTES = {
    "supervisor": "Human contact and portfolio monitor. Read the shared Room protocol; route project technical work to Lead. Use Paseo orchestration tools only for bounded supervision and recovery.",
    "lead": "Sole technical owner. Define bounded outcomes, brief Peers, integrate and verify exact candidates, and explicitly accept or reject with evidence.",
    "peer": "Own one bounded outcome delegated by Lead. Return an immutable candidate or a concrete blocker with proof. Do not orchestrate or accept your own work.",
}
SCRIPT_DIR = Path(__file__).resolve().parent
POLICY_FILE = "local-policy.toml"
LOCAL_HELPERS = ("codex-room-windows.py", "new-junction.ps1", "slp-budget.py")
SANDBOX_MODES = ("read-only", "workspace-write", "danger-full-access")
APPROVAL_POLICIES = ("untrusted", "on-failure", "on-request", "never")
PASEO_MODE_IDS = ("auto", "auto-review", "full-access")
ROLE_POLICY_KEYS = {"sandbox_mode", "approval_policy", "paseo_mode_id"}
DEFAULT_MODE_ID = "full-access"
CRON_FIELDS = re.compile(r"[0-9*/,\-]+( [0-9*/,\-]+){4}")
HEARTBEAT_CRON = re.compile(r'cron "([^"\n]+)"')
HEARTBEAT_USAGE_ANCHOR = "returned schedule ID privately."
HEARTBEAT_USAGE_INSTRUCTION = (
    "\nOn every heartbeat, run `python ~/.config/codex-room/slp-budget.py "
    "--root-agent \"$PASEO_AGENT_ID\" --compact` from Git Bash to sample cumulative "
    "usage. The report separates input, cached input, noncached input, output, and reasoning "
    "tokens, role totals, measured sessions, and UNKNOWN sessions. Keep the compact result "
    "for status; run without --compact when a per-session breakdown is needed. Surface a new "
    "UNKNOWN or budget concern, but do not message Human or Lead solely because counters "
    "rose. A reused session's total is not exact story spend. If the report fails, state "
    "that usage visibility is unavailable.\n"
)
STALL_INTERVENTION_INSTRUCTION = (
    "\nFor an SLP Lead-Peer stall, investigate two rejects of the same failure class, "
    "a round with no new executable signal, a missed Lead disposition checkpoint, "
    "or a threatened Human-approved budget/reserve. Compare the exact candidate, "
    "matrix row, Peer evidence, Lead response, and usage delta; message count or "
    "cumulative tokens alone are not proof of waste. Do not launch another "
    "Supervisor-routed dependent dispatch until Lead closes that loop. Ask Lead "
    "an open evidence-based question and follow the answer to a recorded decision. "
    "Lead owns technical acceptance: do not choose a side, validate project work, "
    "or direct Peer. Use at most one bounded independent check for a disputed "
    "observable fact. Two same-class rejects reopen design through Lead; a third "
    "or material extra cost, scope, or risk goes to Human with options and a "
    "recommendation. Human owns material cost and product risk. Keep unrelated "
    "ready work moving. This is not a mechanical dispatch gate.\n"
)


def fail(message: str) -> None:
    raise SystemExit(f"codex-room-install: {message}")


def redirected(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def preflight_path(path: Path, boundary: Path) -> None:
    candidate = path
    while candidate != boundary:
        if redirected(candidate):
            fail(f"managed path or parent is redirected: {candidate}")
        if candidate.exists() and not candidate.is_dir() and candidate != path:
            fail(f"managed parent is not a directory: {candidate}")
        if candidate.parent == candidate:
            fail(f"managed path escapes expected home: {path}")
        candidate = candidate.parent


def codex_catalog() -> dict:
    binary = os.environ.get("CODEX_BIN") or shutil.which("codex.cmd") or shutil.which("codex")
    if not binary:
        fail("Codex CLI is unavailable on PATH")
    completed = subprocess.run([binary, "debug", "models"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if completed.returncode:
        fail("codex debug models failed; verify Codex login and CLI version")
    catalog = json.loads(completed.stdout)
    if not isinstance(catalog.get("models"), list):
        fail("Codex model catalog is malformed")
    return catalog


def paseo_cli() -> Path | None:
    found = shutil.which("paseo")
    candidates = [Path(found)] if found else []
    local = os.environ.get("LOCALAPPDATA")
    if local:
        candidates.append(Path(local) / "Programs" / "Paseo" / "resources" / "bin" / "paseo.cmd")
    candidates.append(Path("C:/Program Files/Paseo/resources/bin/paseo.cmd"))
    return next((path for path in candidates if path.is_file()), None)


def latest_commit() -> str:
    request = Request(f"https://api.github.com/repos/{REPOSITORY}/commits/main",
                      headers={"User-Agent": "codex-room-windows-updater", "Accept": "application/vnd.github+json"})
    with urlopen(request, timeout=30) as response:
        commit = json.load(response).get("sha", "")
    if len(commit) != 40 or any(char not in "0123456789abcdef" for char in commit):
        fail("GitHub did not return a valid main commit SHA")
    return commit


def source_assets(commit: str, pinned: bool) -> dict[str, bytes]:
    assets = {}
    raw = f"https://raw.githubusercontent.com/{REPOSITORY}/{commit}/home/.config/codex-room"
    for relative, digest in SOURCES.items():
        with urlopen(f"{raw}/{relative}", timeout=30) as response:
            content = response.read()
        if len(content) > 512_000:
            fail(f"source asset is unexpectedly large: {relative}")
        if pinned and hashlib.sha256(content).hexdigest() != digest:
            fail(f"source digest mismatch: {relative}")
        assets[relative] = content
    return assets


def role_specs(assets: dict[str, bytes], catalog: dict) -> dict[str, dict]:
    specs = {}
    if not all(word in assets["workflow/WORKSPACE_PROTOCOL.md"].decode("utf-8")
               for word in ("Supervisor", "Lead", "Peer")):
        fail("upstream protocol lacks the three role names")
    if not assets["model-instructions.md"].strip():
        fail("upstream model instructions are empty")
    for role in ROLES:
        overlay = assets[f"overlays/{role}.config.toml"].decode("utf-8")
        spec = tomllib.loads(overlay)
        unsupported = set(spec) - {"model", "model_reasoning_effort", "sandbox_mode",
                                   "approval_policy", "developer_instructions",
                                   "approvals_reviewer", "model_instructions_file"}
        if unsupported or not re.search(r'(?ms)^developer_instructions\s*=\s*""".*?^"""\s*$', overlay):
            fail(f"upstream {role} overlay format changed; Windows adapter needs review")
        model = spec.get("model")
        effort = spec.get("model_reasoning_effort")
        instructions = spec.get("developer_instructions")
        if not isinstance(model, str) or not isinstance(effort, str) or not isinstance(instructions, str):
            fail(f"upstream {role} overlay lacks model, effort or instructions")
        if f"Room role: {role.capitalize()}." not in instructions or "WORKSPACE_PROTOCOL.md" not in instructions:
            fail(f"upstream {role} overlay no longer matches the Windows role contract")
        if spec.get("sandbox_mode") != "danger-full-access" or spec.get("approval_policy") != "never":
            fail(f"upstream {role} permission mode changed; Windows adapter needs review")
        found = next((entry for entry in catalog["models"] if entry.get("slug", entry.get("id")) == model), None)
        if not found:
            fail(f"upstream {role} model {model} is absent from local Codex catalog")
        levels = found.get("supported_reasoning_levels")
        if not isinstance(levels, list) or effort not in [entry.get("effort") for entry in levels]:
            fail(f"upstream {role} effort {effort} is unavailable for {model}")
        specs[role] = {"model": model, "effort": effort,
                       "sandbox": spec["sandbox_mode"], "approval": spec["approval_policy"]}
    for model, effort in (option for options in ROLE_OPTIONS.values() for option in options):
        found = next((entry for entry in catalog["models"] if entry.get("slug", entry.get("id")) == model), None)
        if not found or effort not in [level.get("effort") for level in found.get("supported_reasoning_levels", [])]:
            fail(f"requested profile model/effort is unavailable: {model}/{effort}")
    return specs


def load_local_policy(path: Path) -> tuple[dict, str | None]:
    """Read and strictly validate the optional local policy next to this script."""
    if not path.is_file():
        return {}, None
    raw = path.read_bytes()
    try:
        policy = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        fail(f"local policy is not valid UTF-8 TOML: {error}")
    unsupported = set(policy) - {"version", "roles", "heartbeat"}
    if unsupported:
        fail(f"local policy has unsupported key: {', '.join(sorted(unsupported))}")
    if policy.get("version") != 1:
        fail("local policy version must be 1")
    roles = policy.get("roles", {})
    if not isinstance(roles, dict):
        fail("local policy roles must be a table")
    for role, override in roles.items():
        if role not in ROLES:
            fail(f"local policy names an unknown role: {role}")
        if not isinstance(override, dict):
            fail(f"local policy role {role} must be a table")
        unsupported = set(override) - ROLE_POLICY_KEYS
        if unsupported:
            fail(f"local policy role {role} has unsupported key: {', '.join(sorted(unsupported))}")
        sandbox = override.get("sandbox_mode")
        if sandbox is not None and sandbox not in SANDBOX_MODES:
            fail(f"local policy role {role} sandbox_mode must be one of {', '.join(SANDBOX_MODES)}")
        approval = override.get("approval_policy")
        if approval is not None and approval not in APPROVAL_POLICIES:
            fail(f"local policy role {role} approval_policy must be one of {', '.join(APPROVAL_POLICIES)}")
        mode_id = override.get("paseo_mode_id")
        if mode_id is not None and mode_id not in PASEO_MODE_IDS:
            fail(f"local policy role {role} paseo_mode_id must be one of {', '.join(PASEO_MODE_IDS)}")
        if sandbox not in (None, "danger-full-access") and mode_id is None:
            # Paseo applies its own mode on top of the Codex sandbox. The operator
            # must name the matching mode instead of leaving the profile at full-access.
            fail(f"local policy role {role} narrows sandbox_mode and must also set paseo_mode_id")
    heartbeat = policy.get("heartbeat", {})
    if not isinstance(heartbeat, dict):
        fail("local policy heartbeat must be a table")
    unsupported = set(heartbeat) - {"cron", "usage_report", "stall_intervention"}
    if unsupported:
        fail(f"local policy heartbeat has unsupported key: {', '.join(sorted(unsupported))}")
    cron = heartbeat.get("cron")
    if cron is not None and (not isinstance(cron, str) or not CRON_FIELDS.fullmatch(cron)):
        fail("local policy heartbeat cron must be a five-field cron expression")
    if "usage_report" in heartbeat and type(heartbeat["usage_report"]) is not bool:
        fail("local policy heartbeat usage_report must be boolean")
    if "stall_intervention" in heartbeat and type(heartbeat["stall_intervention"]) is not bool:
        fail("local policy heartbeat stall_intervention must be boolean")
    return policy, hashlib.sha256(raw).hexdigest()


def replace_overlay_scalar(overlay: str, key: str, value: str, role: str) -> str:
    """Replace one top-level string scalar that precedes the instruction block."""
    match = re.search(r"(?m)^developer_instructions\s*=", overlay)
    head_end = match.start() if match else len(overlay)
    pattern = re.compile(rf'(?m)^{re.escape(key)}[ \t]*=[ \t]*"[^"\n]*"[ \t]*$')
    head = overlay[:head_end]
    if len(pattern.findall(head)) != 1:
        fail(f"upstream {role} overlay has no single {key} line; local policy cannot be applied")
    return pattern.sub(lambda _: f"{key} = {json.dumps(value)}", head, count=1) + overlay[head_end:]


def apply_local_policy(assets: dict[str, bytes], specs: dict[str, dict],
                       policy: dict) -> tuple[dict[str, bytes], dict[str, dict]]:
    """Return effective overlays and role specs; the upstream inputs stay untouched."""
    roles = policy.get("roles", {})
    cron = policy.get("heartbeat", {}).get("cron")
    usage_report = policy.get("heartbeat", {}).get("usage_report", False)
    stall_intervention = policy.get("heartbeat", {}).get("stall_intervention", False)
    if not roles and cron is None and not usage_report and not stall_intervention:
        return assets, specs
    effective_assets = dict(assets)
    effective_specs = {role: dict(spec) for role, spec in specs.items()}
    for role in ROLES:
        override = roles.get(role, {})
        name = f"overlays/{role}.config.toml"
        overlay = assets[name].decode("utf-8")
        for key, field in (("sandbox_mode", "sandbox"), ("approval_policy", "approval")):
            if key in override:
                overlay = replace_overlay_scalar(overlay, key, override[key], role)
                effective_specs[role][field] = override[key]
        effective_specs[role]["mode_id"] = override.get("paseo_mode_id", DEFAULT_MODE_ID)
        if role == "supervisor" and cron is not None:
            if len(HEARTBEAT_CRON.findall(overlay)) != 1:
                fail("upstream supervisor heartbeat wording changed; local policy cannot be applied")
            overlay = HEARTBEAT_CRON.sub(lambda _: f'cron "{cron}"', overlay, count=1)
            effective_specs[role]["heartbeat_cron"] = cron
        if role == "supervisor" and usage_report:
            if overlay.count(HEARTBEAT_USAGE_ANCHOR) != 1:
                fail("upstream supervisor heartbeat wording changed; usage report cannot be applied")
            overlay = overlay.replace(HEARTBEAT_USAGE_ANCHOR,
                                      HEARTBEAT_USAGE_ANCHOR + HEARTBEAT_USAGE_INSTRUCTION, 1)
            effective_specs[role]["heartbeat_usage_report"] = True
        if role == "supervisor" and stall_intervention:
            if overlay.count(HEARTBEAT_USAGE_ANCHOR) != 1:
                fail("upstream supervisor heartbeat wording changed; stall intervention cannot be applied")
            overlay = overlay.replace(HEARTBEAT_USAGE_ANCHOR,
                                      HEARTBEAT_USAGE_ANCHOR + STALL_INTERVENTION_INSTRUCTION, 1)
            effective_specs[role]["heartbeat_stall_intervention"] = True
        effective_assets[name] = overlay.encode("utf-8")
    return effective_assets, effective_specs


def upstream_changes(manifest_path: Path, assets: dict[str, bytes]) -> list[str]:
    """Name upstream assets whose bytes differ from the installed source manifest."""
    recorded: dict = {}
    if manifest_path.is_file():
        try:
            recorded = json.loads(manifest_path.read_text(encoding="utf-8")).get("sha256", {})
        except (json.JSONDecodeError, AttributeError):
            recorded = {}
    return sorted(name for name, content in assets.items()
                  if recorded.get(name) != hashlib.sha256(content).hexdigest())


def profile(role: str, mode_id: str = DEFAULT_MODE_ID) -> dict:
    model, effort = ROLE_OPTIONS[role][0]
    return {
        "id": f"codex-room-{role}", "name": NAMES[role],
        "provider": f"codex-{role}", "model": model,
        "modeId": mode_id, "thinkingOptionId": effort,
        "notes": NOTES[role] + " Choose model and reasoning from this role's provider choices according to task difficulty.",
    }


def provider(role: str, executable: Path, installed_script: Path, spec: dict) -> dict:
    options = ROLE_OPTIONS[role]
    models = []
    for model in dict.fromkeys(option[0] for option in options):
        levels = [option[1] for option in options if option[0] == model]
        models.append({"id": model, "label": model, "isDefault": model == options[0][0],
                       "thinkingOptions": [{"id": level, "label": level.capitalize(),
                                            "isDefault": level == levels[0]} for level in levels]})
    return {
        "extends": "codex", "label": NAMES[role],
        "description": NOTES[role],
        "command": [str(executable), str(installed_script), role],
        "params": {"sandbox_mode": spec["sandbox"], "approval_policy": spec["approval"]},
        "models": models,
        "paseoTools": {"enabled": role != "peer"},
    }


def planned_config(current: dict, executable: Path, installed_script: Path,
                   specs: dict[str, dict]) -> dict:
    result = json.loads(json.dumps(current))
    daemon = result.setdefault("daemon", {})
    daemon["agentProfiles"] = [profile(role, specs[role].get("mode_id", DEFAULT_MODE_ID)) for role in ROLES]
    mcp = daemon.setdefault("mcp", {})
    mcp["enabled"] = True
    mcp["injectIntoAgents"] = True
    providers = result.setdefault("agents", {}).setdefault("providers", {})
    for name in (*ALIASES, *(f"claude-{role}" for role in ROLES)):
        providers.pop(name, None)
    for role in ROLES:
        providers[f"codex-{role}"] = provider(role, executable, installed_script, specs[role])
    return result


def write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def backup_paths(paths: list[Path], home: Path) -> tuple[Path, dict[Path, Path | None]]:
    base = home / ".codex-room-backups"
    if redirected(base):
        fail(f"backup root is redirected: {base}")
    base.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = base / f"windows-{stamp}-{os.getpid()}"
    root.mkdir()
    record: dict[Path, Path | None] = {}
    for index, path in enumerate(paths):
        if redirected(path):
            fail(f"managed target is redirected: {path}")
        if path.exists():
            if not path.is_file():
                fail(f"managed target is not a file: {path}")
            saved = root / f"file-{index:02d}"
            shutil.copy2(path, saved)
            record[path] = saved
        else:
            record[path] = None
    (root / "manifest.json").write_text(json.dumps(
        {str(path): str(saved) if saved else None for path, saved in record.items()}, indent=2
    ), encoding="utf-8")
    return root, record


def restore(record: dict[Path, Path | None]) -> None:
    for path, saved in reversed(tuple(record.items())):
        if saved is None:
            if path.is_file() and not redirected(path):
                path.unlink()
        else:
            write_atomic(path, saved.read_bytes())


def model_instruction_links(runtime: Path, source: Path) -> dict[Path, bool]:
    links = {}
    for role in ROLES:
        link = runtime / role / "model-instructions.md"
        if redirected(link):
            fail(f"runtime model instructions are redirected: {link}")
        existed = link.exists()
        if existed and (not source.is_file() or not link.is_file() or not link.samefile(source)):
            fail(f"runtime model instructions differ from installed source: {link}")
        links[link] = existed
    return links


def restore_model_links(links: dict[Path, bool], source: Path) -> None:
    for link, existed in links.items():
        if link.exists():
            if redirected(link) or not link.is_file():
                fail(f"cannot restore unexpected runtime link: {link}")
            link.unlink()
        if existed:
            os.link(source, link)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="replace all existing Paseo agent profiles")
    parser.add_argument("--reload", action="store_true", help="reload live Paseo after apply")
    parser.add_argument("--source", choices=("pinned", "latest"), default="pinned",
                        help="pinned verified commit or latest upstream main commit")
    parser.add_argument("--accept-upstream-changes", action="store_true",
                        help="with --source latest --apply: accept reviewed upstream role or protocol changes")
    args = parser.parse_args()
    if args.reload and not args.apply:
        fail("--reload requires --apply")
    if os.name != "nt" or sys.version_info < (3, 12):
        fail("native Windows and Python 3.12 or newer are required")
    home = Path.home()
    canonical = home / ".codex"
    room = home / ".config" / "codex-room"
    config_path = home / ".paseo" / "config.json"
    runtime = home / ".codex-runtime"
    if not config_path.is_file() or not (canonical / "config.toml").is_file() or not (canonical / "auth.json").is_file():
        fail("Paseo config or authenticated Codex home is missing")
    for path in (config_path, room, runtime):
        preflight_path(path, home)
    for path in (SCRIPT_DIR / name for name in LOCAL_HELPERS):
        if not path.is_file():
            fail(f"source helper is missing: {path}")
    catalog = codex_catalog()
    commit = latest_commit() if args.source == "latest" else COMMIT
    assets = source_assets(commit, args.source == "pinned")
    upstream_assets = assets
    upstream_specs = role_specs(upstream_assets, catalog)
    policy, policy_digest = load_local_policy(SCRIPT_DIR / POLICY_FILE)
    assets, specs = apply_local_policy(upstream_assets, upstream_specs, policy)
    changed = upstream_changes(room / "source-manifest.json", upstream_assets)
    current = json.loads(config_path.read_text(encoding="utf-8-sig"))
    if not isinstance(current.get("daemon", {}).get("agentProfiles", []), list):
        fail("daemon.agentProfiles must be an array")
    installed_script = room / "codex-room-windows.py"
    desired = planned_config(current, Path(sys.executable), installed_script, specs)
    old_ids = [entry.get("id") for entry in current["daemon"].get("agentProfiles", [])]
    print(f"PASEO_HOST={config_path}")
    print(f"CURRENT_PROFILES={len(old_ids)} ids={','.join(str(x) for x in old_ids)}")
    print(f"TARGET_PROFILES={len(PROFILE_IDS)} ids={','.join(PROFILE_IDS)}")
    print("ROLE_CHOICES=" + ",".join(f"{role}:{model}/{effort}" for role in ROLES
                                      for model, effort in ROLE_OPTIONS[role]))
    print(f"CODEX_MODELS={len(catalog['models'])}; SOURCE_COMMIT={commit}; SOURCE_MODE={args.source}")
    print(f"RUNTIME_ROOT={runtime}")
    print("LOCAL_POLICY=" + (f"sha256:{policy_digest}" if policy_digest else "none"))
    for role in ROLES:
        before, after = upstream_specs[role], specs[role]
        print(f"EFFECTIVE role={role} sandbox={before['sandbox']}->{after['sandbox']} "
              f"approval={before['approval']}->{after['approval']} "
              f"paseo_mode={after.get('mode_id', DEFAULT_MODE_ID)}")
    if "heartbeat_cron" in specs["supervisor"]:
        print(f"EFFECTIVE heartbeat_cron={specs['supervisor']['heartbeat_cron']}")
    print(f"EFFECTIVE heartbeat_usage_report={specs['supervisor'].get('heartbeat_usage_report', False)}")
    print(f"EFFECTIVE heartbeat_stall_intervention={specs['supervisor'].get('heartbeat_stall_intervention', False)}")
    print("UPSTREAM_CHANGED=" + (",".join(changed) if changed else "none"))
    if args.source == "latest" and args.apply and changed and not args.accept_upstream_changes:
        fail("upstream role or protocol content differs from the installed source; "
             "review the changed files at SOURCE_COMMIT, then repeat with --accept-upstream-changes")
    if not args.apply:
        print("PLAN_ONLY: no host files changed")
        return
    manifest = {"commit": commit, "sha256": {name: hashlib.sha256(content).hexdigest()
                                           for name, content in upstream_assets.items()}, "roles": specs}
    if policy_digest:
        manifest["local_policy_sha256"] = policy_digest
    manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode("utf-8")
    source_model = room / "model-instructions.md"
    links = model_instruction_links(runtime, source_model)
    managed = [config_path]
    managed += [room / name for name in SOURCES]
    managed += [room / name for name in LOCAL_HELPERS]
    managed.append(room / "source-manifest.json")
    for role in ROLES:
        managed += [runtime / role / "config.toml", runtime / role / "model-catalog.no-native-agents.json"]
    for path in managed:
        preflight_path(path, home)
    files = {room / name: content for name, content in assets.items()}
    files.update({room / name: (SCRIPT_DIR / name).read_bytes() for name in LOCAL_HELPERS})
    files[room / "source-manifest.json"] = manifest_bytes
    if (current == desired and all(path.is_file() and path.read_bytes() == content
                                   for path, content in files.items())
            and all((runtime / role / "config.toml").is_file()
                    and (runtime / role / "model-catalog.no-native-agents.json").is_file()
                    and links[runtime / role / "model-instructions.md"] for role in ROLES)):
        print(f"UP_TO_DATE commit={commit}; no host files changed")
        return
    backup, record = backup_paths(managed, home)
    try:
        for destination, content in files.items():
            if not destination.is_file() or destination.read_bytes() != content:
                write_atomic(destination, content)
        if any(links.values()) and source_model.read_bytes() != (record[source_model].read_bytes() if record[source_model] else b""):
            for link, existed in links.items():
                if existed:
                    link.unlink()
        for role in ROLES:
            completed = subprocess.run([sys.executable, str(installed_script), "--sync-only", role],
                                       capture_output=True, text=True, encoding="utf-8", errors="replace")
            if completed.returncode:
                fail(f"runtime sync failed for {role}: {completed.stderr.strip()}")
        write_atomic(config_path, (json.dumps(desired, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        if args.reload:
            cli = paseo_cli()
            if not cli:
                fail("Paseo CLI not found; config saved but reload unavailable")
            completed = subprocess.run([str(cli), "reload"], capture_output=True, text=True, encoding="utf-8", errors="replace")
            if completed.returncode:
                fail(f"Paseo reload failed: {completed.stderr.strip()}")
        print(f"APPLY_OK backup={backup}")
    except BaseException:
        restore(record)
        restore_model_links(links, source_model)
        if args.reload:
            cli = paseo_cli()
            if cli:
                subprocess.run([str(cli), "reload"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        raise


if __name__ == "__main__":
    main()
