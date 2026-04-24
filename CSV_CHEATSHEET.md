# CSV Cheat Sheet

This is the fast version of the project docs.

Use this when you want to answer questions like:

- What happened on this exact appearance?
- What happened on this exact keypress?
- How did this whole trial go?
- Was timing stable?


## Which file should I open?

- `participant_<PID>_stimulus.csv`
  One row per stimulus appearance.
  Use this for onset times, SOAs, corners, and whether a specific appearance got a response.

- `participant_<PID>_responses.csv`
  One row per recorded keypress.
  Use this for hit vs false alarm classification and what was on screen when the key was pressed.

- `participant_<PID>_trials.csv`
  One row per trial.
  Use this for quick trial-level performance and frame-timing quality checks.


## Stimulus CSV

Think of this file as:

"What did the script schedule and what actually happened for each appearance?"

### Identity columns

- `appearance_id`
  Internal appearance label like `PT_1` or `NPD_3`.

- `role`
  `PT`, `NPT`, `PD`, or `NPD`.

- `object_id`
  Internal stimulus ID like `animate_obj_4`.

- `object_name`
  Readable label like `cow (moo)`.

- `category`
  `animate` or `inanimate`.

### Spatial and design columns

- `corner`
  Where it appeared.

- `target_key`
  Correct numpad key for target-category items.

- `sound_lead_sec`
  Intended sound lead relative to visual peak.

### Actual timing columns

- `fade_in_start`
  Actual visual onset.

- `peak_opacity_time`
  Actual time the image reached full opacity.

- `fade_out_end`
  Actual time the image disappeared.

- `sound_start`
  Actual logged sound onset.

- `sound_end`
  Actual logged sound offset.

- `response_deadline`
  End of the valid response window.

### Scheduled timing columns

- `scheduled_fade_in_start`
- `scheduled_peak_opacity_time`
- `scheduled_fade_out_end`
- `scheduled_sound_start`
- `scheduled_sound_end`
- `requested_sound_start`

The `scheduled_*` fields are the pre-run planned values.
`requested_sound_start` is the runtime launch request captured on the firing frame.
Use these fields to compare planned, requested, and recorded timing.

### Timing quality columns

- `visual_onset_error_ms`
  Actual visual onset minus scheduled visual onset, in milliseconds.

- `sound_onset_error_ms`
  Logged sound timestamp minus scheduled sound onset, in milliseconds.
  On `ptb_preflight` rows this is the requested PTB launch time versus schedule, not a microphone-confirmed speaker onset.

- `av_sync_error_ms`
  Change in recorded sound-vs-visual alignment relative to the planned SOA.
  This is the best column to inspect when you want to catch a late visual flip against an on-time PTB sound request.

- `sound_start_source`
  What kind of sound timestamp this is:
  - `ptb_preflight`: PTB scheduled pre-flip timestamp
  - `fallback_postflip`: fallback timestamp taken after `play()`
  - `failed`: sound was supposed to happen but failed
  - blank: silent item

### Response columns

- `response_made`
  Whether this appearance got a stored response.

- `response_key`
  Which key was stored for this appearance.

- `response_time`
  Time of the stored response.

- `rt_from_fade_in`
  `response_time - fade_in_start`

- `response_in_window`
  Whether the stored response was inside the valid window.

- `response_correct`
  Whether the response matched the correct target corner.

### Session columns

- `participant_pid`
- `block_type`
- `trial_num`
- `is_practice`
- `active_pt_name`
- `active_pt_friendly`


## Responses CSV

Think of this file as:

"What did the participant press, and what was happening at that exact moment?"

### Keypress identity

- `keypress_time`
  When the keypress happened.

- `key_pressed`
  Which key was pressed.

- `response_type`
  `hit` or a false-alarm label like `fa_late`.

### Matched target columns

- `hit_object`
- `hit_role`
- `hit_corner`
- `hit_sound_lead_sec`

These describe the matched target event if the keypress can be tied to one.

### Reaction time columns

- `rt_from_fade_in`
  RT from actual visual onset.

- `rt_from_sound_start`
  RT from logged sound onset, if applicable.

- `hit_sound_start_source`
  Whether that RT came from a `ptb_preflight` or `fallback_postflip` sound timestamp.

- `response_in_window`
  Whether that matched response was within the valid window.

### Scene snapshot columns

- `fa_pre_visual`
  Useful context for false alarms.

- `most_visible_object`
- `most_visible_role`
- `most_visible_opacity`
- `most_visible_corner`
- `most_visible_sound_lead_sec`

These describe the most visually salient item at keypress time.

- `sound_playing_object`
- `sound_playing_role`

These describe the sound event that was active at keypress time, if any.

- `sounds_in_last_3sec`
  Short text history of recently fired sounds.

- `all_visible_at_keypress`
  Text summary of everything visible when the key was pressed.

### Session columns

- `participant_pid`
- `block_type`
- `trial_num`
- `is_practice`
- `active_pt_name`
- `active_pt_friendly`


## Trials CSV

Think of this file as:

"How did this whole trial go?"

### Trial identity

- `participant_pid`
- `block_type`
- `trial_num`
- `is_practice`
- `active_pt_name`
- `active_pt_friendly`
- `active_pt_soa`
- `pt_corner_this_trial`

### Trial composition

- `n_pt_appearances`
- `n_npt_appearances`
- `n_pd_appearances`
- `n_npd_appearances`
- `total_appearances`

### Performance summary

- `trial_duration_sec`
- `n_hits`
- `n_false_alarms`
- `pt_hit_rate`
- `npt_hit_rate`

### Frame-timing summary

- `measured_refresh_hz`
  Estimated refresh rate from recorded frame intervals in that trial.

- `mean_frame_ms`
- `median_frame_ms`
- `max_frame_ms`

- `n_long_frames`
  Count of frames longer than the configured threshold.


## Fast Rules Of Thumb

- If you care about one specific image or sound event, open `stimulus.csv`.
- If you care about one specific button press, open `responses.csv`.
- If you care about whether a whole trial was clean or messy, open `trials.csv`.
- If you compare RTs from sound, filter on `hit_sound_start_source == ptb_preflight` when you want the cleanest like-for-like rows.
- If you see `failed` in `sound_start_source`, treat that row as a sound failure, not a valid sound onset.
- If `n_long_frames` is high or `max_frame_ms` spikes, be careful interpreting that trial's timing.
- If you care about AV desync, check `av_sync_error_ms` together with `n_long_frames`; `sound_onset_error_ms` alone can look clean on PTB rows.
