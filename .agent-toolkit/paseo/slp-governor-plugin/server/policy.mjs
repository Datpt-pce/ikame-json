import path from 'node:path';

export const TITLE = /^SLP\|([A-Za-z0-9._/-]+)\|([A-Za-z0-9._/-]+)\|([A-Za-z0-9._/-]+)\|([A-Za-z0-9._/-]+)\|(supervisor|lead|peer)\|([A-Za-z0-9._/-]+)$/;

export function parseTitle(title) {
  if (typeof title !== 'string') return null;
  const match = TITLE.exec(title);
  if (!match) return null;
  const [, story, slice, phase, candidate, role, dispatchId] = match;
  return { story, slice, phase, candidate, role, dispatchId };
}

export function validateConfig(raw) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw) || raw.version !== 1 ||
      !Array.isArray(raw.scopes)) throw new Error('SLP governor config must be version 1 with scopes');
  if (Object.keys(raw).some((key) => !['version', 'scopes'].includes(key)))
    throw new Error('SLP governor config has unknown keys');
  const scopes = raw.scopes.map((scope) => {
    if (!scope || typeof scope !== 'object' || Array.isArray(scope) ||
        Object.keys(scope).sort().join(',') !== 'contract,ledger,mode,python,reporter,root')
      throw new Error('SLP governor scope fields are invalid');
    for (const key of ['root', 'contract', 'ledger', 'python', 'reporter']) {
      if (typeof scope[key] !== 'string' || !path.win32.isAbsolute(scope[key]))
        throw new Error(`SLP governor ${key} must be an absolute Windows path`);
    }
    if (!['shadow', 'enforce'].includes(scope.mode))
      throw new Error('SLP governor mode must be shadow or enforce');
    return { ...scope };
  });
  return { version: 1, scopes };
}

export function inScope(root, cwd) {
  if (typeof cwd !== 'string' || !path.win32.isAbsolute(cwd)) return false;
  const relative = path.win32.relative(root.toLowerCase(), cwd.toLowerCase());
  return relative === '' || (relative !== '..' && !relative.startsWith('..\\') &&
                             !path.win32.isAbsolute(relative));
}

export function scopeFor(config, cwd) {
  const matches = config.scopes.filter((scope) => inScope(scope.root, cwd));
  if (matches.length > 1) throw new Error('SLP governor scopes overlap');
  return matches[0] ?? null;
}

export function createArgs(scope, title) {
  if (!parseTitle(title)) throw new Error('SLP dispatch title is required');
  return [scope.reporter, '--authorize-create', '--contract', scope.contract,
          '--ledger', scope.ledger, '--title', title, '--json'];
}

export function bindArgs(scope, dispatchId, agentId) {
  return [scope.reporter, '--bind', '--ledger', scope.ledger,
          '--dispatch-id', dispatchId, '--agent-id', agentId, '--json'];
}

export function closeArgs(scope, dispatchId) {
  return [scope.reporter, '--close', '--ledger', scope.ledger,
          '--dispatch-id', dispatchId, '--json'];
}
