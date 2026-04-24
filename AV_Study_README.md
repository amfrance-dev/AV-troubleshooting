# AV Study README

This guide explains the AV Spatiotemporal Awareness Study in simple language.

This file is meant to help you understand:

- what this project does
- which files matter
- how to run the study
- what the code is doing during each trial
- how timing works
- what gets saved in each CSV file
- how to check whether the saved data looks correct


## 1. What This Study Is

This project runs a visual and audio attention experiment.

A participant watches the screen while objects appear in one of the four screen corners:

- top left
- top right
- bottom left
- bottom right

Some objects also make a sound.

The participant's job is to press the matching numpad key when they see the target object in a corner.

The target changes depending on the current block and the currently active privileged target.


## 2. The Most Important Files

These are the files most people will care about:

- [`av_spatiotemporal_study.py`](C:\Users\Canine\Downloads\AV_Spatiotemporal_Study\av_spatiotemporal_study.py)
  This is the main experiment script. It runs the study, shows stimuli, collects responses, and saves data.

- [`validate_data.py`](C:\Users\Canine\Downloads\AV_Spatiotemporal_Study\validate_data.py)
  This checks whether the saved CSV files are internally consistent. It is the "quality control" script.

- [`run_debug_session.py`](C:\Users\Canine\Downloads\AV_Spatiotemporal_Study\run_debug_session.py)
  This is the guided debug-run helper. It launches the study, validates the newest participant folder, and writes a debug review template.

- [`clean_audio_set.py`](C:\Users\Canine\Downloads\AV_Spatiotemporal_Study\clean_audio_set.py)
  This creates a cleaned offline copy of each experiment WAV so the study can prefer a uniform audio set.

- [`analyze.py`](C:\Users\Canine\Downloads\AV_Spatiotemporal_Study\analyze.py)
  This is the analysis script. It is for later summaries and plots, not for checking whether the raw data is valid.

- [`data`](C:\Users\Canine\Downloads\AV_Spatiotemporal_Study\data)
  This folder stores one subfolder per participant/session.

- [`20_stimuli`](C:\Users\Canine\Downloads\AV_Spatiotemporal_Study\20_stimuli)
  This folder holds the image and sound files used during the experiment.

- [`AV_Study_Data_README.pdf`](C:\Users\Canine\Downloads\AV_Spatiotemporal_Study\AV_Study_Data_README.pdf)
  This is a separate project document about the data.

- [`CSV_CHEATSHEET.md`](C:\Users\Canine\Downloads\AV_Spatiotemporal_Study\CSV_CHEATSHEET.md)
  This is the fast reference for the three CSV outputs and the most important timing columns.


## 3. What Happens When You Run `av_spatiotemporal_study.py`

When you run the main experiment script, it does the following:

1. Picks the working folder.
2. Sets PsychoPy audio preferences.
3. Loads the stimulus pools.
4. Creates a participant ID based on the current date and time.
5. Creates a data folder for that participant.
6. Creates three CSV files:
   - stimulus file
   - responses file
   - trials file
7. Randomly assigns privileged targets.
8. Randomly assigns privileged distractors for each block.
9. Decides the block order:
   - animate then inanimate
   - or inanimate then animate
10. Shows a debug screen listing the assigned targets and distractors.
11. Shows the instructions screen.
12. Runs the practice trials.
13. Runs the real trials.
14. Shows a final summary screen.


## 4. The Structure of the Experiment

There are two block types:

- `animate`
- `inanimate`

There are four main stimulus roles:

- `PT`
  Privileged Target. This is the important target item. It has a fixed sound lead time for the whole experiment.

- `NPT`
  Non-Privileged Target. Same target category as the block, but no sound lead is assigned.

- `PD`
  Privileged Distractor. This is a distractor with sound. Its sound lead time is random for each appearance.

- `NPD`
  Non-Privileged Distractor. This is a distractor without sound.

In simple terms:

- PT and NPT are target-category items
- PD and NPD are distractor-category items


## 5. Numpad Response Mapping

The script expects the participant to use these numpad keys:

