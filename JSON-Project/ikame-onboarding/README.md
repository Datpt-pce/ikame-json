# iKame onboarding Lottie handoff

## Source and scope

- Design source: [AI Learn — node `6726:55902`](https://www.figma.com/design/mmMqlJ5drO1IhYTaHDCm7f/AI-Learn?node-id=6726-55902)
- Scoped REST snapshot: `source/figma-node-6726-55902.json` (17,746 nodes; no other Figma pages fetched).
- Layer plan: `source/figma-layer-plan.json`.
- Deliverables: `welcome-1`, `on-1`, `on-2`, and `on-3` as standalone Lottie JSON files.
- Sequence rule: follow the Figma flow from left to right, then top to bottom. Visual content enters before related text.

## Deliverables

| File | Canvas | Duration | Layers | Assets | Size | SHA-256 |
|---|---:|---:|---:|---:|---:|---|
| `dist/welcome-1.json` | 750×1320 | 9.00 s | 19 | 13 | 1,685,370 B | `dc510a663ed6904f4b60d4a46c63cc76aa519f4c571d5f8ffece551921a369ad` |
| `dist/on-1.json` | 750×1084 | 15.00 s | 22 | 18 | 4,222,663 B | `eb51a02fc4caa80e4a298d1f47e44a31570c317ca0899f4d76ef399a77b8d904` |
| `dist/on-2.json` | 750×1068 | 6.00 s | 8 | 8 | 1,490,513 B | `3eff62b35d1bbe5bb4cdfd9c8ca3ff0bae9d0b7ce6f1bebfc544cd1ea27af7d8` |
| `dist/on-3.json` | 750×1068 | 9.00 s | 44 | 43 | 4,986,025 B | `87be1289208cd3a2c5c609b78f9981951929ad036596f092dbef0f65cc6fc6d9` |

## Layer and motion contract

- Format: Bodymovin-compatible Lottie JSON, 30 fps, embedded PNG assets.
- Every visible asset is exported from an explicit Figma node ID under `6726:55902`; full scene frames are not used as substitute layers.
- Each Lottie layer carries `figma.node_id`, node name/type, and semantic role. Embedded assets also carry the source node ID and SHA-256.
- Background position and scale remain fixed. A background shared by consecutive scenes is emitted once and persists; only a genuine background change uses an opacity crossfade.
- The full timeline and every entrance/exit animation are authored at a `1.5×` speed multiplier.
- Every non-background layer has an explicit `0→100` opacity cross-dissolve entrance in addition to its role-specific motion.
- Avatars, cards, icons, and controls use restrained eased rise/pop/pulse entrances.
- Native rounded rectangles use their unrotated Figma size and their composed rotation inside the source frame, so greeting bubbles stay aligned with exported text.
- `welcome-1` includes the source frame's persistent linear gradient fill; transparent artwork no longer exposes the host player's checkerboard/background.
- Text is exported directly from its Figma `TEXT` node and revealed with opacity plus a 6 px vertical settle. No masks, track mattes, or runtime fonts are required.
- At the authored `1.5×` speed, visuals lead text by at least 8 frames and every completed text reveal holds for at least 30 frames; question, teaching, and corrective-feedback scenes hold longer.
- `on-1` reveals the tutor, chat, lower controls, then greeting text; `on-3` reveals the four journey icons and arrow from bottom to top.
- Scene markers use semantic IDs such as `call_question`, `phrase_lesson`, and `learning_journey`.
- Host playback should use `autoplay: true`, `loop: false`, preserve the final frame, and render with `contain` behavior.

## Rebuild and verification

The encrypted PAT stays outside the repository at `%LOCALAPPDATA%\ikame-json\figma-token.dpapi`. The PowerShell scripts decrypt it only in memory and never print it.

```powershell
# Refresh only the approved Figma subtree.
& JSON-Project/ikame-onboarding/tools/fetch-figma-source.ps1

# Export the allowlisted layer nodes in one Figma image API request.
& JSON-Project/ikame-onboarding/tools/export-figma-layers.ps1

# Rebuild the four JSON files.
node JSON-Project/ikame-onboarding/tools/rebuild-motion.mjs

# Validate source scope, provenance, animation, ordering, and reading timing.
node JSON-Project/ikame-onboarding/tests/validate-figma-source.mjs
node JSON-Project/ikame-onboarding/tests/validate-motion.mjs
```

`preview.html` is a local QA page for lottie-web 5.12.2. Representative frames across all four final files were rendered with isolated Chrome headless profiles and visually reviewed. The checks include text-reveal states, the persistent `on-1` call background, absence of gray matte artifacts in `welcome-1`, and the seam-free campus/graduate composition in `on-3`.

All four files also load, validate, and render through the LottieDocs JSON Playground. The page reports no render errors or browser-console errors. Its schema checker emits warnings for Bodymovin compatibility fields marked deprecated and for the custom Figma provenance metadata; these warnings do not affect rendering. `tools/test-lottiefiles-playground.mjs` contains the repeatable Chrome DevTools check.

For `welcome-1`, settled frames from all five scenes were compared against direct full-frame Figma exports. Mean absolute RGB-channel difference was 0.54–0.72 on a 0–255 scale; pixels differing by more than three levels per channel covered 0.66–2.26%, concentrated around anti-aliased edges.

Native iOS/Android compatibility remains unverified because the target player, version, and renderer were not supplied.

## Implementation decisions

- Preserve the source hierarchy: when Figma provides separate visual, UI, and text nodes, animate those nodes independently.
- Reconstruct only simple bubble/card fills as native Lottie rounded rectangles so their child text remains independently animatable; the layer still retains the source Figma frame ID.
- Use the original exported text node as the text artwork and a renderer-safe opacity/position reveal. No screen capture is split into pseudo-layers.
- When sequential Figma frames repeat an identical background or persistent element, represent it once across the shared timeline and animate only the changed foreground layers.
- Avoid generated masks and mattes unless the exact target player and renderer have been explicitly validated.
- Acceptance requires visible intermediate motion, correct stacking, readable holds, and a real player render; JSON parsing alone is insufficient.
