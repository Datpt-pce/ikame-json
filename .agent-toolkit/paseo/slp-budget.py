#!/usr/bin/env python3
"""Read-only Paseo/Codex session usage report for SLP supervision.

The adapter intentionally emits only allowlisted identifiers and counters. Codex
JSONL is an implementation detail: unreadable, absent, ambiguous or regressed
counters are UNKNOWN, never silently treated as zero. No prompts are retained.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
import tomllib


COUNTERS = (
    'total_tokens', 'input_tokens', 'cached_input_tokens',
    'noncached_input_tokens', 'output_tokens', 'reasoning_output_tokens',
)
SOURCE_COUNTERS = tuple(name for name in COUNTERS if name != 'noncached_input_tokens')
SESSION_ID = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,127}$')
AGENT_ID = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,127}$')
SHA256 = re.compile(r'^[0-9a-f]{64}$')
DISPATCH_TITLE = re.compile(
    r'^SLP\|(?P<story>[A-Za-z0-9._/-]+)\|(?P<slice>[A-Za-z0-9._/-]+)\|'
    r'(?P<phase>[A-Za-z0-9._/-]+)\|(?P<candidate>[A-Za-z0-9._/-]+)\|'
    r'(?P<role>supervisor|lead|peer)\|(?P<dispatch_id>[A-Za-z0-9._/-]+)$'
)
CONTRACT_KEYS = {'version', 'story', 'slice', 'mode', 'preset', 'max_total_tokens',
                 'validation_reserve_tokens', 'thresholds'}
PRESETS = {'economy', 'balanced', 'high-assurance'}
ROLES = {'writer', 'auditor', 'validation', 'lead', 'supervisor'}


def unknown(reason: str) -> dict:
    return {'status': 'unknown', 'reason': reason}


def safe_id(value: object) -> str | None:
    return value if isinstance(value, str) and AGENT_ID.fullmatch(value) else None


def safe_tag(value: object) -> str:
    if isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]{0,127}', value):
        return value
    return 'UNKNOWN'


def load_contract(path: Path) -> dict:
    """Load an explicit, strict per-slice budget contract; no implicit defaults."""
    with path.open('rb') as stream:
        data = tomllib.load(stream)
    if not isinstance(data, dict):
        raise ValueError('contract must be a TOML table')
    extra = set(data) - CONTRACT_KEYS
    missing = CONTRACT_KEYS - set(data)
    if extra or missing:
        raise ValueError(f'contract has unsupported or missing keys: {sorted(extra | missing)}')
    if type(data['version']) is not int or data['version'] != 1:
        raise ValueError('contract version must be 1')
    for name in ('story', 'slice'):
        if safe_tag(data[name]) != data[name]:
            raise ValueError(f'contract {name} must be a stable slug')
    if data['mode'] not in {'shadow', 'enforce'}:
        raise ValueError('contract mode must be shadow or enforce')
    if data['preset'] not in PRESETS:
        raise ValueError('unknown budget preset')
    for name in ('max_total_tokens', 'validation_reserve_tokens'):
        if type(data[name]) is not int or data[name] < 0:
            raise ValueError(f'contract {name} must be a nonnegative integer')
    if data['max_total_tokens'] <= 0 or data['validation_reserve_tokens'] >= data['max_total_tokens']:
        raise ValueError('contract reserve must be smaller than a positive cap')
    thresholds = data['thresholds']
    if not isinstance(thresholds, dict) or set(thresholds) != {'warn_percent', 'restricted_percent'}:
        raise ValueError('thresholds must have exactly warn_percent and restricted_percent')
    warn, restricted = thresholds['warn_percent'], thresholds['restricted_percent']
    if type(warn) is not int or type(restricted) is not int or not 0 < warn < restricted < 100:
        raise ValueError('thresholds must satisfy 0 < warn < restricted < 100')
    return data


def evaluate(contract: dict, report: dict, *, role: str, evidence: dict | None = None) -> dict:
    """Pure admission decision. Unknown usage is a blocker only in enforcement."""
    if role not in ROLES:
        raise ValueError('unknown dispatch role')
    evidence = evidence or {}
    allowed_evidence = {'rejects_same_class', 'previous_candidates', 'new_executable_signals',
                        'candidate_hash', 'delta_hash'}
    if set(evidence) - allowed_evidence:
        raise ValueError('unsupported evidence fields')
    for key in ('rejects_same_class', 'previous_candidates', 'new_executable_signals'):
        value = evidence.get(key, 0)
        if type(value) is not int or value < 0:
            raise ValueError(f'{key} must be a nonnegative integer')
    known = report['known_total_tokens']
    if type(known) is not int or known < 0:
        raise ValueError('known_total_tokens must be nonnegative')
    remaining = max(0, contract['max_total_tokens'] - known)
    fraction = known * 100 / contract['max_total_tokens']
    state = ('PAUSED' if fraction >= 100 else
             'RESTRICTED' if fraction >= contract['thresholds']['restricted_percent'] else
             'WARN' if fraction >= contract['thresholds']['warn_percent'] else 'OPEN')
    reasons = []
    if report.get('unknown_sessions', 0) or report.get('unattributed_sessions', 0):
        reasons.append('UNKNOWN_USAGE')
    if fraction >= 100:
        reasons.append('TOKEN_CAP_EXCEEDED')
    elif state == 'RESTRICTED' and role in {'writer', 'auditor'}:
        reasons.append('RESTRICTED_TO_VALIDATION')
    if role == 'writer' and remaining <= contract['validation_reserve_tokens']:
        reasons.append('VALIDATION_RESERVE')
    rejects = evidence.get('rejects_same_class', 0)
    if rejects >= 3:
        reasons.append('HUMAN_DECISION')
    elif rejects >= 2:
        reasons.append('REOPEN_DESIGN')
    if (role in {'writer', 'auditor'} and evidence.get('previous_candidates', 0) > 0
            and evidence.get('new_executable_signals', 0) == 0):
        reasons.append('NO_NEW_SIGNAL')
    if role == 'auditor' and (not isinstance(evidence.get('candidate_hash'), str)
                              or SHA256.fullmatch(evidence['candidate_hash']) is None
                              or not isinstance(evidence.get('delta_hash'), str)
                              or SHA256.fullmatch(evidence['delta_hash']) is None):
        reasons.append('AUDIT_CANDIDATE_UNBOUND')
    # Enforce mode is a future host opt-in. Shadow always returns the would-block reasons.
    decision = 'allow_shadow' if contract['mode'] == 'shadow' else ('deny' if reasons else 'allow')
    return {
        'mode': contract['mode'], 'state': state, 'decision': decision,
        'would_deny': bool(reasons), 'reason_codes': reasons,
        'known_total_tokens': known, 'remaining_tokens': remaining,
        'validation_reserve_tokens': contract['validation_reserve_tokens'],
    }


class BudgetLedger:
    """Toolkit-owned SQLite dispatch ledger; events never contain raw agent data."""

    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection:
            connection.executescript('''
                CREATE TABLE IF NOT EXISTS dispatches (
                    dispatch_id TEXT PRIMARY KEY,
                    story TEXT NOT NULL,
                    slice TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    candidate TEXT NOT NULL,
                    role TEXT NOT NULL,
                    agent_id TEXT UNIQUE,
                    status TEXT NOT NULL,
                    reserved_tokens INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    occurred_at TEXT NOT NULL,
                    dispatch_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    receipt_json TEXT NOT NULL
                );
            ''')

    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _event(self, connection, dispatch_id: str, kind: str, receipt: dict) -> None:
        connection.execute('INSERT INTO events(occurred_at, dispatch_id, kind, receipt_json) VALUES (?, ?, ?, ?)',
                           (self._now(), dispatch_id, kind, json.dumps(receipt, sort_keys=True)))

    def pending_tokens(self, story: str, slice_id: str) -> int:
        with closing(self._connect()) as connection:
            return connection.execute('''
                SELECT COALESCE(SUM(reserved_tokens), 0) FROM dispatches
                WHERE story = ? AND slice = ? AND status IN ('reserved', 'creating', 'bound')
            ''', (story, slice_id)).fetchone()[0]

    def dispatches(self, story: str, slice_id: str) -> list[dict]:
        with closing(self._connect()) as connection:
            rows = connection.execute('''
                SELECT dispatch_id, story, slice, phase, candidate, role, agent_id, status,
                       reserved_tokens, created_at, updated_at FROM dispatches
                WHERE story = ? AND slice = ? ORDER BY created_at, dispatch_id
            ''', (story, slice_id)).fetchall()
        return [dict(row) for row in rows]

    def events(self) -> list[dict]:
        with closing(self._connect()) as connection:
            rows = connection.execute('SELECT event_id, dispatch_id, kind, receipt_json FROM events ORDER BY event_id').fetchall()
        return [{'event_id': row['event_id'], 'dispatch_id': row['dispatch_id'],
                 'kind': row['kind'], 'receipt': json.loads(row['receipt_json'])} for row in rows]

    def admit(self, contract: dict, report: dict, fields: dict, *, work_role: str,
              requested_tokens: int, evidence: dict | None = None) -> dict:
        expected = {'dispatch_id', 'story', 'slice', 'phase', 'candidate', 'role'}
        if set(fields) != expected or any(safe_tag(value) != value for value in fields.values()):
            raise ValueError('dispatch fields must be stable non-secret slugs')
        if fields['story'] != contract['story'] or fields['slice'] != contract['slice']:
            raise ValueError('dispatch story/slice differs from contract')
        if fields['role'] not in {'supervisor', 'lead', 'peer'}:
            raise ValueError('dispatch role must be Supervisor, Lead, or Peer')
        if type(requested_tokens) is not int or requested_tokens <= 0:
            raise ValueError('requested_tokens must be positive')
        dispatch_id = fields['dispatch_id']
        with closing(self._connect()) as connection:
            connection.execute('BEGIN IMMEDIATE')
            if connection.execute('SELECT 1 FROM dispatches WHERE dispatch_id = ?', (dispatch_id,)).fetchone():
                raise ValueError('dispatch already exists')
            pending = connection.execute('''
                SELECT COALESCE(SUM(reserved_tokens), 0) FROM dispatches
                WHERE story = ? AND slice = ? AND status IN ('reserved', 'creating', 'bound')
            ''', (contract['story'], contract['slice'])).fetchone()[0]
            virtual = {**report, 'known_total_tokens': report['known_total_tokens'] + pending}
            decision = evaluate(contract, virtual, role=work_role, evidence=evidence)
            ceiling = contract['max_total_tokens']
            if work_role != 'validation':
                ceiling -= contract['validation_reserve_tokens']
            if virtual['known_total_tokens'] + requested_tokens > ceiling:
                decision['reason_codes'].append('DISPATCH_RESERVE_EXCEEDS_CAP')
                decision['would_deny'] = True
                if contract['mode'] == 'enforce':
                    decision['decision'] = 'deny'
            receipt = {**decision, 'dispatch_id': dispatch_id,
                       'requested_tokens': requested_tokens, 'pending_before': pending}
            if receipt['decision'] != 'deny':
                now = self._now()
                connection.execute('''
                    INSERT INTO dispatches(dispatch_id, story, slice, phase, candidate, role,
                                           agent_id, status, reserved_tokens, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, NULL, 'reserved', ?, ?, ?)
                ''', (dispatch_id, fields['story'], fields['slice'], fields['phase'],
                      fields['candidate'], fields['role'], requested_tokens, now, now))
                self._event(connection, dispatch_id, 'admitted', receipt)
            else:
                self._event(connection, dispatch_id, 'denied', receipt)
            connection.commit()
            return receipt

    def authorize_create(self, title: str, contract: dict | None = None) -> dict:
        """Consume one exact pre-reserved permit in Paseo's agent.create before hook."""
        match = DISPATCH_TITLE.fullmatch(title)
        if match is None:
            raise ValueError('SLP title does not match dispatch format')
        fields = match.groupdict()
        dispatch_id = fields.pop('dispatch_id')
        with closing(self._connect()) as connection:
            connection.execute('BEGIN IMMEDIATE')
            row = connection.execute('''
                SELECT story, slice, phase, candidate, role, status FROM dispatches
                WHERE dispatch_id = ?
            ''', (dispatch_id,)).fetchone()
            if row is None or any(row[name] != value for name, value in fields.items()):
                raise ValueError('SLP title does not match reserved dispatch')
            if contract is not None and (contract['mode'] != 'enforce'
                                         or row['story'] != contract['story']
                                         or row['slice'] != contract['slice']):
                raise ValueError('dispatch does not match an enforce contract')
            if row['status'] != 'reserved':
                raise ValueError('dispatch is not reserved')
            connection.execute("UPDATE dispatches SET status = 'creating', updated_at = ? WHERE dispatch_id = ?",
                               (self._now(), dispatch_id))
            receipt = {'dispatch_id': dispatch_id, 'decision': 'allow', 'status': 'creating'}
            self._event(connection, dispatch_id, 'create_authorized', receipt)
            connection.commit()
            return receipt

    def bind(self, dispatch_id: str, agent_id: str) -> None:
        if safe_id(agent_id) != agent_id:
            raise ValueError('agent_id must be a stable ID')
        with closing(self._connect()) as connection:
            connection.execute('BEGIN IMMEDIATE')
            row = connection.execute('SELECT status, agent_id FROM dispatches WHERE dispatch_id = ?',
                                     (dispatch_id,)).fetchone()
            if row is None or row['status'] not in {'reserved', 'creating'} or row['agent_id'] is not None:
                raise ValueError('dispatch is not available for bind')
            connection.execute("UPDATE dispatches SET agent_id = ?, status = 'bound', updated_at = ? WHERE dispatch_id = ?",
                               (agent_id, self._now(), dispatch_id))
            self._event(connection, dispatch_id, 'bound', {'agent_id': agent_id})
            connection.commit()

    def close(self, dispatch_id: str) -> None:
        with closing(self._connect()) as connection:
            connection.execute('BEGIN IMMEDIATE')
            row = connection.execute('SELECT status FROM dispatches WHERE dispatch_id = ?',
                                     (dispatch_id,)).fetchone()
            if row is None or row['status'] not in {'reserved', 'creating', 'bound'}:
                raise ValueError('dispatch is not open')
            connection.execute("UPDATE dispatches SET status = 'closed', updated_at = ? WHERE dispatch_id = ?",
                               (self._now(), dispatch_id))
            self._event(connection, dispatch_id, 'closed', {})
            connection.commit()