- `4` = top left
- `5` = top right
- `1` = bottom left
- `2` = bottom right

If the object appears in the top right corner, the correct response is `num_5`.


## 6. Important Functions in `av_spatiotemporal_study.py`

This section explains the main functions in plain English.

### `friendly_name(item)`

Turns an internal stimulus item into a human-readable name such as:

- `cow (moo)`
- `camera (click)`

This is used for logs and saved CSV files.


### `get_path(category, obj_num, file_type='img')`

Builds the file path for either:

- the object's image
- the object's sound

This keeps the script from hard-coding every file path by hand.


### `normalize_audio(snd_path)`

Uses `pydub` to create a normalized copy of a sound file so volume is more consistent across stimuli.

If `pydub` is not installed, the script falls back to the original sound file.


### `assign_pt_group()`

Randomly chooses the privileged targets for the participant.

It picks:

- 2 animate PTs
- 2 inanimate PTs

Each PT gets a fixed sound lead time that stays attached to that PT for the full experiment.


### `assign_pd_group(pt_group, block_type)`

Chooses privileged distractors for a given block.

If the block is `animate`, then distractors come from the inanimate pool.

If the block is `inanimate`, then distractors come from the animate pool.


### `load_background()`

Creates animated background noise from the source blob image.

This is purely for the visual background and not the actual target logic.


### `build_trial_appearances(block_type, pt_group, pd_group, npd_pool, active_pt_name)`

Decides how many appearances the trial will contain and which items fill those roles.

This is where the script decides things like:

- how many PT appearances
- how many NPT appearances
- how many PD appearances
- how many NPD appearances

This function decides the trial ingredients, but not their exact timing yet.


### `build_timeline(appearances, block_type)`

This is one of the most important functions in the whole project.

It takes the planned appearances and schedules them in time.

This function decides:

- when each stimulus starts fading in
- when each stimulus reaches peak opacity
- when each stimulus fades out
- when each sound starts
- when each sound ends
- which corner each item goes in

It also enforces spacing rules, such as:

- no overlapping visuals in the same corner
- no audio overlap closer than the allowed gap
- no negative sound start times
- minimum spacing between visual onsets
- minimum spacing between repeats of the same item


### `validate_timeline(timeline)`

Checks the generated timeline for obvious problems, especially:

- same-corner visual overlap
- audio overlap

This is an internal schedule check before the trial runs.


### `save_trial_data(...)`

Writes one row per appearance into the stimulus CSV.

This file is the detailed "what happened in the trial" file.


### `snapshot_scene(timeline, t)`

Looks at the exact moment a key was pressed and summarizes what was on screen and what sound was playing.

This is used to make the response log more informative.


### `classify_fa_type(...)`

Classifies false alarms into types such as:

- `fa_wrong_corner`
- `fa_late`
- `fa_no_target`
- `fa_empty`


### `save_trial_summary(...)`

Writes one row into the trials CSV.

This is a trial-level summary instead of an appearance-level or keypress-level log.


### `save_response(...)`

Writes one row into the responses CSV every time the participant presses a response key.


### `show_debug_screen(...)`

Shows a readable summary of the participant's assigned PTs and PDs before the experiment starts.

This is mostly for the experimenter.


### `run_trial(...)`

This is the core trial runner.

It:

- builds appearances
- builds the timeline
- runs the clock
- draws the background
- plays sounds
- draws images
- watches for keypresses
- classifies hits and false alarms
- saves rows to the CSV files


### `make_pt_sequence(block_type, pt_group, n_trials)`

Creates the sequence of active PTs across a block.

This is how the script decides which PT is the active target for each trial in a block.


## 7. How Timing Works

Timing is extremely important in this study.

The script uses several timing values:

- fade in duration
- peak hold duration
- fade out duration
- sound duration
- response window
- audio gap
- visual onset gap
- same-item repeat gap

### Visual timing

Each visual stimulus has three phases:

1. fade in
2. hold at peak opacity
3. fade out

The script saves:

- `fade_in_start`
- `peak_opacity_time`
- `fade_out_end`

These are the actual stored visual times for that appearance.

The stimulus CSV can also store the original planned values separately using:

