import { readFile, writeFile } from "node:fs/promises";

const [port, jsonPath, screenshotPath] = process.argv.slice(2);
if (!port || !jsonPath || !screenshotPath) {
  throw new Error("Usage: node test-lottiefiles-playground.mjs <port> <json> <screenshot>");
}

const targets = await fetch(`http://127.0.0.1:${port}/json/list`).then((response) => response.json());
const target = targets.find((candidate) =>
  candidate.url.startsWith("https://lottiefiles.github.io/lottie-docs/playground/json_editor/"),
);
if (!target?.webSocketDebuggerUrl) throw new Error("LottieFiles Playground tab was not found.");

const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
});

let nextId = 1;
const pending = new Map();
const browserErrors = [];
socket.addEventListener("message", (event) => {
  const message = JSON.parse(event.data);
  if (message.id && pending.has(message.id)) {
    const { resolve, reject } = pending.get(message.id);
    pending.delete(message.id);
    if (message.error) reject(new Error(message.error.message));
    else resolve(message.result);
  }
  if (message.method === "Runtime.exceptionThrown") {
    browserErrors.push(message.params.exceptionDetails.text);
  }
  if (message.method === "Log.entryAdded" && message.params.entry.level === "error") {
    browserErrors.push(message.params.entry.text);
  }
});

function command(method, params = {}) {
  const id = nextId;
  nextId += 1;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
  });
}

async function evaluate(expression) {
  const result = await command("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
  });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
  return result.result.value;
}

async function waitFor(expression, timeoutMs = 15000, optional = false) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await evaluate(expression)) return true;
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  if (optional) return false;
  throw new Error(`Timed out waiting for: ${expression}`);
}

await command("Runtime.enable");
await command("Log.enable");
await command("Page.enable");
await waitFor(
  `typeof lottie_string_input === "function" && typeof editor !== "undefined" && editor.schema != null`,
);

const jsonText = await readFile(jsonPath, "utf8");
await evaluate(`lottie_string_input(${JSON.stringify(jsonText)}, false); true`);
await waitFor(`lottie_player?.lottie?.layers?.length > 0 && lottie_player?.anim != null`);
const validationCompleted = await waitFor(
  `editor.completions.validation_result != null`,
  45000,
  true,
);
await evaluate(`lottie_player.pause(); lottie_player.go_to_frame(lottie_player.lottie.op - 1); true`);
await new Promise((resolve) => setTimeout(resolve, 500));

const status = await evaluate(`({
  lottieLoaded: Boolean(lottie_player?.lottie),
  animationLoaded: Boolean(lottie_player?.anim),
  width: lottie_player?.lottie?.w,
  height: lottie_player?.lottie?.h,
  frameRate: lottie_player?.lottie?.fr,
  finalFrame: Math.round(lottie_player?.anim?.currentFrame ?? -1),
  layers: lottie_player?.lottie?.layers?.length,
  assets: lottie_player?.lottie?.assets?.length,
  lintErrors: (editor?.lint_errors ?? []).map((error) => ({
    severity: error.severity,
    message: error.message,
  })),
  visibleError: error_container?.style?.display !== "none" ? error_container?.textContent?.trim() : "",
})`);

const screenshot = await command("Page.captureScreenshot", {
  format: "png",
  captureBeyondViewport: false,
});
await writeFile(screenshotPath, Buffer.from(screenshot.data, "base64"));
socket.close();

const lintSummary = Object.entries(
  status.lintErrors.reduce((summary, error) => {
    const key = `${error.severity}: ${error.message}`;
    summary[key] = (summary[key] ?? 0) + 1;
    return summary;
  }, {}),
).map(([message, count]) => ({ message, count }));
const schemaErrorCount = status.lintErrors.filter((error) => error.severity === "error").length;
delete status.lintErrors;

console.log(JSON.stringify({
  ...status,
  validationCompleted,
  schemaErrorCount,
  lintSummary,
  browserErrors,
}, null, 2));

if (!status.lottieLoaded || !status.animationLoaded || status.visibleError || schemaErrorCount > 0 || browserErrors.length > 0) {
  process.exitCode = 1;
}