def extract_agent(raw: dict) -> dict:
    """Strip raw Paseo metadata to non-secret SLP identity fields."""
    labels = raw.get('labels') if isinstance(raw.get('labels'), dict) else {}
    runtime = raw.get('runtimeInfo') if isinstance(raw.get('runtimeInfo'), dict) else {}
    title = raw.get('title')
    title_fields = DISPATCH_TITLE.fullmatch(title).groupdict() if isinstance(title, str) and DISPATCH_TITLE.fullmatch(title) else {}

    def identity(name: str, *label_names: str) -> str:
        from_title = safe_tag(title_fields.get(name))
        from_label = next((safe_tag(labels[key]) for key in label_names if labels.get(key)), 'UNKNOWN')
        if from_title != 'UNKNOWN' and from_label != 'UNKNOWN' and from_title != from_label:
            return 'UNKNOWN'
        return from_title if from_title != 'UNKNOWN' else from_label

    return {
        'agent_id': safe_id(raw.get('id')),
        'parent_agent_id': safe_id(labels.get('paseo.parent-agent-id')),
        'session_id': safe_id(runtime.get('sessionId')),
        'role': identity('role', 'slp.role'),
        'story': identity('story', 'slp.story', 'slp.packet'),
        'slice': identity('slice', 'slp.slice', 'slp.scope'),
        'phase': identity('phase', 'slp.phase'),
        'candidate': identity('candidate', 'slp.candidate'),
        'dispatch_id': identity('dispatch_id', 'slp.dispatch-id'),
    }


