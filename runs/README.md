# Astra run archive

Every modeling attempt belongs in its own timestamped folder, for example `runs/2026-09-09_qj_initial/`.

Create an archive before starting a real run:

```powershell
.\scripts\new_astra_run.ps1 `
  -Subject qj `
  -Stage initial `
  -PromptPath .\runs\prompts\qj_initial.md
```

Use `-Subject cr400af` and the matching prompt for the second track. The script copies the exact prompt, snapshots the selected reference rows, creates checkpoint folders, and leaves explicit placeholders for the real recording. It never fabricates a video file or a Blender checkpoint.

Required files:

- `prompt.md`: exact prompt sent to Astra.
- `run-log.csv`: timestamps, iterations, failures, repairs, and manual interventions.
- `screen-recording.mkv`: untouched full screen recording, including waits and errors.
- `reference-used.csv`: IDs from `references/reference-index.csv` actually supplied to the run.
- `checkpoints/`: `v00_ai_initial.blend`, each repair checkpoint, and `v99_human_finish.blend`.
- `manual-interventions.md`: every human edit, reason, time, and affected component.

The prompt files in `runs/prompts/` are ready-to-run templates. They are not evidence that Astra has already been run. A real run is complete only when the untouched screen recording, `v00_ai_initial.blend`, repair checkpoints, export, and log are present in its own archive.

Do not describe the procedural baseline in `models/` as an Astra result. The first real Astra run must be labeled `ai_initial`, and the result must be retained before any manual edit.
