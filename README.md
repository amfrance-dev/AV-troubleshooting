# AudioVisualSpatiotemporalStudy

This repository contains the runnable experiment bundle for a PsychoPy-based audiovisual spatiotemporal awareness study.

## What The Project Does

Participants watch black-and-white objects appear in one of four screen corners while some objects also play a sound. They respond with the matching numpad key based on the current target rules for the block.

The task logs:

- per-stimulus timing and response data
- per-keypress response data
- per-trial frame-timing summaries

## What Is In This Runtime Bundle

- [`av_spatiotemporal_study.py`](./av_spatiotemporal_study.py): main experiment script
- [`validate_data.py`](./validate_data.py): QC script for saved CSV outputs
- [`AV_Study_README.md`](./AV_Study_README.md): detailed operator guide
- [`CSV_CHEATSHEET.md`](./CSV_CHEATSHEET.md): quick reference for output columns
- [`20_stimuli`](./20_stimuli): required image and audio assets
- [`otherblobs.png`](./otherblobs.png): background noise source image
- [`data`](./data): output folder for participant/session runs

This branch intentionally excludes legacy scripts, installers, and old analysis clutter so the repo stays focused on the files needed to run the experiment and store results.

## Running The Experiment

1. Install PsychoPy and the Python dependencies used by `av_spatiotemporal_study.py`.
2. Confirm the stimulus assets are present in `20_stimuli/`.
3. Run `av_spatiotemporal_study.py` from PsychoPy or with Python in the study directory.
4. Collect outputs from `data/<participant_pid>/`.

### Linux (PipeWire + Xorg) quick setup

For timing-critical sessions on Linux:

1. Log into an Xorg session.
2. Verify your intended output sink is active and not HDMI by mistake.
3. Run with explicit audio overrides when needed:
   - `AV_STUDY_AUDIO_LIBS=ptb,sounddevice,pygame`
   - `AV_STUDY_AUDIO_DEVICE=default`
   - `AV_STUDY_AUDIO_LATENCY_MODE=2`
4. Start the study and pass the startup audio preflight tone gate.

Useful runtime overrides:

- `AV_STUDY_DIR=/path/to/study_root` to force the working directory.
- `AV_STUDY_STRICT_XORG=1` to fail hard on Wayland.
- `AV_STUDY_SKIP_AUDIO_PREFLIGHT=1` only for non-collection smoke tests.

## Timing Note

`av_spatiotemporal_study.py` currently includes a `DEBUG_OVERLAY` setting. Leave it on for layout checks, but turn it off before production-style timing runs if you want the cleanest frame-timing numbers.

## Output

Each run creates a timestamped participant folder under [`data`](./data) containing:

- `participant_*_stimulus.csv`
- `participant_*_responses.csv`
- `participant_*_trials.csv`

Use [`validate_data.py`](./validate_data.py) after a run to sanity-check the saved data.