def _valid_counters(sample: object) -> dict | None:
    if not isinstance(sample, dict):
        return None
    values = {name: sample.get(name) for name in SOURCE_COUNTERS}
    if any(type(value) is not int or value < 0 for value in values.values()):
        return None
    if values['cached_input_tokens'] > values['input_tokens']:
        return None
    if values['reasoning_output_tokens'] > values['output_tokens']:
        return None
    if values['input_tokens'] + values['output_tokens'] != values['total_tokens']:
        return None
    values['noncached_input_tokens'] = values['input_tokens'] - values['cached_input_tokens']
    return values


def read_cumulative_usage(path: Path) -> dict:
    """Use the last monotonic cumulative token_count event, not sum of events."""
    previous: dict | None = None
    try:
        with path.open('r', encoding='utf-8') as stream:
            for line in stream:
                if 'token_count' not in line:
                    continue
                record = json.loads(line)
                payload = record.get('payload') if isinstance(record, dict) else None
                if not isinstance(payload, dict) or payload.get('type') != 'token_count':
                    continue
                info = payload.get('info')
                if not isinstance(info, dict) or info.get('total_token_usage') is None:
                    continue
                sample = _valid_counters(info['total_token_usage'])
                if sample is None:
                    return unknown('invalid_counter')
                if previous is not None and any(sample[name] < previous[name] for name in COUNTERS):
                    return unknown('counter_regression')
                previous = sample
    except (OSError, UnicodeError, json.JSONDecodeError):
        return unknown('session_log_unreadable')
    return {'status': 'measured', **previous} if previous is not None else unknown('counter_missing')


