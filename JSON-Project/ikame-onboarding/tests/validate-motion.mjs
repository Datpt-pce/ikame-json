import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { join } from "node:path";

const projectDirectory = join(process.cwd(), "JSON-Project", "ikame-onboarding");
const sourceDocument = JSON.parse(
  await readFile(join(projectDirectory, "source", "figma-node-6726-55902.json"), "utf8"),
);
const plan = JSON.parse(
  await readFile(join(projectDirectory, "source", "figma-layer-plan.json"), "utf8"),
);
const builderSource = await readFile(join(projectDirectory, "tools", "rebuild-motion.mjs"), "utf8");

const scaleFrame = (frame, speedMultiplier) => Math.round(frame / speedMultiplier);

const nodes = new Map();
const parentIds = new Map();
(function visit(node, parent) {
  nodes.set(node.id, node);
  if (parent) parentIds.set(node.id, parent.id);
  for (const child of node.children ?? []) visit(child, node);
})(sourceDocument.document, null);

function rotationWithin(nodeId, ancestorId) {
  let rotation = 0;
  let current = nodes.get(nodeId);
  while (current && current.id !== ancestorId) {
    const transform = current.relativeTransform;
    if (transform) rotation += Math.atan2(transform[1][0], transform[0][0]);
    current = nodes.get(parentIds.get(current.id));
  }
  assert.equal(current?.id, ancestorId, `${nodeId}: expected ancestor ${ancestorId}`);
  return (rotation * 180) / Math.PI;
}

assert.equal(plan.file_key, sourceDocument.file_key, "plan must target the fetched Figma file");
assert.equal(plan.root_node_id, sourceDocument.root_node_id, "plan must stay inside the fetched subtree");
assert.deepEqual(
  plan.outputs.map((output) => output.file),
  ["welcome-1.json", "on-1.json", "on-2.json", "on-3.json"],
  "exactly four requested outputs are required",
);

for (const pattern of [/cropAsset/i, /ffmpeg/i, /delogo/i, /crop=/i, /without_text/i, /image_stage_/i]) {
  assert.doesNotMatch(builderSource, pattern, `builder must not contain legacy screenshot processing: ${pattern}`);
}

for (const output of plan.outputs) {
  assert.equal(output.fps, 30, `${output.file}: fixed 30 fps contract`);
  assert.equal(output.speed_multiplier, 1.5, `${output.file}: playback is authored at 1.5x speed`);
  assert.ok(output.width > 0 && output.height > 0, `${output.file}: positive canvas`);
  assert.ok(output.scenes.length > 0, `${output.file}: scenes required`);

  let previousEnd = 0;
  for (const scene of output.scenes) {
    assert.equal(scene.start, previousEnd, `${output.file}/${scene.id}: scenes must be contiguous`);
    assert.ok(scene.end > scene.start, `${output.file}/${scene.id}: positive duration`);
    assert.ok(scene.reading_seconds >= 2, `${output.file}/${scene.id}: explicit reading allowance`);
    assert.ok(scene.rationale, `${output.file}/${scene.id}: timing rationale required`);
    previousEnd = scene.end;

    const sourceFrame = nodes.get(scene.source_frame_id);
    assert.ok(sourceFrame, `${output.file}/${scene.id}: source frame exists`);
    assert.equal(sourceFrame.type, "FRAME", `${output.file}/${scene.id}: source frame type`);

    let earliestVisual = Infinity;
    let earliestText = Infinity;
    for (const layer of scene.layers) {
      const sourceNode = nodes.get(layer.node_id);
      assert.ok(sourceNode, `${output.file}/${scene.id}: missing node ${layer.node_id}`);
      assert.notEqual(sourceNode.type, "SECTION", `${layer.node_id}: section cannot masquerade as a layer`);
      assert.notEqual(sourceNode.id, scene.source_frame_id, `${layer.node_id}: full scene screenshots are forbidden`);
      assert.ok(sourceNode.absoluteBoundingBox, `${layer.node_id}: layer needs source bounds`);
      assert.ok(["image", "shape"].includes(layer.kind), `${layer.node_id}: supported layer kind`);
      assert.ok(["background", "visual", "text", "ui"].includes(layer.role), `${layer.node_id}: semantic role`);

      const entrance = scene.start + (layer.delay ?? 0);
      if (layer.role === "text") {
        earliestText = Math.min(earliestText, entrance);
        assert.equal(sourceNode.type, "TEXT", `${layer.node_id}: text must come from a Figma TEXT node`);
        assert.ok(["typing", "text"].includes(layer.motion), `${layer.node_id}: text has an explicit reveal intent`);
      } else {
        earliestVisual = Math.min(earliestVisual, entrance);
      }
    }
    if (Number.isFinite(earliestText)) {
      assert.ok(earliestText > earliestVisual, `${output.file}/${scene.id}: visual must precede text`);
    }
  }
}

