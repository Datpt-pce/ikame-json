import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const root = fileURLToPath(new URL('../', import.meta.url));
const shim = fileURLToPath(new URL('./codegraph/node_modules/@colbymchenry/codegraph/npm-shim.js', import.meta.url));
const args = process.argv.slice(2);
if (args[0] === 'serve') args.push('--path', root);
const child = spawn(process.execPath, [shim, ...args], {
  cwd: root, windowsHide: true, stdio: 'inherit',
  env: { ...process.env, DO_NOT_TRACK: '1', CODEGRAPH_NO_UPDATE_CHECK: '1', CODEGRAPH_NO_DOWNLOAD: '1' },
});
child.on('error', error => { console.error(error.message); process.exitCode = 1; });
child.on('exit', code => { process.exitCode = code ?? 1; });