def _root_id(agent_id: str, parents: dict[str, str | None]) -> str:
    current = agent_id
    seen = set()
    while current in parents and parents[current] and current not in seen:
        seen.add(current)
        current = parents[current]
    return current if current not in seen else 'UNKNOWN'


def _summary(rows: list[dict]) -> dict:
    known = {name: 0 for name in COUNTERS}
    missing = defaultdict(int)
    for row in rows:
        usage = row['usage']
        if usage['status'] == 'measured':
            for name in COUNTERS:
                known[name] += usage[name]
        else:
            missing[usage['reason']] += 1
    return {
        'status': 'partial' if missing else 'measured',
        'known_total_tokens': known['total_tokens'],
        'known_usage': known,
        'measured_sessions': len(rows) - sum(missing.values()),
        'unknown_sessions': sum(missing.values()),
        'unknown_reasons': dict(sorted(missing.items())),
        'unattributed_sessions': sum(1 for row in rows if any(
            row.get(name, 'UNKNOWN') == 'UNKNOWN'
            for name in ('role', 'story', 'slice', 'phase', 'candidate', 'dispatch_id'))),
    }


def summarize(rows: list[dict]) -> dict:
    """Aggregate known lower bounds while preserving every unknown session."""
    report = _summary(rows)
    roots = defaultdict(list)
    for row in rows:
        roots[row['root_agent_id']].append(row)
    report['roots'] = [
        {'root_agent_id': root_id, **_summary(members), 'sessions': members}
        for root_id, members in sorted(roots.items())
    ]
    return report


