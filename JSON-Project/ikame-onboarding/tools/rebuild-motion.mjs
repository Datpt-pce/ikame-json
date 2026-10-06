import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";

const projectDirectory = join(process.cwd(), "JSON-Project", "ikame-onboarding");
const sourceDirectory = join(projectDirectory, "source");
const assetDirectory = join(sourceDirectory, "figma-assets");
const distDirectory = join(projectDirectory, "dist");

const sourceDocument = JSON.parse(
  await readFile(join(sourceDirectory, "figma-node-6726-55902.json"), "utf8"),
);
const plan = JSON.parse(await readFile(join(sourceDirectory, "figma-layer-plan.json"), "utf8"));

if (sourceDocument.file_key !== plan.file_key || sourceDocument.root_node_id !== plan.root_node_id) {
  throw new Error("The motion plan does not match the scoped Figma source.");
}

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
  if (current?.id !== ancestorId) {
    throw new Error(`Node ${nodeId} is not inside source frame ${ancestorId}.`);
  }
  return (rotation * 180) / Math.PI;
}

const easeIn = { x: [0.667], y: [1] };
const easeOut = { x: [0.333], y: [0] };

function scaleFrame(frame, speedMultiplier) {
  return Math.round(frame / speedMultiplier);
}

function animatedProperty(frames) {
  return {
    a: 1,
    k: frames.map((frame, index) => {
      const keyframe = { t: frame.time, s: frame.value };
      const next = frames[index + 1];
      if (next) {
        keyframe.e = next.value;
        keyframe.i = easeIn;
        keyframe.o = easeOut;
      }
      if (frame.hold) keyframe.h = 1;
      return keyframe;
    }),
  };
}

function opacityProperty(start, sceneEnd, outFrame, exits, entranceFrames = 12) {
  const frames = [
    { time: start, value: [0] },
    { time: start + entranceFrames, value: [100] },
  ];
  if (exits) {
    frames.push(
      { time: sceneEnd, value: [100] },
      { time: outFrame, value: [0] },
    );
  }
  return animatedProperty(frames);
}

function transformFor({
  motion,
  start,
  position,
  scale,
  sceneEnd,
  outFrame,
  exits,
  rotation = 0,
  lockPositionScale = false,
  staticOpacity = false,
  speedMultiplier = 1,
}) {
  const [x, y, z] = position;
  const [sx, sy, sz] = scale;
  const isTextReveal = motion === "typing" || motion === "text";
  const duration = (frames) => Math.max(1, scaleFrame(frames, speedMultiplier));
  let positionProperty = { a: 0, k: position };
  let scaleProperty = { a: 0, k: scale };

  if (!lockPositionScale && isTextReveal) {
    positionProperty = animatedProperty([
      { time: start, value: [x, y + 6, z] },
      { time: start + duration(10), value: position },
    ]);
  } else if (!lockPositionScale && motion === "rise") {
    positionProperty = animatedProperty([
      { time: start, value: [x, y + 28, z] },
      { time: start + duration(12), value: [x, y - 3, z] },
      { time: start + duration(18), value: position },
    ]);
  } else if (!lockPositionScale && motion === "wipe") {
    positionProperty = animatedProperty([
      { time: start, value: [x - 22, y, z] },
      { time: start + duration(18), value: position },
    ]);
    scaleProperty = animatedProperty([
      { time: start, value: [sx * 0.86, sy, sz] },
      { time: start + duration(18), value: scale },
    ]);
  } else if (!lockPositionScale && motion === "pop") {
    positionProperty = animatedProperty([
      { time: start, value: [x, y + 12, z] },
      { time: start + duration(12), value: [x, y - 2, z] },
      { time: start + duration(18), value: position },
    ]);
    scaleProperty = animatedProperty([
      { time: start, value: [sx * 0.88, sy * 0.88, sz] },
      { time: start + duration(12), value: [sx * 1.035, sy * 1.035, sz] },
      { time: start + duration(18), value: scale },
    ]);
  } else if (!lockPositionScale && motion === "pulse") {
    scaleProperty = animatedProperty([
      { time: start, value: [sx * 0.9, sy * 0.9, sz] },
      { time: start + duration(12), value: scale },
      { time: start + duration(26), value: [sx * 1.08, sy * 1.08, sz] },
      { time: start + duration(38), value: scale },
    ]);
  }

  return {
    o: staticOpacity
      ? { a: 0, k: 100 }
      : opacityProperty(
          start,
          sceneEnd,
          outFrame,
          exits,
          duration(isTextReveal ? 10 : 12),
        ),
    r: { a: 0, k: rotation },
    p: positionProperty,
    a: { a: 0, k: [0, 0, 0] },
    s: scaleProperty,
  };
}

