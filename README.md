# Dual-track real train modeling project

This project implements a traceable, multi-part modeling workflow for a QJ steam locomotive and a CR400AF EMU.

The source of truth is split into four areas:

- `references/`: unchanged reference photos plus licensing/source metadata.
- `scripts/`: reproducible Blender generation, reference fetching, validation, and viewer serving tools.
- `models/`: generated Blender scenes, GLB exports, and manifests.
- `runs/`: Astra run logs, prompt versions, screen recordings, and manual intervention records.
- `viewer/`: a local Three.js viewer for the two exported GLB models.
- `video/`: Chinese narration, storyboard, capture checklist, and edit manifest.

The included model generator creates a clearly labeled procedural baseline with separate named parts. It is not an Astra run. Replace or extend it with the recorded Astra run while keeping the initial, repair, and human-finish checkpoints.

## Quick start

1. Fetch the rights-traceable Wikimedia Commons references:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\fetch_references.ps1
   ```

2. Generate the multi-part Blender scenes and GLB files. Blender is resolved from the default Windows installation path when it is not on `PATH`:

   ```powershell
   .\scripts\run_blender_build.ps1
   ```

3. Validate the exports:

   ```powershell
   python .\scripts\validate_assets.py
   ```

4. Start the viewer from the project root:

   ```powershell
   npm run viewer:bg
   ```

   Open `http://localhost:41738/viewer/`.

   Use `npm run viewer` when you want the server attached to the current terminal; use `npm run viewer:bg` for the normal persistent local viewer.

5. Follow `video/capture-checklist.md` and store all Astra recordings and versioned files under `runs/`.

6. Start a traceable Astra archive before each real run:

   ```powershell
   .\scripts\new_astra_run.ps1 -Subject qj -Stage initial -PromptPath .\runs\prompts\qj_initial.md
   ```

   The viewer also loads `models/model-manifest.json` and the reference index. Select a visible mesh in the 3D view to inspect its role and open the preserved local reference image or source page.

The final video is intentionally not marked complete until real Astra screen recordings, untouched AI checkpoints, repair logs, and a human voice recording exist. `video/production-manifest.json` records this gate and the exact parallel-scene evidence requirements.

## Attribution

The reference index is generated from Wikimedia Commons metadata. The project keeps source URLs, authors, licenses, access dates, and local SHA-256 hashes. Review each license before publishing a reference image in the final video; CC BY and CC BY-SA images require the attribution shown in `references/reference-index.csv`.
