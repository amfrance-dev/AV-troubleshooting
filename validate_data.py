import argparse
import csv
import math
import os
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_STUDY_DIR = Path(r"Z:\Experiments\Anthony\AV_Spatiotemporal_Study")
if not DEFAULT_STUDY_DIR.exists():
    DEFAULT_STUDY_DIR = Path(r"C:\Users\Canine\Downloads\AV_Spatiotemporal_Study")
if not DEFAULT_STUDY_DIR.exists():
    DEFAULT_STUDY_DIR = Path(__file__).resolve().parent

DATA_DIR = DEFAULT_STUDY_DIR / "data"

STIM_ALIASES = {
    "appearance_id": "appearance_id",
    "app_id": "appearance_id",
    "role": "role",
    "stimulus_role": "role",
    "object_id": "object_id",
    "item_name": "object_id",
    "object_name": "object_name",
    "item_friendly": "object_name",
    "category": "category",
    "item_category": "category",
    "sound_lead_sec": "sound_lead_sec",
    "soa_sec": "sound_lead_sec",
    "corner": "corner",
    "target_key": "target_key",
    "correct_key": "target_key",
    "fade_in_start": "fade_in_start",
    "start_vis": "fade_in_start",
    "peak_opacity_time": "peak_opacity_time",
    "peak_vis": "peak_opacity_time",
    "fade_out_end": "fade_out_end",
    "end_vis": "fade_out_end",
    "sound_start": "sound_start",
    "start_snd": "sound_start",
    "sound_end": "sound_end",
    "end_snd": "sound_end",
    "response_deadline": "response_deadline",
    "response_window_end": "response_deadline",
    "scheduled_fade_in_start": "scheduled_fade_in_start",
    "scheduled_peak_opacity_time": "scheduled_peak_opacity_time",
    "scheduled_fade_out_end": "scheduled_fade_out_end",
    "scheduled_sound_start": "scheduled_sound_start",
    "scheduled_sound_end": "scheduled_sound_end",
    "requested_sound_start": "requested_sound_start",
    "visual_onset_error_ms": "visual_onset_error_ms",
    "sound_onset_error_ms": "sound_onset_error_ms",
    "av_sync_error_ms": "av_sync_error_ms",
    "sound_start_source": "sound_start_source",
    "response_made": "response_made",
    "response_key": "response_key",
    "response_time": "response_time",
    "rt_from_fade_in": "rt_from_fade_in",
    "rt_from_visual_onset": "rt_from_fade_in",
    "response_in_window": "response_in_window",
    "response_correct": "response_correct",
    "participant_pid": "participant_pid",
    "block_type": "block_type",
    "trial_num": "trial_num",
    "is_practice": "is_practice",
    "active_pt_name": "active_pt_name",
    "active_pt_friendly": "active_pt_friendly",
}

RESP_ALIASES = {
    "keypress_time": "keypress_time",
    "response_time": "keypress_time",
    "key_pressed": "key_pressed",
    "response_key": "key_pressed",
    "response_type": "response_type",
    "hit_object": "hit_object",
    "hit_item": "hit_object",
    "hit_role": "hit_role",
    "hit_corner": "hit_corner",
    "hit_sound_lead_sec": "hit_sound_lead_sec",
    "hit_soa": "hit_sound_lead_sec",
    "rt_from_fade_in": "rt_from_fade_in",
    "rt_from_visual_onset": "rt_from_fade_in",
    "rt_from_sound_start": "rt_from_sound_start",
    "rt_from_sound_onset": "rt_from_sound_start",
    "hit_sound_start_source": "hit_sound_start_source",
    "response_in_window": "response_in_window",
    "fa_pre_visual": "fa_pre_visual",
    "most_visible_object": "most_visible_object",
    "salient_item": "most_visible_object",
    "most_visible_role": "most_visible_role",
    "salient_role": "most_visible_role",
    "most_visible_opacity": "most_visible_opacity",
    "salient_opacity": "most_visible_opacity",
    "most_visible_corner": "most_visible_corner",
    "most_visible_sound_lead_sec": "most_visible_sound_lead_sec",
    "salient_soa": "most_visible_sound_lead_sec",
    "sound_playing_object": "sound_playing_object",
    "sound_playing_now": "sound_playing_object",
    "sound_playing_role": "sound_playing_role",
    "sounds_in_last_5sec": "recent_sounds",
    "sounds_in_last_3sec": "recent_sounds",
    "recent_sounds": "recent_sounds",
    "all_visible_at_keypress": "all_visible_at_keypress",
    "all_visible": "all_visible_at_keypress",
    "participant_pid": "participant_pid",
    "block_type": "block_type",
    "trial_num": "trial_num",
    "is_practice": "is_practice",
    "active_pt_name": "active_pt_name",
    "active_pt_friendly": "active_pt_friendly",
}