function imageTransformFor(options) {
  const transform = transformFor(options);
  transform.a = { a: 0, k: options.anchor };
  return transform;
}

function pngDimensions(bytes) {
  const signature = bytes.subarray(1, 4).toString("ascii");
  if (signature !== "PNG") throw new Error("Expected a PNG Figma export.");
  return { width: bytes.readUInt32BE(16), height: bytes.readUInt32BE(20) };
}

function assetFilename(nodeId) {
  return `${nodeId.replaceAll(":", "_").replaceAll(";", "_")}.png`;
}

function assetId(nodeId) {
  return `figma_${nodeId.replace(/[^A-Za-z0-9_-]/g, "_")}`;
}

async function loadAsset(nodeId) {
  const bytes = await readFile(join(assetDirectory, assetFilename(nodeId)));
  const { width, height } = pngDimensions(bytes);
  return {
    id: assetId(nodeId),
    w: width,
    h: height,
    u: "",
    p: `data:image/png;base64,${bytes.toString("base64")}`,
    e: 1,
    figma_node_id: nodeId,
    sha256: createHash("sha256").update(bytes).digest("hex"),
  };
}

function rgbaFromNode(node) {
  const fill = (node.fills ?? []).find((candidate) => candidate.visible !== false);
  const gradientColor = fill?.gradientStops?.[0]?.color;
  const color = fill?.color ?? gradientColor ?? node.backgroundColor ?? { r: 1, g: 1, b: 1, a: 1 };
  const alpha = (fill?.opacity ?? 1) * (color.a ?? 1);
  return { color: [color.r, color.g, color.b, 1], opacity: alpha * 100 };
}

function frameFillLayer({ sourceFrame, output, outputEnd }) {
  const fill = (sourceFrame.fills ?? sourceFrame.background ?? []).find(
    (candidate) => candidate.visible !== false && candidate.type === "GRADIENT_LINEAR",
  );
  if (!fill) throw new Error(`Source frame ${sourceFrame.id} has no linear gradient fill.`);
  const [startHandle, endHandle] = fill.gradientHandlePositions;
  const gradientColors = fill.gradientStops.flatMap((stop) => [
    stop.position,
    stop.color.r,
    stop.color.g,
    stop.color.b,
  ]);

  return {
    ddd: 0,
    ty: 4,
    nm: `background — frame fill — ${sourceFrame.id}`,
    sr: 1,
    ks: {
      o: { a: 0, k: 100 },
      r: { a: 0, k: 0 },
      p: { a: 0, k: [0, 0, 0] },
      a: { a: 0, k: [0, 0, 0] },
      s: { a: 0, k: [100, 100, 100] },
    },
    ao: 0,
    shapes: [
      {
        ty: "rc",
        d: 1,
        s: { a: 0, k: [output.width, output.height] },
        p: { a: 0, k: [output.width / 2, output.height / 2] },
        r: { a: 0, k: 0 },
        nm: "Frame bounds",
      },
      {
        ty: "gf",
        o: { a: 0, k: (fill.opacity ?? 1) * 100 },
        r: 1,
        bm: 0,
        g: { p: fill.gradientStops.length, k: { a: 0, k: gradientColors } },
        s: { a: 0, k: [startHandle.x * output.width, startHandle.y * output.height] },
        e: { a: 0, k: [endHandle.x * output.width, endHandle.y * output.height] },
        t: 1,
        nm: "Figma frame gradient",
      },
    ],
    ip: 0,
    op: outputEnd,
    st: 0,
    bm: 0,
    figma: {
      node_id: sourceFrame.id,
      node_name: sourceFrame.name,
      node_type: sourceFrame.type,
      role: "background",
      frame_fill: true,
    },
  };
}