def _session_index(runtime_root: Path) -> dict[str, list[Path]]:
    index = defaultdict(list)
    if not runtime_root.is_dir():
        return index
    for path in runtime_root.glob('*/**/rollout-*.jsonl'):
        session_id = path.stem.rsplit('-', 5)[-5:]
        if len(session_id) == 5:
            value = '-'.join(session_id)
            if SESSION_ID.fullmatch(value):
                index[value].append(path)
    return index


def collect(home: Path, *, root_agent: str | None = None,
            story: str | None = None, slice_id: str | None = None,
            ledger: BudgetLedger | None = None) -> dict:
    metadata_root = home / '.paseo' / 'agents'
    agents = {}
    if metadata_root.is_dir():
        for path in metadata_root.glob('*/*.json'):
            try:
                raw = json.loads(path.read_text(encoding='utf-8'))
            except (OSError, UnicodeError, json.JSONDecodeError):
                continue
            if not isinstance(raw, dict):
                continue
            row = extract_agent(raw)
            if row['agent_id']:
                agents[row['agent_id']] = row
    parents = {key: row['parent_agent_id'] for key, row in agents.items()}
    session_counts = defaultdict(int)
    for row in agents.values():
        if row['session_id']:
            session_counts[row['session_id']] += 1
    index = _session_index(home / '.codex-runtime')
    rows = []
    for agent_id, row in sorted(agents.items()):
        root_id = _root_id(agent_id, parents)
        if root_agent and root_id != root_agent:
            continue
        if story and row['story'] != story:
            continue
        if slice_id and row['slice'] != slice_id:
            continue
        session_id = row['session_id']
        if not session_id:
            usage = unknown('session_id_missing')
        elif session_counts[session_id] > 1:
            usage = unknown('session_shared')
        elif len(index[session_id]) == 0:
            usage = unknown('session_log_missing')
        elif len(index[session_id]) != 1:
            usage = unknown('session_log_ambiguous')
        else:
            usage = read_cumulative_usage(index[session_id][0])
        rows.append({**row, 'root_agent_id': root_id, 'usage': usage})
    if ledger is not None:
        if not story or not slice_id:
            raise ValueError('ledger comparison requires exact story and slice')
        found = {row['agent_id'] for row in rows}
        for dispatch in ledger.dispatches(story, slice_id):
            agent_id = dispatch['agent_id']
            if agent_id in found:
                continue
            if root_agent:
                # Without a bound parent, this dispatch cannot be placed in a
                # single Supervisor tree. It must remain visible at story level.
                continue
            rows.append({
                'agent_id': agent_id or 'UNKNOWN', 'parent_agent_id': None,
                'root_agent_id': agent_id or dispatch['dispatch_id'],
                'session_id': None, 'role': dispatch['role'], 'story': story,
                'slice': slice_id, 'phase': dispatch['phase'],
                'candidate': dispatch['candidate'], 'dispatch_id': dispatch['dispatch_id'],
                'usage': unknown('dispatch_not_bound' if not agent_id else 'bound_agent_missing'),
            })
    return summarize(rows)