TRIAL_ALIASES = {
    "participant_pid": "participant_pid",
    "block_type": "block_type",
    "trial_num": "trial_num",
    "is_practice": "is_practice",
    "active_pt_name": "active_pt_name",
    "active_pt_friendly": "active_pt_friendly",
    "active_pt_soa": "active_pt_soa",
    "pt_corner_this_trial": "pt_corner_this_trial",
    "n_pt_appearances": "n_pt_appearances",
    "n_npt_appearances": "n_npt_appearances",
    "n_pd_appearances": "n_pd_appearances",
    "n_npd_appearances": "n_npd_appearances",
    "total_appearances": "total_appearances",
    "trial_duration_sec": "trial_duration_sec",
    "n_hits": "n_hits",
    "n_false_alarms": "n_false_alarms",
    "pt_hit_rate": "pt_hit_rate",
    "npt_hit_rate": "npt_hit_rate",
    "measured_refresh_hz": "measured_refresh_hz",
    "mean_frame_ms": "mean_frame_ms",
    "median_frame_ms": "median_frame_ms",
    "max_frame_ms": "max_frame_ms",
    "n_long_frames": "n_long_frames",
}

REQUIRED_STIM = {
    "appearance_id", "role", "object_id", "object_name", "category",
    "corner", "fade_in_start", "peak_opacity_time", "fade_out_end",
    "response_made", "participant_pid", "block_type", "trial_num", "is_practice",
}
REQUIRED_RESP = {
    "keypress_time", "key_pressed", "response_type",
    "participant_pid", "block_type", "trial_num", "is_practice",
}
REQUIRED_TRIALS = {
    "participant_pid", "block_type", "trial_num", "is_practice",
    "n_pt_appearances", "n_npt_appearances", "n_pd_appearances", "n_npd_appearances",
    "total_appearances", "trial_duration_sec", "n_hits", "n_false_alarms",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate AV study participant CSV outputs."
    )
    parser.add_argument(
        "participant",
        nargs="?",
        help="Participant folder name or full path. Defaults to the latest folder in data/.",
    )
    parser.add_argument("--data-dir", default=str(DATA_DIR), help="Root data directory.")
    parser.add_argument("--visual-gap", type=float, default=0.25, help="Minimum allowed gap between any two visual onsets.")
    parser.add_argument("--same-item-gap", type=float, default=0.75, help="Minimum allowed quiet gap between repeated appearances of the same item.")
    parser.add_argument("--audio-gap", type=float, default=0.2, help="Minimum allowed gap between audio windows.")
    parser.add_argument("--timing-tol", type=float, default=0.02, help="Tolerance for timing equality checks in seconds.")
    parser.add_argument("--refresh-hz", type=float, default=120.0, help="Assumed display refresh rate when converting onset drift thresholds from frames to milliseconds.")
    parser.add_argument("--warn-visual-onset-frames", type=float, default=1.0, help="Warn when visual onset drift exceeds this many frames.")
    parser.add_argument("--error-visual-onset-frames", type=float, default=2.0, help="Error when visual onset drift exceeds this many frames.")
    parser.add_argument("--warn-sound-onset-frames", type=float, default=1.0, help="Warn when sound onset drift exceeds this many frame-equivalents.")
    parser.add_argument("--error-sound-onset-frames", type=float, default=2.5, help="Error when sound onset drift exceeds this many frame-equivalents.")
    parser.add_argument("--design-trials-per-block", type=int, default=None, help="Expected number of real trials per block.")
    parser.add_argument("--design-pt-trials", type=int, default=None, help="Expected number of real trials per PT.")
    parser.add_argument(
        "--write-report",
        dest="write_report",
        action="store_true",
        default=True,
        help="Write a validation report text file into the participant folder (default: on).",
    )
    parser.add_argument(
        "--no-write-report",
        dest="write_report",
        action="store_false",
        help="Skip writing the validation report text file.",
    )
    return parser.parse_args()