function shapeLayer({ node, sourceFrame, spec, scene, outputEnd, speedMultiplier }) {
  const box = node.absoluteBoundingBox;
  const frameBox = sourceFrame.absoluteBoundingBox;
  const start = scene.start + (spec.delay ?? 0);
  const isLastScene = scene.end === outputEnd;
  const shared = spec.shared === true;
  const exits = !shared && !spec.persist && !isLastScene;
  const outFrame =
    shared || spec.persist || isLastScene
      ? outputEnd
      : scene.end + scaleFrame(12, speedMultiplier);
  const x = box.x - frameBox.x + box.width / 2;
  const y = box.y - frameBox.y + box.height / 2;
  const shapeWidth = node.size?.x ?? box.width;
  const shapeHeight = node.size?.y ?? box.height;
  const radius = node.cornerRadius ?? Math.min(...(node.rectangleCornerRadii ?? [0]));
  const { color, opacity } = rgbaFromNode(node);
  const transform = transformFor({
    motion: spec.motion,
    start,
    position: [x, y, 0],
    scale: [100, 100, 100],
    sceneEnd: scene.end,
    outFrame,
    exits,
    rotation: rotationWithin(node.id, sourceFrame.id),
    lockPositionScale: spec.role === "background",
    staticOpacity: spec.role === "background" && (shared || scene.start === 0),
    speedMultiplier,
  });

  return {
    ddd: 0,
    ty: 4,
    nm: `${spec.role} — ${node.name} — ${node.id}`,
    sr: 1,
    ks: transform,
    ao: 0,
    shapes: [
      {
        ty: "rc",
        d: 1,
        s: { a: 0, k: [shapeWidth, shapeHeight] },
        p: { a: 0, k: [0, 0] },
        r: { a: 0, k: Math.min(radius, shapeWidth / 2, shapeHeight / 2) },
        nm: node.name,
      },
      { ty: "fl", c: { a: 0, k: color }, o: { a: 0, k: opacity }, r: 1, nm: "Figma fill" },
    ],
    ip: start,
    op: outFrame,
    st: 0,
    bm: 0,
    figma: {
      node_id: node.id,
      node_name: node.name,
      node_type: node.type,
      role: spec.role,
      shared,
      shared_background: shared && spec.role === "background",
      ...(spec.role !== "background" ? { entrance_fx: "cross_dissolve" } : {}),
    },
  };
}

function imageLayer({
  node,
  sourceFrame,
  spec,
  scene,
  output,
  outputEnd,
  asset,
  speedMultiplier,
}) {
  const box = node.absoluteBoundingBox;
  const frameBox = sourceFrame.absoluteBoundingBox;
  const start = scene.start + (spec.delay ?? 0);
  const isLastScene = scene.end === outputEnd;
  const shared = spec.shared === true;
  const exits = !shared && !spec.persist && !isLastScene;
  const outFrame =
    shared || spec.persist || isLastScene
      ? outputEnd
      : scene.end + scaleFrame(12, speedMultiplier);
  const isCover = spec.fit === "cover";
  const x = isCover ? output.width / 2 : box.x - frameBox.x + box.width / 2;
  const y = isCover ? output.height / 2 : box.y - frameBox.y + box.height / 2;
  const scale = isCover
    ? (() => {
        const coverScale = Math.max(output.width / asset.w, output.height / asset.h) * 100;
        return [coverScale, coverScale, 100];
      })()
    : [(box.width / asset.w) * 100, (box.height / asset.h) * 100, 100];
  const transform = imageTransformFor({
    motion: spec.motion,
    start,
    position: [x, y, 0],
    scale,
    anchor: [asset.w / 2, asset.h / 2, 0],
    sceneEnd: scene.end,
    outFrame,
    exits,
    lockPositionScale: spec.role === "background",
    staticOpacity: spec.role === "background" && (shared || scene.start === 0),
    speedMultiplier,
  });

  const layer = {
    ddd: 0,
    ty: 2,
    nm: `${spec.role} — ${node.name} — ${node.id}`,
    refId: asset.id,
    sr: 1,
    ks: transform,
    ao: 0,
    ip: start,
    op: outFrame,
    st: 0,
    bm: 0,
    figma: {
      node_id: node.id,
      node_name: node.name,
      node_type: node.type,
      role: spec.role,
      shared,
      shared_background: shared && spec.role === "background",
      ...(spec.role !== "background" ? { entrance_fx: "cross_dissolve" } : {}),
      ...(spec.fit ? { fit: spec.fit } : {}),
    },
  };

  const reveal = spec.motion === "typing" || spec.motion === "text"
    ? { start, end: start + scaleFrame(10, speedMultiplier) }
    : undefined;
  return { layer, reveal };
}

