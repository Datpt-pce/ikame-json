import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { join } from "node:path";

const projectDirectory = join(process.cwd(), "JSON-Project", "ikame-onboarding");
const sourcePath = join(projectDirectory, "source", "figma-node-6726-55902.json");
const source = JSON.parse(await readFile(sourcePath, "utf8"));

assert.equal(source.file_key, "mmMqlJ5drO1IhYTaHDCm7f", "must use the AI-Learn file");
assert.equal(source.root_node_id, "6726:55902", "must fetch only the requested root node");
assert.equal(source.document.id, source.root_node_id, "document root must match requested node");

const seenIds = new Set();
let nodeCount = 0;
function visit(node) {
  assert.equal(typeof node.id, "string", "every Figma node needs an id");
  assert.ok(!seenIds.has(node.id), `duplicate Figma node id ${node.id}`);
  seenIds.add(node.id);
  nodeCount += 1;
  for (const child of node.children ?? []) visit(child);
}
visit(source.document);

assert.ok(nodeCount > 1, "requested Figma root must contain a layer tree");
assert.ok(!JSON.stringify(source).includes("X-Figma-Token"), "source snapshot must not contain the PAT");

console.log(`PASS: scoped Figma source contains ${nodeCount} uniquely identified nodes`);