def pick_participant_dir(data_dir, participant_arg):
    if participant_arg:
        candidate = Path(participant_arg)
        if candidate.exists():
            return candidate
        candidate = Path(data_dir) / participant_arg
        if candidate.exists():
            return candidate
        raise FileNotFoundError(f"Could not find participant folder: {participant_arg}")

    folders = sorted(
        [p for p in Path(data_dir).iterdir() if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
    )
    if not folders:
        raise FileNotFoundError(f"No participant folders found in {data_dir}")
    return folders[-1]


def load_csv(path, alias_map, required_cols):
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    raw_columns = rows[0].keys() if rows else []
    canonical_rows = []
    present = set()
    for row in rows:
        canonical = {}
        for key, value in row.items():
            target = alias_map.get(key)
            if target:
                canonical[target] = value
                present.add(target)
        canonical_rows.append(canonical)

    missing = sorted(required_cols - present)
    return canonical_rows, list(raw_columns), missing


def to_float(value):
    if value in (None, "", "None", "nan"):
        return None
    return float(value)


def to_int(value):
    if value in (None, "", "None", "nan"):
        return None
    return int(float(value))


def to_bool(value):
    if isinstance(value, bool):
        return value
    if value in (None, "", "None"):
        return None
    text = str(value).strip().lower()
    if text == "true":
        return True
    if text == "false":
        return False
    return None


def approx_equal(a, b, tol):
    return a is not None and b is not None and abs(a - b) <= tol


def trial_key(row):
    return (
        row.get("participant_pid", ""),
        row.get("block_type", ""),
        to_int(row.get("trial_num")),
        to_bool(row.get("is_practice")),
    )


def format_trial_key(key):
    pid, block_type, trial_num, is_practice = key
    label = "practice" if is_practice else "real"
    return f"{pid} | {block_type} | trial {trial_num} | {label}"


def add_issue(issues, severity, code, message, trial=None):
    issues.append({
        "severity": severity,
        "code": code,
        "message": message,
        "trial": trial,
    })


def frames_to_ms(frames, refresh_hz):
    return (frames / refresh_hz) * 1000.0


def timing_threshold_summary(args):
    warn_visual_ms = frames_to_ms(args.warn_visual_onset_frames, args.refresh_hz)
    error_visual_ms = frames_to_ms(args.error_visual_onset_frames, args.refresh_hz)
    warn_sound_ms = frames_to_ms(args.warn_sound_onset_frames, args.refresh_hz)
    error_sound_ms = frames_to_ms(args.error_sound_onset_frames, args.refresh_hz)
    return [
        f"Refresh assumption: {args.refresh_hz:.1f} Hz",
        f"Visual onset drift warn: > {args.warn_visual_onset_frames:.2f} frame(s) ({warn_visual_ms:.3f} ms)",
        f"Visual onset drift error: > {args.error_visual_onset_frames:.2f} frame(s) ({error_visual_ms:.3f} ms)",
        f"AV sync drift warn: > {args.warn_sound_onset_frames:.2f} frame-equivalent(s) ({warn_sound_ms:.3f} ms)",
        f"AV sync drift error: > {args.error_sound_onset_frames:.2f} frame-equivalent(s) ({error_sound_ms:.3f} ms)",
    ]


def validate_rows(stim_rows, resp_rows, trial_rows, args):
    issues = []
    legacy_distractor_response_window = []
    fallback_sound_rows = []
    warn_visual_onset_error_ms = frames_to_ms(args.warn_visual_onset_frames, args.refresh_hz)
    error_visual_onset_error_ms = frames_to_ms(args.error_visual_onset_frames, args.refresh_hz)
    warn_sound_onset_error_ms = frames_to_ms(args.warn_sound_onset_frames, args.refresh_hz)
    error_sound_onset_error_ms = frames_to_ms(args.error_sound_onset_frames, args.refresh_hz)

    stim_by_trial = defaultdict(list)
    resp_by_trial = defaultdict(list)
    trial_row_by_key = {}

    for row in stim_rows:
        stim_by_trial[trial_key(row)].append(row)
    for row in resp_rows:
        resp_by_trial[trial_key(row)].append(row)
    for row in trial_rows:
        key = trial_key(row)
        if key in trial_row_by_key:
            add_issue(issues, "ERROR", "duplicate_trial_summary", "Duplicate trials.csv row for the same trial.", key)
        trial_row_by_key[key] = row

    for key, trial_stim in stim_by_trial.items():
        trial_stim.sort(key=lambda r: (to_float(r.get("fade_in_start")) or -1.0, r.get("appearance_id", "")))
        trial_resp = sorted(resp_by_trial.get(key, []), key=lambda r: to_float(r.get("keypress_time")) or -1.0)
        trial_summary = trial_row_by_key.get(key)

        if trial_summary is None:
            add_issue(issues, "ERROR", "missing_trial_summary", "No trials.csv row found for this trial.", key)

        stim_roles = Counter(row.get("role") for row in trial_stim)
        response_types = Counter(row.get("response_type") for row in trial_resp)
        hits_in_resp = sum(1 for row in trial_resp if row.get("response_type") == "hit")
        fas_in_resp = sum(1 for row in trial_resp if (row.get("response_type") or "").startswith("fa_"))

        for row in trial_stim:
            start_vis = to_float(row.get("fade_in_start"))
            peak_vis = to_float(row.get("peak_opacity_time"))
            end_vis = to_float(row.get("fade_out_end"))
            sound_start = to_float(row.get("sound_start"))
            sound_end = to_float(row.get("sound_end"))
            sound_lead = to_float(row.get("sound_lead_sec"))
            response_time = to_float(row.get("response_time"))
            rt_from_fade_in = to_float(row.get("rt_from_fade_in"))
            scheduled_start_vis = to_float(row.get("scheduled_fade_in_start"))
            scheduled_peak_vis = to_float(row.get("scheduled_peak_opacity_time"))
            scheduled_end_vis = to_float(row.get("scheduled_fade_out_end"))
            scheduled_sound_start = to_float(row.get("scheduled_sound_start"))
            scheduled_sound_end = to_float(row.get("scheduled_sound_end"))
            requested_sound_start = to_float(row.get("requested_sound_start"))
            visual_onset_error_ms = to_float(row.get("visual_onset_error_ms"))
            sound_onset_error_ms = to_float(row.get("sound_onset_error_ms"))
            av_sync_error_ms = to_float(row.get("av_sync_error_ms"))
            sound_start_source = row.get("sound_start_source")
            response_made = to_bool(row.get("response_made"))
            response_in_window = row.get("response_in_window")
            role = row.get("role")

            if None in (start_vis, peak_vis, end_vis):
                add_issue(issues, "ERROR", "missing_visual_time", f"{row.get('appearance_id')} is missing visual timing.", key)
                continue

            if not (start_vis <= peak_vis <= end_vis):
                add_issue(issues, "ERROR", "bad_visual_order", f"{row.get('appearance_id')} has out-of-order visual times.", key)

            if scheduled_start_vis is not None:
                computed_visual_error_ms = (start_vis - scheduled_start_vis) * 1000
                if visual_onset_error_ms is not None and not approx_equal(computed_visual_error_ms, visual_onset_error_ms, 1.0):
                    add_issue(
                        issues, "ERROR", "visual_onset_error_mismatch",
                        f"{row.get('appearance_id')} stores visual_onset_error_ms={visual_onset_error_ms:.3f} but computed drift is {computed_visual_error_ms:.3f} ms.",
                        key,
                    )
                drift_ms = visual_onset_error_ms if visual_onset_error_ms is not None else computed_visual_error_ms
                abs_drift_ms = abs(drift_ms)
                if abs_drift_ms > error_visual_onset_error_ms:
                    add_issue(
                        issues, "ERROR", "visual_onset_drift",
                        f"{row.get('appearance_id')} has visual onset drift of {drift_ms:.3f} ms (> {args.error_visual_onset_frames:.2f} frames at {args.refresh_hz:.1f} Hz).",
                        key,
                    )
                elif abs_drift_ms > warn_visual_onset_error_ms:
                    add_issue(
                        issues, "WARN", "visual_onset_drift",
                        f"{row.get('appearance_id')} has visual onset drift of {drift_ms:.3f} ms (> {args.warn_visual_onset_frames:.2f} frames at {args.refresh_hz:.1f} Hz).",
                        key,
                    )

                if scheduled_peak_vis is not None:
                    expected_peak = start_vis + (scheduled_peak_vis - scheduled_start_vis)
                    if not approx_equal(expected_peak, peak_vis, args.timing_tol):
                        add_issue(
                            issues, "ERROR", "visual_phase_shift",
                            f"{row.get('appearance_id')} peak time no longer matches the expected phase shift from actual onset.",
                            key,
                        )
                if scheduled_end_vis is not None:
                    expected_end = start_vis + (scheduled_end_vis - scheduled_start_vis)
                    if not approx_equal(expected_end, end_vis, args.timing_tol):
                        add_issue(
                            issues, "ERROR", "visual_phase_shift",
                            f"{row.get('appearance_id')} fade-out end no longer matches the expected phase shift from actual onset.",
                            key,
                        )

            if sound_lead is not None:
                if sound_start is None or sound_end is None:
                    add_issue(issues, "ERROR", "missing_sound_window", f"{row.get('appearance_id')} has SOA but missing sound timing.", key)
                else:
                    if sound_start < -args.timing_tol:
                        add_issue(issues, "ERROR", "negative_sound_start", f"{row.get('appearance_id')} has sound_start < 0 ({sound_start:.3f}).", key)
                    actual_lead = peak_vis - sound_start
                    if not approx_equal(actual_lead, sound_lead, args.timing_tol):
                        add_issue(
                            issues, "ERROR", "soa_mismatch",
                            f"{row.get('appearance_id')} logged lead {sound_lead:.3f}s but peak-sound_start is {actual_lead:.3f}s.",
                            key,
                        )
                    if sound_end < sound_start:
                        add_issue(issues, "ERROR", "bad_sound_order", f"{row.get('appearance_id')} has sound_end before sound_start.", key)

                    if scheduled_sound_start is not None:
                        computed_sound_error_ms = (sound_start - scheduled_sound_start) * 1000
                        if sound_onset_error_ms is not None and not approx_equal(computed_sound_error_ms, sound_onset_error_ms, 1.0):
                            add_issue(
                                issues, "ERROR", "sound_onset_error_mismatch",
                                f"{row.get('appearance_id')} stores sound_onset_error_ms={sound_onset_error_ms:.3f} but computed drift is {computed_sound_error_ms:.3f} ms.",
                                key,
                            )
                        if sound_start_source == "fallback_postflip":
                            drift_ms = sound_onset_error_ms if sound_onset_error_ms is not None else computed_sound_error_ms
                            abs_drift_ms = abs(drift_ms)
                            if abs_drift_ms > error_sound_onset_error_ms:
                                add_issue(
                                    issues, "ERROR", "sound_onset_drift",
                                    f"{row.get('appearance_id')} has fallback sound timestamp drift of {drift_ms:.3f} ms (> {args.error_sound_onset_frames:.2f} frame-equivalents at {args.refresh_hz:.1f} Hz).",
                                    key,
                                )
                            elif abs_drift_ms > warn_sound_onset_error_ms:
                                add_issue(
                                    issues, "WARN", "sound_onset_drift",
                                    f"{row.get('appearance_id')} has fallback sound timestamp drift of {drift_ms:.3f} ms (> {args.warn_sound_onset_frames:.2f} frame-equivalents at {args.refresh_hz:.1f} Hz).",
                                    key,
                                )

                        computed_av_sync_error_ms = ((start_vis - sound_start) - (scheduled_start_vis - scheduled_sound_start)) * 1000
                        if av_sync_error_ms is not None and not approx_equal(computed_av_sync_error_ms, av_sync_error_ms, 1.0):
                            add_issue(
                                issues, "ERROR", "av_sync_error_mismatch",
                                f"{row.get('appearance_id')} stores av_sync_error_ms={av_sync_error_ms:.3f} but computed AV drift is {computed_av_sync_error_ms:.3f} ms.",
                                key,
                            )
                        av_drift_ms = av_sync_error_ms if av_sync_error_ms is not None else computed_av_sync_error_ms
                        abs_av_drift_ms = abs(av_drift_ms)
                        if abs_av_drift_ms > error_sound_onset_error_ms:
                            add_issue(
                                issues, "ERROR", "av_sync_drift",
                                f"{row.get('appearance_id')} has AV sync drift of {av_drift_ms:.3f} ms (> {args.error_sound_onset_frames:.2f} frame-equivalents at {args.refresh_hz:.1f} Hz).",
                                key,
                            )
                        elif abs_av_drift_ms > warn_sound_onset_error_ms:
                            add_issue(
                                issues, "WARN", "av_sync_drift",
                                f"{row.get('appearance_id')} has AV sync drift of {av_drift_ms:.3f} ms (> {args.warn_sound_onset_frames:.2f} frame-equivalents at {args.refresh_hz:.1f} Hz).",
                                key,
                            )

                        if sound_start_source == "ptb_preflight" and requested_sound_start is not None:
                            requested_slip_ms = (requested_sound_start - scheduled_sound_start) * 1000
                            if not approx_equal(requested_slip_ms, computed_sound_error_ms, 1.0):
                                add_issue(
                                    issues, "WARN", "ptb_sound_request_mismatch",
                                    f"{row.get('appearance_id')} has PTB sound_start/requested_sound_start disagreement larger than expected.",
                                    key,
                                )

                    if scheduled_sound_end is not None and scheduled_sound_start is not None:
                        expected_sound_end = sound_start + (scheduled_sound_end - scheduled_sound_start)
                        if not approx_equal(expected_sound_end, sound_end, args.timing_tol):
                            add_issue(
                                issues, "ERROR", "sound_duration_shift",
                                f"{row.get('appearance_id')} sound end no longer matches the expected duration from actual sound onset.",
                                key,
                            )

                    if sound_start_source == "fallback_postflip":
                        fallback_sound_rows.append((key, row.get("appearance_id")))

            if response_time is not None and rt_from_fade_in is not None:
                actual_rt = response_time - start_vis
                if not approx_equal(actual_rt, rt_from_fade_in, args.timing_tol):
                    add_issue(
                        issues, "ERROR", "rt_mismatch",
                        f"{row.get('appearance_id')} has rt_from_fade_in={rt_from_fade_in:.3f}s but computed RT is {actual_rt:.3f}s.",
                        key,
                    )

            if role in ("PD", "NPD") and response_in_window not in ("N/A", "", None):
                legacy_distractor_response_window.append((key, row.get("appearance_id"), response_in_window))

            if role in ("PT", "NPT") and response_made and response_time is None:
                add_issue(issues, "ERROR", "missing_response_time", f"{row.get('appearance_id')} is marked responded without response_time.", key)

        for i, left in enumerate(trial_stim):
            left_corner = left.get("corner")
            left_start = to_float(left.get("fade_in_start"))
            left_end = to_float(left.get("fade_out_end"))
            left_sound_start = to_float(left.get("sound_start"))
            left_sound_end = to_float(left.get("sound_end"))

            for right in trial_stim[i + 1:]:
                right_start = to_float(right.get("fade_in_start"))
                right_end = to_float(right.get("fade_out_end"))
                right_sound_start = to_float(right.get("sound_start"))
                right_sound_end = to_float(right.get("sound_end"))

                if left_corner == right.get("corner"):
                    if left_start is not None and left_end is not None and right_start is not None and right_end is not None:
                        if not (left_end <= right_start + args.timing_tol or right_end <= left_start + args.timing_tol):
                            add_issue(
                                issues, "ERROR", "same_corner_overlap",
                                f"{left.get('appearance_id')} and {right.get('appearance_id')} overlap in {left_corner}.",
                                key,
                            )

                if left_start is not None and right_start is not None:
                    onset_gap = abs(right_start - left_start)
                    if onset_gap + args.timing_tol < args.visual_gap:
                        add_issue(
                            issues, "ERROR", "visual_onset_gap",
                            f"{left.get('appearance_id')} and {right.get('appearance_id')} start {onset_gap:.3f}s apart.",
                            key,
                        )

                if left.get("object_id") == right.get("object_id"):
                    if left_start is not None and left_end is not None and right_start is not None and right_end is not None:
                        same_gap = min(abs(right_start - left_end), abs(left_start - right_end))
                        overlap_or_gap_ok = (
                            left_end + args.same_item_gap <= right_start + args.timing_tol
                            or right_end + args.same_item_gap <= left_start + args.timing_tol
                        )
                        if not overlap_or_gap_ok:
                            add_issue(
                                issues, "ERROR", "same_item_repeat_gap",
                                f"{left.get('appearance_id')} and {right.get('appearance_id')} repeat {left.get('object_name')} too closely.",
                                key,
                            )

                if None not in (left_sound_start, left_sound_end, right_sound_start, right_sound_end):
                    gap_ok = (
                        left_sound_end + args.audio_gap <= right_sound_start + args.timing_tol
                        or right_sound_end + args.audio_gap <= left_sound_start + args.timing_tol
                    )
                    if not gap_ok:
                        add_issue(
                            issues, "ERROR", "audio_overlap_gap",
                            f"{left.get('appearance_id')} and {right.get('appearance_id')} have audio windows too close.",
                            key,
                        )

        eligible_hits = []
        for row in trial_stim:
            role = row.get("role")
            if role not in ("PT", "NPT"):
                continue
            if not to_bool(row.get("response_made")):
                continue
            if row.get("response_key") in (None, ""):
                continue
            eligible_hits.append((
                row.get("response_key"),
                round(to_float(row.get("response_time")) or -1.0, 4),
                row.get("role"),
                row.get("object_name"),
            ))

        hit_rows = [
            (
                row.get("key_pressed"),
                round(to_float(row.get("keypress_time")) or -1.0, 4),
                row.get("hit_role"),
                row.get("hit_object"),
            )
            for row in trial_resp if row.get("response_type") == "hit"
        ]

        if Counter(eligible_hits) != Counter(hit_rows):
            add_issue(
                issues, "ERROR", "hit_reconciliation",
                f"Stimulus hit rows ({len(eligible_hits)}) do not reconcile with responses hits ({len(hit_rows)}).",
                key,
            )

        if trial_summary:
            expected_total = len(trial_stim)
            expected_hits = sum(1 for row in trial_stim if row.get("role") in ("PT", "NPT") and to_bool(row.get("response_made")) and to_bool(row.get("response_in_window")) and row.get("response_key") == row.get("target_key"))
            expected_pt = stim_roles.get("PT", 0)
            expected_npt = stim_roles.get("NPT", 0)
            expected_pd = stim_roles.get("PD", 0)
            expected_npd = stim_roles.get("NPD", 0)

            summary_checks = [
                ("n_pt_appearances", expected_pt),
                ("n_npt_appearances", expected_npt),
                ("n_pd_appearances", expected_pd),
                ("n_npd_appearances", expected_npd),
                ("total_appearances", expected_total),
                ("n_hits", expected_hits),
                ("n_false_alarms", fas_in_resp),
            ]
            for field, expected in summary_checks:
                actual = to_int(trial_summary.get(field))
                if actual != expected:
                    add_issue(
                        issues, "ERROR", "trial_summary_mismatch",
                        f"{field}={actual} but computed value is {expected}.",
                        key,
                    )

            trial_dur = to_float(trial_summary.get("trial_duration_sec"))
            max_end = max((to_float(row.get("fade_out_end")) or 0.0) for row in trial_stim) if trial_stim else 0.0
            if trial_dur is not None and trial_dur + args.timing_tol < max_end:
                add_issue(
                    issues, "ERROR", "trial_duration_short",
                    f"trial_duration_sec={trial_dur:.3f}s but a stimulus ends at {max_end:.3f}s.",
                    key,
                )

            measured_refresh_hz = to_float(trial_summary.get("measured_refresh_hz"))
            median_frame_ms = to_float(trial_summary.get("median_frame_ms"))
            max_frame_ms = to_float(trial_summary.get("max_frame_ms"))
            n_long_frames = to_int(trial_summary.get("n_long_frames"))
            expected_frame_ms = 1000.0 / args.refresh_hz if args.refresh_hz else None

            if measured_refresh_hz is not None and args.refresh_hz:
                hz_gap = abs(measured_refresh_hz - args.refresh_hz)
                if hz_gap > max(2.0, args.refresh_hz * 0.05):
                    add_issue(
                        issues, "WARN", "refresh_mismatch",
                        f"trials.csv reports measured_refresh_hz={measured_refresh_hz:.2f} but validator assumed {args.refresh_hz:.2f} Hz.",
                        key,
                    )

            if n_long_frames is not None and n_long_frames > 0:
                add_issue(
                    issues, "WARN", "long_frames",
                    f"Trial recorded {n_long_frames} long frame(s).",
                    key,
                )

            if expected_frame_ms is not None and median_frame_ms is not None:
                if median_frame_ms > expected_frame_ms * args.error_visual_onset_frames:
                    add_issue(
                        issues, "WARN", "slow_frame_pacing",
                        f"median_frame_ms={median_frame_ms:.3f} looks slower than the validator's expected frame budget ({expected_frame_ms:.3f} ms).",
                        key,
                    )

            if expected_frame_ms is not None and max_frame_ms is not None:
                if max_frame_ms > expected_frame_ms * 3.0:
                    add_issue(
                        issues, "WARN", "very_long_frame",
                        f"max_frame_ms={max_frame_ms:.3f} indicates a severe frame delay.",
                        key,
                    )

        for row in trial_resp:
            if row.get("response_type") != "hit":
                continue
            matches = [
                stim for stim in trial_stim
                if stim.get("role") in ("PT", "NPT")
                and round(to_float(stim.get("response_time")) or -1.0, 4) == round(to_float(row.get("keypress_time")) or -1.0, 4)
                and stim.get("response_key") == row.get("key_pressed")
            ]
            if len(matches) != 1:
                add_issue(
                    issues, "ERROR", "hit_match_count",
                    f"Hit at {row.get('keypress_time')} matched {len(matches)} stimulus rows.",
                    key,
                )

        if fas_in_resp != response_types.get("fa_empty", 0) + response_types.get("fa_late", 0) + response_types.get("fa_no_target", 0) + response_types.get("fa_wrong_corner", 0):
            add_issue(issues, "ERROR", "fa_count_internal", "Unexpected internal false-alarm count mismatch.", key)

    real_trial_rows = [row for row in trial_rows if not to_bool(row.get("is_practice"))]
    if args.design_trials_per_block is not None:
        counts = Counter(row.get("block_type") for row in real_trial_rows)
        for block_type, count in sorted(counts.items()):
            if count != args.design_trials_per_block:
                add_issue(
                    issues, "WARN", "design_trials_per_block",
                    f"Block {block_type} has {count} real trials; expected {args.design_trials_per_block}.",
                )

    if args.design_pt_trials is not None:
        counts = Counter(row.get("active_pt_name") for row in real_trial_rows)
        for pt_name, count in sorted(counts.items()):
            if count != args.design_pt_trials:
                add_issue(
                    issues, "WARN", "design_pt_trials",
                    f"PT {pt_name} has {count} real trials; expected {args.design_pt_trials}.",
                )

    if legacy_distractor_response_window:
        sample_key, sample_app_id, sample_value = legacy_distractor_response_window[0]
        add_issue(
            issues, "WARN", "legacy_distractor_response_window",
            f"{len(legacy_distractor_response_window)} distractor rows still use response_in_window='{sample_value}' instead of 'N/A'. "
            f"Sample row: {sample_app_id}. This usually means the data was generated before the logging fix.",
            sample_key,
        )

    if fallback_sound_rows:
        sample_key, sample_app_id = fallback_sound_rows[0]
        add_issue(
            issues, "WARN", "fallback_sound_timestamps",
            f"{len(fallback_sound_rows)} sound row(s) used fallback_postflip timing instead of ptb_preflight. "
            f"Sample row: {sample_app_id}. These rows are still valid, but their sound_start semantics differ slightly.",
            sample_key,
        )

    return issues


def print_report(participant_dir, stim_rows, resp_rows, trial_rows, issues, args):
    report = build_report_text(participant_dir, stim_rows, resp_rows, trial_rows, issues, args)
    print(report)


def build_report_text(participant_dir, stim_rows, resp_rows, trial_rows, issues, args):
    errors = [issue for issue in issues if issue["severity"] == "ERROR"]
    warns = [issue for issue in issues if issue["severity"] == "WARN"]
    lines = []

    lines.append(f"Participant folder: {participant_dir}")
    lines.append(f"Stimulus rows: {len(stim_rows)}")
    lines.append(f"Response rows: {len(resp_rows)}")
    lines.append(f"Trial rows:    {len(trial_rows)}")
    lines.append(f"Errors: {len(errors)}")
    lines.append(f"Warnings: {len(warns)}")
    lines.append("")
    lines.append("Timing thresholds:")
    lines.extend(f"- {line}" for line in timing_threshold_summary(args))

    by_trial = defaultdict(list)
    for issue in issues:
        by_trial[issue["trial"]].append(issue)

    if not issues:
        lines.append("PASS: No validation issues found.")
        return "\n".join(lines)

    lines.append("")
    lines.append("Issues:")
    for issue in issues:
        prefix = f"[{issue['severity']}] {issue['code']}"
        if issue["trial"] is not None:
            lines.append(f"{prefix} | {format_trial_key(issue['trial'])}")
        else:
            lines.append(prefix)
        lines.append(f"  {issue['message']}")

    if by_trial:
        ranked = sorted(
            ((key, len(items)) for key, items in by_trial.items() if key is not None),
            key=lambda pair: pair[1],
            reverse=True,
        )[:10]
        if ranked:
            lines.append("")
            lines.append("Most flagged trials:")
            for key, count in ranked:
                lines.append(f"  {count:2d}  {format_trial_key(key)}")

    return "\n".join(lines)


def write_report(participant_dir, report_text):
    report_path = participant_dir / "validation_report.txt"
    report_path.write_text(report_text + "\n", encoding="utf-8")
    return report_path


def main():
    args = parse_args()
    participant_dir = pick_participant_dir(args.data_dir, args.participant)
    pid = participant_dir.name

    stim_path = participant_dir / f"participant_{pid}_stimulus.csv"
    resp_path = participant_dir / f"participant_{pid}_responses.csv"
    trials_path = participant_dir / f"participant_{pid}_trials.csv"

    missing_files = [str(path) for path in (stim_path, resp_path, trials_path) if not path.exists()]
    if missing_files:
        for path in missing_files:
            print(f"Missing file: {path}")
        raise SystemExit(1)

    stim_rows, stim_cols, stim_missing = load_csv(stim_path, STIM_ALIASES, REQUIRED_STIM)
    resp_rows, resp_cols, resp_missing = load_csv(resp_path, RESP_ALIASES, REQUIRED_RESP)
    trial_rows, trial_cols, trial_missing = load_csv(trials_path, TRIAL_ALIASES, REQUIRED_TRIALS)

    issues = []
    for label, missing in (
        ("stimulus.csv", stim_missing),
        ("responses.csv", resp_missing),
        ("trials.csv", trial_missing),
    ):
        if missing:
            add_issue(issues, "ERROR", "missing_columns", f"{label} is missing canonical columns: {missing}")

    issues.extend(validate_rows(stim_rows, resp_rows, trial_rows, args))
    report_text = build_report_text(participant_dir, stim_rows, resp_rows, trial_rows, issues, args)
    print(report_text)

    if args.write_report:
        report_path = write_report(participant_dir, report_text)
        print(f"\nSaved report: {report_path}")

    raise SystemExit(1 if any(issue["severity"] == "ERROR" for issue in issues) else 0)


if __name__ == "__main__":
    main()