for (const output of plan.outputs) {
  const animation = JSON.parse(await readFile(join(projectDirectory, "dist", output.file), "utf8"));
  const expectedDuration = scaleFrame(output.scenes.at(-1).end, output.speed_multiplier);
  assert.equal(animation.w, output.width, `${output.file}: width`);
  assert.equal(animation.h, output.height, `${output.file}: height`);
  assert.equal(animation.fr, output.fps, `${output.file}: fps`);
  assert.equal(animation.op, expectedDuration, `${output.file}: duration`);
  assert.equal(animation.meta?.source?.file_key, plan.file_key, `${output.file}: Figma provenance`);
  assert.equal(animation.meta?.source?.root_node_id, plan.root_node_id, `${output.file}: scoped root provenance`);
  assert.equal(animation.meta?.layer_strategy, "direct Figma node layers", `${output.file}: layer strategy`);
  assert.equal(
    animation.meta?.speed_multiplier,
    output.speed_multiplier,
    `${output.file}: speed multiplier is embedded`,
  );
  assert.equal(animation.markers.length, output.scenes.length, `${output.file}: one marker per scene`);
  assert.deepEqual(
    animation.markers.map(({ tm, dr }) => ({ tm, dr })),
    output.scenes.map((scene) => ({
      tm: scaleFrame(scene.start, output.speed_multiplier),
      dr:
        scaleFrame(scene.end, output.speed_multiplier) -
        scaleFrame(scene.start, output.speed_multiplier),
    })),
    `${output.file}: scene markers are scaled with the complete timeline`,
  );

  const assetsById = new Map(animation.assets.map((asset) => [asset.id, asset]));
  assert.ok(animation.layers.length >= output.scenes.length * 2, `${output.file}: layer-based composition`);
  for (const layer of animation.layers) {
    assert.ok(layer.figma?.node_id, `${output.file}/${layer.nm}: node provenance on every layer`);
    assert.ok(nodes.has(layer.figma.node_id), `${output.file}/${layer.nm}: provenance node exists`);
    assert.equal(layer.tt, undefined, `${output.file}/${layer.nm}: track mattes are forbidden for renderer safety`);
    assert.equal(layer.td, undefined, `${output.file}/${layer.nm}: matte source layers are forbidden`);
    assert.equal(layer.masksProperties, undefined, `${output.file}/${layer.nm}: generated masks are forbidden`);
    if (layer.figma.role === "background") {
      assert.equal(layer.ks?.p?.a, 0, `${output.file}/${layer.nm}: background position stays fixed`);
      assert.equal(layer.ks?.s?.a, 0, `${output.file}/${layer.nm}: background scale stays fixed`);
    } else {
      assert.equal(
        layer.figma.entrance_fx,
        "cross_dissolve",
        `${output.file}/${layer.nm}: non-background entrance FX contract`,
      );
      assert.equal(layer.ks?.o?.a, 1, `${output.file}/${layer.nm}: cross dissolve animates opacity`);
      assert.deepEqual(layer.ks.o.k[0].s, [0], `${output.file}/${layer.nm}: cross dissolve starts hidden`);
      assert.deepEqual(layer.ks.o.k[1].s, [100], `${output.file}/${layer.nm}: cross dissolve reaches full opacity`);
    }
    if (layer.figma.shared_background) {
      assert.deepEqual(layer.ks.o, { a: 0, k: 100 }, `${output.file}/${layer.nm}: shared background stays fully static`);
      assert.equal(layer.op, animation.op, `${output.file}/${layer.nm}: shared background persists to the end`);
    }
    if (layer.ty === 2) {
      const asset = assetsById.get(layer.refId);
      assert.ok(asset, `${output.file}/${layer.nm}: referenced asset exists`);
      assert.equal(asset.figma_node_id, layer.figma.node_id, `${output.file}/${layer.nm}: asset provenance matches`);
      assert.match(asset.p, /^data:image\/png;base64,/, `${output.file}/${layer.nm}: embedded direct node export`);
    }
  }

  assert.deepEqual(
    animation.meta.reading_timing.scenes.map((scene) => scene.frames),
    output.scenes.map(
      (scene) =>
        scaleFrame(scene.end, output.speed_multiplier) -
        scaleFrame(scene.start, output.speed_multiplier),
    ),
    `${output.file}: reading durations are embedded`,
  );
  for (const reveal of animation.meta.text_reveals) {
    assert.ok(reveal.visual_lead_frames >= 8, `${output.file}/${reveal.node_id}: visual lead`);
    assert.ok(reveal.final_hold_frames >= 30, `${output.file}/${reveal.node_id}: reading hold`);
  }
}