for (const output of plan.outputs) {
  const speedMultiplier = output.speed_multiplier ?? 1;
  const scenes = output.scenes.map((scene) => ({
    ...scene,
    start: scaleFrame(scene.start, speedMultiplier),
    end: scaleFrame(scene.end, speedMultiplier),
    layers: scene.layers.map((spec) => ({
      ...spec,
      delay: scaleFrame(spec.delay ?? 0, speedMultiplier),
    })),
  }));
  const outputEnd = scenes.at(-1).end;
  const assets = [];
  const assetsByNode = new Map();
  const bottomToTopLayers = [];
  const textReveals = [];

  if (output.include_frame_fill) {
    const firstSourceFrame = nodes.get(scenes[0].source_frame_id);
    bottomToTopLayers.push(frameFillLayer({ sourceFrame: firstSourceFrame, output, outputEnd }));
  }

  for (const scene of scenes) {
    const sourceFrame = nodes.get(scene.source_frame_id);
    if (!sourceFrame) throw new Error(`Missing source frame ${scene.source_frame_id}.`);

    for (const spec of scene.layers) {
      const node = nodes.get(spec.node_id);
      if (!node) throw new Error(`Missing Figma node ${spec.node_id}.`);
      if (spec.kind === "shape") {
        bottomToTopLayers.push(
          shapeLayer({ node, sourceFrame, spec, scene, outputEnd, speedMultiplier }),
        );
        continue;
      }

      let asset = assetsByNode.get(node.id);
      if (!asset) {
        asset = await loadAsset(node.id);
        assetsByNode.set(node.id, asset);
        assets.push(asset);
      }
      const result = imageLayer({
        node,
        sourceFrame,
        spec,
        scene,
        output,
        outputEnd,
        asset,
        speedMultiplier,
      });
      bottomToTopLayers.push(result.layer);
      if (result.reveal) {
        textReveals.push({
          node_id: node.id,
          text: node.characters,
          start_frame: result.reveal.start,
          end_frame: result.reveal.end,
          visual_lead_frames: spec.delay ?? 0,
          final_hold_frames: scene.end - result.reveal.end,
        });
      }
    }
  }

  const animation = {
    v: "5.12.2",
    fr: output.fps,
    ip: 0,
    op: outputEnd,
    w: output.width,
    h: output.height,
    nm: output.file.replace(".json", ""),
    ddd: 0,
    assets,
    layers: bottomToTopLayers.reverse().map((layer, index) => ({ ...layer, ind: index + 1 })),
    markers: scenes.map((scene) => ({
      tm: scene.start,
      cm: scene.id,
      dr: scene.end - scene.start,
    })),
    meta: {
      generator: "ikame direct Figma layer builder",
      source: {
        file_key: plan.file_key,
        root_node_id: plan.root_node_id,
        version: sourceDocument.version,
        last_modified: sourceDocument.last_modified,
      },
      layer_strategy: "direct Figma node layers",
      asset_strategy: "embedded PNG exports of individual Figma nodes",
      speed_multiplier: speedMultiplier,
      entrance_fx: "cross_dissolve for every non-background layer",
      reading_timing: {
        fps: output.fps,
        scenes: scenes.map((scene) => ({
          id: scene.id,
          frames: scene.end - scene.start,
          seconds: (scene.end - scene.start) / output.fps,
          source_seconds: scene.reading_seconds,
          rationale: scene.rationale,
        })),
      },
      text_reveals: textReveals,
    },
  };

  await writeFile(join(distDirectory, output.file), JSON.stringify(animation));
  console.log(`Built ${output.file}: ${animation.layers.length} layers, ${assets.length} assets.`);
}