- `scheduled_fade_in_start`
- `scheduled_peak_opacity_time`
- `scheduled_fade_out_end`

So a single appearance has a full visible time window from `fade_in_start` to `fade_out_end`.


### Sound timing

If a stimulus has sound, the sound lead is measured relative to the visual peak, not relative to the fade-in start.

That means this equation should be true:

`peak_opacity_time - sound_start = sound_lead_sec`

The stimulus CSV can also store the planned audio window separately using:

- `scheduled_sound_start`
- `scheduled_sound_end`

Example:

- `peak_opacity_time = 15.558`
- `sound_start = 14.273`
- difference = `1.285`

So if `sound_lead_sec` is about `1.282`, that is correct within normal rounding tolerance.


### Response timing

The reaction time from visual onset is:

`response_time - fade_in_start`

Example:

- `response_time = 7.9292`
- `fade_in_start = 7.216`
- RT = `0.7132`

That is why the stored reaction time should match:

`rt_from_fade_in = response_time - fade_in_start`


### Current spacing rules

The current code now enforces:

- a minimum gap between any two visual onsets
- a minimum gap between repeated appearances of the same item
- a minimum gap between audio windows

This means stimuli can still overlap in total visible duration, but they should not begin too close together.


## 8. Current CSV Output Files

Each run creates three CSV files in the participant folder.

Example folder:

[`data\20260402_140141`](C:\Users\Canine\Downloads\AV_Spatiotemporal_Study\data\20260402_140141)


## 9. Stimulus CSV

File name pattern:

- `participant_<PID>_stimulus.csv`

This file contains one row per appearance.

### Stimulus CSV columns

- `appearance_id`
  Internal label for that appearance, such as `PT_1` or `NPD_3`.

- `role`
  One of `PT`, `NPT`, `PD`, or `NPD`.

- `object_id`
  Internal item name, such as `animate_obj_4`.

- `object_name`
  Friendly item name, such as `cow (moo)`.

- `category`
  Either `animate` or `inanimate`.

- `sound_lead_sec`
  The lead time for sounded items. Blank for silent items.

- `corner`
  Which corner the stimulus appeared in.

- `target_key`
  The correct numpad key for target-category items. Blank for distractors.

- `fade_in_start`
  When the image began to appear.

- `peak_opacity_time`
  When the image reached full brightness.

- `fade_out_end`
  When the image fully disappeared.

- `sound_start`
  When the sound started. Blank for silent items.

- `sound_end`
  When the sound ended. Blank for silent items.

- `response_deadline`
  The end of the allowed response window for target-category items.

- `scheduled_fade_in_start`
  The originally planned fade-in start before actual display timing was recorded.

- `scheduled_peak_opacity_time`
  The originally planned peak time before actual display timing was recorded.

- `scheduled_fade_out_end`
  The originally planned fade-out end before actual display timing was recorded.

- `scheduled_sound_start`
  The originally planned sound start before actual sound timing was recorded.

- `scheduled_sound_end`
  The originally planned sound end before actual sound timing was recorded.

- `requested_sound_start`
  The sound start time the runtime requested on that frame.
  On `ptb_preflight` rows this is the PTB launch target; on `fallback_postflip` rows it is the pre-flip request that the fallback path tried to honor.

- `visual_onset_error_ms`
  Difference between actual and scheduled visual onset in milliseconds.

- `sound_onset_error_ms`
  Difference between the logged sound timestamp and the scheduled sound onset in milliseconds.
  For `ptb_preflight` rows this reflects the requested PTB launch time, not a microphone-confirmed speaker onset.

- `av_sync_error_ms`
  Change in recorded sound-vs-visual alignment relative to the planned SOA.
  This is the best per-event field for spotting a late visual flip against an otherwise on-time sound request.

- `sound_start_source`
  Explains what kind of sound timestamp was stored.
  Current values are:
  - `ptb_preflight`
  - `fallback_postflip`
  - `failed`
  - blank for silent items

- `response_made`
  Whether that appearance received a stored response.

- `response_key`
  Which key was recorded for that appearance, if any.

