import assert from 'node:assert/strict';
import test from 'node:test';
import { createArgs, inScope, parseTitle, scopeFor, validateConfig } from './policy.mjs';

const raw = { version: 1, scopes: [{
  root: 'D:\\work\\elp', contract: 'D:\\work\\elp\\slp-budget.toml',
  ledger: 'C:\\Users\\test\\slp-budget.sqlite', mode: 'enforce',
  python: 'C:\\Python\\python.exe', reporter: 'C:\\room\\slp-budget.py',
}] };

test('exact Windows path scope has boundary and detects overlap', () => {
  const config = validateConfig(raw);
  assert.equal(scopeFor(config, 'D:\\work\\elp\\src')?.mode, 'enforce');
  assert.equal(inScope('D:\\work\\elp', 'D:\\work\\elp-old'), false);
  assert.equal(inScope('D:\\work\\elp', 'E:\\work\\elp'), false);
  assert.throws(() => scopeFor({ scopes: [config.scopes[0], config.scopes[0]] }, 'D:\\work\\elp'), /overlap/);
});

test('only structured dispatch title can consume a permit', () => {
  const scope = validateConfig(raw).scopes[0];
  const title = 'SLP|PSW-002|core|build|c1|peer|dispatch-1';
  assert.equal(parseTitle(title)?.dispatchId, 'dispatch-1');
  assert.equal(parseTitle('ordinary agent'), null);
  assert.deepEqual(createArgs(scope, title).slice(0, 3),
                   ['C:\\room\\slp-budget.py', '--authorize-create', '--contract']);
  assert.throws(() => createArgs(scope, 'ordinary agent'), /required/);
});

test('untrusted config paths and unknown fields fail closed', () => {
  assert.throws(() => validateConfig({ ...raw, extra: 1 }), /unknown keys/);
  assert.throws(() => validateConfig({ version: 1, scopes: [{ ...raw.scopes[0], python: 'python' }] }), /absolute/);
});
