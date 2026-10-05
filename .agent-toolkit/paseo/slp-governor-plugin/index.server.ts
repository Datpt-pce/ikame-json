import type { PluginServerContext } from '@getpaseo/plugin/server';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { existsSync, readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import path from 'node:path';
import { bindArgs, closeArgs, createArgs, parseTitle, scopeFor, validateConfig } from './server/policy.mjs';

const execFileAsync = promisify(execFile);
const configPath = path.join(homedir(), '.config', 'codex-room', 'slp-governor.json');

function configuredScope(cwd: string) {
  if (!existsSync(configPath)) return null;
  const config = validateConfig(JSON.parse(readFileSync(configPath, 'utf8')));
  return scopeFor(config, cwd);
}

async function runBudget(python: string, args: string[], signal?: AbortSignal) {
  const { stdout } = await execFileAsync(python, args, {
    windowsHide: true,
    timeout: 25_000,
    maxBuffer: 128 * 1024,
    signal,
  });
  return JSON.parse(stdout);
}

export default function contribute(server: PluginServerContext) {
  server.before('agent.create', async ({ request }, { signal }) => {
    const scope = configuredScope(request.config.cwd);
    if (!scope || scope.mode === 'shadow' || request.config.provider === 'codex-supervisor')
      return request;
    const title = request.config.title;
    const identity = parseTitle(title);
    if (!identity || identity.role === 'supervisor')
      throw new Error('SLP_GOVERNOR_DISPATCH_TITLE_REQUIRED');
    if ((request.config.provider === 'codex-peer' && identity.role !== 'peer') ||
        (request.config.provider === 'codex-lead' && identity.role !== 'lead'))
      throw new Error('SLP_GOVERNOR_ROLE_MISMATCH');
    try {
      const receipt = await runBudget(scope.python, createArgs(scope, title), signal);
      if (receipt.decision !== 'allow' || receipt.status !== 'creating')
        throw new Error('unexpected admission receipt');
    } catch {
      // Never echo command stderr; it can contain host paths or private data.
      throw new Error('SLP_GOVERNOR_ADMISSION_DENIED');
    }
    return request;
  });

  server.on('agent.created', async (event, { signal }) => {
    const scope = configuredScope(event.agent.cwd);
    const identity = parseTitle(event.agent.title);
    if (!scope || scope.mode !== 'enforce' || !identity) return;
    try {
      await runBudget(scope.python, bindArgs(scope, identity.dispatchId, event.agent.id), signal);
    } catch {
      console.error('SLP_GOVERNOR_BIND_FAILED', event.agent.id);
    }
  });

  server.on('agent.archived', async (event, { signal }) => {
    const scope = configuredScope(event.agent.cwd);
    const identity = parseTitle(event.agent.title);
    if (!scope || scope.mode !== 'enforce' || !identity) return;
    try {
      await runBudget(scope.python, closeArgs(scope, identity.dispatchId), signal);
    } catch {
      console.error('SLP_GOVERNOR_CLOSE_FAILED', event.agent.id);
    }
  });
  return () => {};
}