def format_text(report: dict, *, compact: bool = False) -> str:
    def breakdown(known: dict) -> str:
        return (f"input={known['input_tokens']:,} cached={known['cached_input_tokens']:,} "
                f"noncached={known['noncached_input_tokens']:,} output={known['output_tokens']:,} "
                f"reasoning={known['reasoning_output_tokens']:,}")

    lines = [
        f"SLP usage: {report['known_total_tokens']:,} known tokens; "
        f"{report['measured_sessions']} measured, {report['unknown_sessions']} UNKNOWN sessions",
        breakdown(report['known_usage']),
    ]
    if report['unknown_reasons']:
        lines.append('UNKNOWN reasons: ' + ', '.join(
            f'{key}={value}' for key, value in report['unknown_reasons'].items()))
    if report['unattributed_sessions']:
        lines.append(f"Attribution incomplete: {report['unattributed_sessions']} sessions lack SLP identity fields")
    for root in report['roots']:
        lines.append(f"root {root['root_agent_id']}: {root['known_total_tokens']:,} known tokens; "
                     f"{root['unknown_sessions']} UNKNOWN")
        roles = defaultdict(list)
        for row in root['sessions']:
            roles[row['role']].append(row)
        for role, members in sorted(roles.items()):
            role_summary = _summary(members)
            lines.append(f"  role {role}: {role_summary['known_total_tokens']:,} known tokens; "
                         f"{role_summary['unknown_sessions']} UNKNOWN; "
                         + breakdown(role_summary['known_usage']))
        if not compact:
            for row in root['sessions']:
                usage = row['usage']
                count = f"{usage['total_tokens']:,}" if usage['status'] == 'measured' else f"UNKNOWN({usage['reason']})"
                detail = (' ' + breakdown(usage)) if usage['status'] == 'measured' else ''
                lines.append(f"    {row['role']} {row['agent_id']} story={row['story']} "
                             f"slice={row['slice']} phase={row['phase']} candidate={row['candidate']} "
                             f"session={row['session_id'] or 'UNKNOWN'} total={count}{detail}")
    return '\n'.join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, default=Path.home(), help='host home containing .paseo and .codex-runtime')
    parser.add_argument('--root-agent', help='show one Supervisor/Lead agent tree')
    parser.add_argument('--story', help='show only agents labeled with this SLP story')
    parser.add_argument('--slice', help='show only agents labeled with this SLP slice')
    parser.add_argument('--contract', type=Path, help='evaluate a per-slice budget contract')
    parser.add_argument('--role', choices=sorted(ROLES), help='dispatch role for budget evaluation')
    parser.add_argument('--evidence-file', type=Path, help='JSON evidence for budget circuit breakers')
    parser.add_argument('--ledger', type=Path, help='toolkit-owned SQLite ledger path')
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--admit', action='store_true', help='reserve one bounded SLP dispatch')
    action.add_argument('--authorize-create', action='store_true', help='consume a pre-reserved create permit')
    action.add_argument('--bind', action='store_true', help='bind created Paseo agent ID to dispatch')
    action.add_argument('--close', action='store_true', help='close dispatch and release its reserve')
    action.add_argument('--events', action='store_true', help='print append-only ledger events')
    parser.add_argument('--dispatch-id')
    parser.add_argument('--phase')
    parser.add_argument('--candidate')
    parser.add_argument('--agent-role', choices=('supervisor', 'lead', 'peer'))
    parser.add_argument('--requested-tokens', type=int)
    parser.add_argument('--title', help='structured SLP create title')
    parser.add_argument('--agent-id', help='new Paseo agent ID for --bind')
    parser.add_argument('--json', action='store_true', help='machine-readable allowlisted counters and identity')
    parser.add_argument('--compact', action='store_true', help='omit per-session detail for low-cost heartbeats')
    args = parser.parse_args()
    if args.root_agent is not None and safe_id(args.root_agent) != args.root_agent:
        parser.error('--root-agent must be a nonempty stable agent ID')
    ledger_path = args.ledger or args.home / '.config/codex-room/slp-budget.sqlite'
    if args.ledger and not args.admit and not ledger_path.is_file():
        parser.error('ledger file is missing; no state was created')
    if args.authorize_create or args.bind or args.close or args.events:
        if not args.ledger:
            parser.error('ledger action requires --ledger')
        ledger = BudgetLedger(ledger_path)
        if args.authorize_create:
            if not args.title or not args.contract:
                parser.error('--authorize-create requires --title and --contract')
            result = ledger.authorize_create(args.title, load_contract(args.contract))
        elif args.bind:
            if not args.dispatch_id or not args.agent_id:
                parser.error('--bind requires --dispatch-id and --agent-id')
            ledger.bind(args.dispatch_id, args.agent_id)
            result = {'dispatch_id': args.dispatch_id, 'decision': 'bound'}
        elif args.close:
            if not args.dispatch_id:
                parser.error('--close requires --dispatch-id')
            ledger.close(args.dispatch_id)
            result = {'dispatch_id': args.dispatch_id, 'decision': 'closed'}
        else:
            result = ledger.events()
        print(json.dumps(result, sort_keys=True) if args.json else result)
        return
    if args.contract:
        if not args.role:
            parser.error('--contract requires --role')
        contract = load_contract(args.contract)
        if args.story and args.story != contract['story']:
            parser.error('--story conflicts with contract story')
        if args.slice and args.slice != contract['slice']:
            parser.error('--slice conflicts with contract slice')
        evidence = None
        if args.evidence_file:
            evidence = json.loads(args.evidence_file.read_text(encoding='utf-8'))
            if not isinstance(evidence, dict):
                parser.error('--evidence-file must contain a JSON object')
        if contract['mode'] == 'enforce' and not args.ledger:
            parser.error('enforce contract requires --ledger')
        ledger = BudgetLedger(ledger_path) if args.ledger else None
        report = collect(args.home, story=contract['story'], slice_id=contract['slice'], ledger=ledger)
        if args.admit:
            if not all((args.dispatch_id, args.phase, args.candidate, args.agent_role,
                        args.requested_tokens, args.ledger)):
                parser.error('--admit requires --ledger, --dispatch-id, --phase, --candidate, '
                             '--agent-role and --requested-tokens')
            fields = {'dispatch_id': args.dispatch_id, 'story': contract['story'],
                      'slice': contract['slice'], 'phase': args.phase,
                      'candidate': args.candidate, 'role': args.agent_role}
            decision = ledger.admit(contract, report, fields, work_role=args.role,
                                    requested_tokens=args.requested_tokens, evidence=evidence)
            print(json.dumps(decision, sort_keys=True) if args.json else decision)
            return
        decision = evaluate(contract, report, role=args.role, evidence=evidence)
        if args.json:
            print(json.dumps(decision, sort_keys=True))
        else:
            print(f"BUDGET {decision['decision']} state={decision['state']} "
                  f"known={decision['known_total_tokens']:,} remaining={decision['remaining_tokens']:,} "
                  f"reasons={','.join(decision['reason_codes']) or 'none'}")
            print(format_text(report, compact=args.compact))
        return
    if args.role or args.evidence_file or args.admit:
        parser.error('--role, --evidence-file and --admit require --contract')
    if args.ledger and not (args.story and args.slice):
        parser.error('--ledger report requires --story and --slice')
    ledger = BudgetLedger(ledger_path) if args.ledger else None
    report = collect(args.home, root_agent=args.root_agent, story=args.story,
                     slice_id=args.slice, ledger=ledger)
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else format_text(report, compact=args.compact))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, sqlite3.Error, tomllib.TOMLDecodeError, json.JSONDecodeError) as error:
        raise SystemExit(f'slp-budget: {error}') from None