- `response_time`
  When the response was recorded for that appearance.

- `rt_from_fade_in`
  `response_time - fade_in_start`

- `response_in_window`
  Whether the response landed in the allowed response window.

- `response_correct`
  Whether the response matched the correct target corner.

- `participant_pid`
  Participant/session ID.

- `block_type`
  The block type for that trial.

- `trial_num`
  Trial number.

- `is_practice`
  `True` for practice, `False` for real trials.

- `active_pt_name`
  Internal name of the currently active privileged target.

- `active_pt_friendly`
  Friendly name of the active privileged target.


## 10. Responses CSV

File name pattern:

- `participant_<PID>_responses.csv`

This file contains one row per recorded keypress.

### Responses CSV columns

- `keypress_time`
  When the keypress happened.

- `key_pressed`
  Which key the participant pressed.

- `response_type`
  Usually `hit` or one of the false alarm labels.

- `hit_object`
  Friendly name of the matched target if the press counted as a hit.

- `hit_role`
  Whether the hit was on a `PT` or `NPT`.

- `hit_corner`
  Corner of the matched target.

- `hit_sound_lead_sec`
  Sound lead of the matched item, if it had one.

- `rt_from_fade_in`
  Keypress time minus target fade-in start.

- `rt_from_sound_start`
  Keypress time minus target sound start, if there was sound.

- `hit_sound_start_source`
  The timing source for the matched target's sound timestamp.
  This helps you tell apart PTB preflip audio timing from fallback timing.

- `response_in_window`
  Whether the matched response was inside the valid response window.

- `fa_pre_visual`
  Helps describe whether a false alarm happened before the image reached peak visibility.

- `most_visible_object`
  The most visually prominent object at the moment of the keypress.

- `most_visible_role`
  Its role.

- `most_visible_opacity`
  Its opacity at the moment of the keypress.

- `most_visible_corner`
  Its corner.

- `most_visible_sound_lead_sec`
  Its sound lead, if any.

- `sound_playing_object`
  Which object's sound was playing at the keypress moment, if any.

- `sound_playing_role`
  Role of the sound-playing object.

- `sounds_in_last_3sec`
  A text list of sounds that fired in the last 3 seconds before the keypress.

- `sounds_in_last_5sec` or `recent_sounds`
  Legacy headers from older runs. The validator can still normalize these.

- `all_visible_at_keypress`
  Text summary of everything visible at the keypress moment.

- `participant_pid`
  Participant/session ID.

- `block_type`
  Block type for that trial.

- `trial_num`
  Trial number.

- `is_practice`
  Practice or real.

- `active_pt_name`
  Active PT internal name.

- `active_pt_friendly`
  Active PT friendly name.


## 11. Trials CSV

File name pattern:

- `participant_<PID>_trials.csv`

This file contains one row per trial.

### Trials CSV columns

- `participant_pid`
  Participant/session ID.

- `block_type`
  `animate` or `inanimate`

- `trial_num`
  Trial number.

- `is_practice`
  Practice or real.

- `active_pt_name`
  Active PT internal name for that trial.

- `active_pt_friendly`
  Friendly active PT name.

- `active_pt_soa`
  The active PT's sound lead.

- `pt_corner_this_trial`
  Corner of the PT in that trial.

- `n_pt_appearances`
  Number of PT rows in that trial.

- `n_npt_appearances`
  Number of NPT rows in that trial.

- `n_pd_appearances`
  Number of PD rows in that trial.

- `n_npd_appearances`
  Number of NPD rows in that trial.

- `total_appearances`
  Total number of stimulus rows in that trial.

- `trial_duration_sec`
  Total duration used for that trial.

- `n_hits`
  Number of valid target responses in that trial.

- `n_false_alarms`
  Number of false alarms in that trial.

- `pt_hit_rate`
  Hit rate for PT appearances in that trial.

- `npt_hit_rate`
  Hit rate for NPT appearances in that trial.

- `measured_refresh_hz`
  The effective refresh rate estimated from the recorded frame intervals in that trial.

- `mean_frame_ms`
  Mean frame duration for that trial in milliseconds.