const on1 = JSON.parse(await readFile(join(projectDirectory, "dist", "on-1.json"), "utf8"));
const on1Plan = plan.outputs.find((output) => output.file === "on-1.json");
const on1NodeIds = on1.layers.map((layer) => layer.figma.node_id);
for (const nodeId of ["6726:142934", "6726:142936", "6726:142937", "6726:142938", "6726:142948"]) {
  const layers = on1.layers.filter((layer) => layer.figma.node_id === nodeId);
  assert.equal(layers.length, 1, `on-1: one persistent shared layer for ${nodeId}`);
  assert.equal(
    layers[0].op,
    scaleFrame(675, on1Plan.speed_multiplier),
    `on-1/${nodeId}: shared call layer persists`,
  );
}
for (const nodeId of ["6726:142934", "6726:142936", "6726:142937"]) {
  const layer = on1.layers.find((candidate) => candidate.figma.node_id === nodeId);
  assert.equal(
    layer.ip,
    scaleFrame(105, on1Plan.speed_multiplier),
    `on-1/${nodeId}: shared background starts once`,
  );
}
for (const duplicateNodeId of [
  "6726:142955", "6726:142883", "6726:142909",
  "6726:142956", "6726:142884", "6726:142910",
  "6726:142957", "6726:142885", "6726:142911",
  "6726:142958", "6726:142886", "6726:142912",
  "6726:142968", "6726:142896", "6726:142922",
]) {
  assert.ok(!on1NodeIds.includes(duplicateNodeId), `on-1: duplicate persistent layer ${duplicateNodeId} must be removed`);
}

const on1FramePositions = on1Plan.scenes.map(
  (scene) => nodes.get(scene.source_frame_id).absoluteBoundingBox,
);
for (let index = 1; index < on1FramePositions.length; index += 1) {
  assert.equal(
    on1FramePositions[index].y,
    on1FramePositions[index - 1].y,
    `on-1/${on1Plan.scenes[index].id}: source frames remain on the same Figma row`,
  );
  assert.ok(
    on1FramePositions[index].x > on1FramePositions[index - 1].x,
    `on-1/${on1Plan.scenes[index].id}: source frames follow the Figma flow left to right`,
  );
}
const callGreeting = on1Plan.scenes.find((scene) => scene.id === "call_greeting");
assert.deepEqual(
  [...callGreeting.layers]
    .filter((layer) => layer.role !== "background")
    .sort((left, right) => (left.delay ?? 0) - (right.delay ?? 0))
    .map((layer) => layer.node_id),
  ["6726:142948", "6726:142949", "6726:142938", "6726:142953"],
  "on-1/call_greeting: reveal tutor, chat, lower controls, then greeting text",
);

const welcomePlan = plan.outputs.find((output) => output.file === "welcome-1.json");
const welcome = JSON.parse(await readFile(join(projectDirectory, "dist", "welcome-1.json"), "utf8"));
assert.equal(welcomePlan.include_frame_fill, true, "welcome-1: Figma frame fill is part of the composition");
const welcomeFrameFill = welcome.layers.find((layer) => layer.figma?.frame_fill);
assert.ok(welcomeFrameFill, "welcome-1: frame gradient prevents transparent checkerboard gaps");
assert.equal(welcomeFrameFill.figma.node_id, welcomePlan.scenes[0].source_frame_id, "welcome-1: frame fill provenance");
assert.equal(welcomeFrameFill.ip, 0, "welcome-1: frame fill starts immediately");
assert.equal(welcomeFrameFill.op, welcome.op, "welcome-1: frame fill persists for the full animation");
assert.equal(welcomeFrameFill.ks.p.a, 0, "welcome-1: frame fill position is static");
assert.equal(welcomeFrameFill.ks.s.a, 0, "welcome-1: frame fill scale is static");
assert.ok(
  welcomeFrameFill.shapes.some((shape) => shape.ty === "gf"),
  "welcome-1: frame fill preserves the Figma linear gradient",
);
const welcomeFramePositions = welcomePlan.scenes.map(
  (scene) => nodes.get(scene.source_frame_id).absoluteBoundingBox,
);
for (let index = 1; index < welcomeFramePositions.length; index += 1) {
  assert.ok(
    welcomeFramePositions[index].x > welcomeFramePositions[index - 1].x,
    `welcome-1/${welcomePlan.scenes[index].id}: source frames follow the Figma flow from left to right`,
  );
  assert.equal(
    welcomeFramePositions[index].y,
    welcomeFramePositions[index - 1].y,
    `welcome-1/${welcomePlan.scenes[index].id}: source frames remain on the same Figma row`,
  );
}

