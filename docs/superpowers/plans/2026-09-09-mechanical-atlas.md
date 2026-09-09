# Mechanical Atlas Implementation Plan

**Goal:** Turn the existing Leopard 2 GLB into a deployable interactive web atlas matching the reference application's relevant model interactions with a new dark layout.

**Architecture:** A separate Vite application under `atlas/` uses Three.js for model rendering and standard DOM controls. Pure model metadata, viewer behavior, and interface state are separate modules. The original Blender/GLB assets remain the source; the web package includes the GLB.

**Tech Stack:** Three.js, OrbitControls, GLTFLoader, GLTFExporter, lucide, Vite, Playwright.

- [x] Read the linked model task and inspect existing assets.
- [x] Audit reference source and list feature parity.
- [x] Classify all source mesh names and provide Chinese component metadata.
- [x] Implement model selection, visibility, isolation, explode, section planes, view controls, and export.
- [x] Implement responsive dark application shell and connect every visible control.
- [x] Build a deployable static distribution and document start/deploy commands.
- [x] Verify desktop/mobile screenshots, nonblank canvas, pointer interaction, and stateful workflows in a real browser.

Verification: 3 source-data tests and 11 browser workflows pass against the production static server. Viewports include 320, 390, 768, 1536, and 1920 pixels. The production build also loads from a nested URL. Reports and screenshots are under `atlas/qa/`.