- `median_frame_ms`
  Median frame duration for that trial in milliseconds.

- `max_frame_ms`
  Longest recorded frame duration for that trial in milliseconds.

- `n_long_frames`
  Number of frames that were longer than the configured long-frame threshold.


## 12. How To Run the Study

### Optional: clean the audio set first

If you want a uniform offline audio set before data collection, run:

```powershell
python clean_audio_set.py --force
```

This writes cleaned copies into each stimulus sound folder under `_cleaned`.
`av_spatiotemporal_study.py` will prefer those cleaned WAV files when they exist.

### Before you begin

Make sure:

- the stimuli folder is present
- PsychoPy is installed
- the computer has a working numpad
- audio is working
- the correct monitor is selected

### To run the study

Open the project folder and run:

```powershell
python av_spatiotemporal_study.py
```

If you normally use PsychoPy's runner instead of plain Python, that is fine too, as long as it runs the same file.


## 13. How To Run the Validator

After collecting data, run:

```powershell
python validate_data.py
```

By default, this checks the most recent participant folder inside `data`.

You can also point to a specific folder:

```powershell
python validate_data.py 20260402_140141
```

If you want to check whether your final study design was followed, you can also add design expectations:

```powershell
python validate_data.py --design-trials-per-block 30 --design-pt-trials 15
```


## 14. How To Run a Guided Debug Session

If you want one structured debug pass, run:

```powershell
python run_debug_session.py
```

This helper will:

- show the current important config values from `av_spatiotemporal_study.py`
- pause so you can start your screen or phone recording
- launch the study
- detect the participant folder created by that run
- run `validate_data.py` on it
- write `debug_review.md` into that participant folder

The `debug_review.md` file is meant to help you turn one run into a useful bug list.


## 15. What the Validation Report Does

The validator checks whether the saved data looks logically correct.

It compares the stimulus, response, and trial files against each other.

It looks for problems such as:

- sound lead values not matching the actual sound and peak times
- reaction times that do not match the stored timestamps
- same-corner visual overlaps
- audio overlaps that are too close
- visual onsets that are too close together
- repeated appearances of the same item that happen too close together
- trial summary numbers that do not match the raw data
- negative sound start times
- missing or mismatched hit records

The validator prints the results to the terminal and also writes:

- `validation_report.txt`

inside the participant folder.


## 16. Why Validation Matters

When the study becomes larger, checking every row by hand becomes unrealistic.

For example, if you eventually run:

- 30 animate trials
- 30 inanimate trials
- 15 trials per PT

then manual row-by-row checking becomes slow and easy to mess up.

The validator is useful because it lets you:

- run the experiment
- check for structural problems quickly
- focus only on the flagged trials


## 17. Common Things To Double-Check

If something feels off, these are good first questions:

- Did `peak_opacity_time - sound_start` really equal `sound_lead_sec`?
- Did `response_time - fade_in_start` really equal `rt_from_fade_in`?
- Did the participant's key match the corner?
- Did the final trial counts match the intended design?
- Did any sound begin before time zero?
- Did any two stimuli begin too close together?
- Did the same item repeat too quickly?
- Did the trial summary match the raw stimulus and response rows?


## 18. Good Beginner Workflow

If you are new to this project, a safe workflow is:

1. Run a short test session.
2. Open the new participant folder in `data`.
3. Run `python validate_data.py`.
4. Read `validation_report.txt`.
5. If the report shows errors, inspect only those trials first.
6. After the validator looks good, move on to deeper analysis with `analyze.py`.

For a more guided version of that workflow, use `python run_debug_session.py`.


## 19. Final Summary

If you only remember a few things, remember these:

- `av_spatiotemporal_study.py` runs the experiment.
- Each run creates 3 CSV files.
- `stimulus.csv` is appearance-level data.
- `responses.csv` is keypress-level data.
- `trials.csv` is trial-level summary data.
- Timing is built around visual onset, peak opacity, fade-out end, and sound lead relative to peak.
- `validate_data.py` is the first tool to use after a run.
- `validation_report.txt` is the quick quality-control report saved into the participant folder.