const welcomeLayerIndexes = new Map(
  welcome.layers.map((layer, index) => [layer.figma.node_id, index]),
);
for (const scene of welcomePlan.scenes) {
  const plannedIndexes = scene.layers.map((layer) => welcomeLayerIndexes.get(layer.node_id));
  assert.ok(
    plannedIndexes.every((index) => Number.isInteger(index)),
    `welcome-1/${scene.id}: every planned Figma layer is present`,
  );
  for (let index = 1; index < plannedIndexes.length; index += 1) {
    assert.ok(
      plannedIndexes[index] < plannedIndexes[index - 1],
      `welcome-1/${scene.id}: Lottie stacking preserves Figma bottom-to-top order`,
    );
  }
}

for (const bubbleNodeId of [
  "6726:41869",
  "6726:45379",
  "6726:48868",
  "6726:52393",
  "6726:55900",
]) {
  const sourceNode = nodes.get(bubbleNodeId);
  const layer = welcome.layers.find((candidate) => candidate.figma.node_id === bubbleNodeId);
  const sourceScene = welcomePlan.scenes.find((scene) =>
    scene.layers.some((candidate) => candidate.node_id === bubbleNodeId),
  );
  const expectedRotation = rotationWithin(bubbleNodeId, sourceScene.source_frame_id);
  assert.ok(layer, `welcome-1: bubble ${bubbleNodeId} exists`);
  assert.ok(
    Math.abs(layer.ks.r.k - expectedRotation) < 0.0001,
    `welcome-1/${bubbleNodeId}: bubble follows its Figma rotation`,
  );
  assert.deepEqual(
    layer.shapes.find((shape) => shape.ty === "rc").s.k,
    [sourceNode.size.x, sourceNode.size.y],
    `welcome-1/${bubbleNodeId}: rotated bubble uses its unrotated Figma size`,
  );
}

const on3 = JSON.parse(await readFile(join(projectDirectory, "dist", "on-3.json"), "utf8"));
const on3Plan = plan.outputs.find((output) => output.file === "on-3.json");
const graduate = on3.layers.find((layer) => layer.figma.node_id === "6726:143034");
const campus = on3.layers.find((layer) => layer.figma.node_id === "6726:143032");
const lowerFade = on3.layers.find((layer) => layer.figma.node_id === "6726:143035");
assert.ok(graduate, "on-3: transparent graduate foreground exists");
assert.equal(graduate.figma.role, "visual", "on-3: graduate remains a foreground layer");
assert.ok(campus, "on-3: campus remains the fixed background");
assert.equal(campus.figma.role, "background", "on-3: campus has background semantics");
assert.equal(campus.ks.p.a, 0, "on-3: campus position is static");
assert.equal(campus.ks.s.a, 0, "on-3: campus scale is static");
assert.ok(lowerFade, "on-3: full-width lower fade remains above the campus");
assert.ok(!on3.layers.some((layer) => layer.figma.node_id === "6726:143033"), "on-3: unrelated blue overlay is removed");

const journey = on3Plan.scenes.find((scene) => scene.id === "learning_journey");
const bottomToTopJourneyNodeIds = [
  "6726:143054",
  "6726:143047",
  "6726:143060",
  "6726:143039",
  "6726:143037",
];
assert.deepEqual(
  [...journey.layers]
    .filter((layer) => bottomToTopJourneyNodeIds.includes(layer.node_id))
    .sort((left, right) => (left.delay ?? 0) - (right.delay ?? 0))
    .map((layer) => layer.node_id),
  bottomToTopJourneyNodeIds,
  "on-3/learning_journey: four icons and arrow reveal bottom to top",
);

console.log("PASS: four animations use direct Figma layers with motion and reading-aware timing");
