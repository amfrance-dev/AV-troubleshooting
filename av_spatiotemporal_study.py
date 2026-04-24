# ==============================================================================
# Main entry point for the AV spatiotemporal study runtime.
# PSYCHOPY EXPERIMENT: AV SPATIOTEMPORAL AWARENESS
# VERSION 26
#
# Timing notes:
#   - Visual onset is stamped from the VBL-synchronised timestamp returned by
#     win.flip(), converted into the shared keyboard clock timebase.
#
#   - PTB audio is scheduled against the upcoming flip with play(when=...),
#     and sound_start is logged as that flip-aligned request time. This is a
#     tight software timestamp, but not a microphone-confirmed DAC onset.
#   - av_sync_error_ms captures the change in recorded sound-vs-visual
#     alignment relative to the planned SOA, which helps expose late-flip AV
#     desync even when PTB sound scheduling itself looks clean.
#   - Frame intervals are summarised per trial into trials.csv so dropped/long
#     frames can be debugged alongside the response and stimulus logs.
# Retains:
#   - Audio normalization via pydub (TARGET_DBFS)
#   - Spatial jitter within quadrants
#   - Expanded 20-item stimulus pool
#   - Flattened target hit label to 'hit'
# ==============================================================================

import os
import sys

# 1. WAYLAND GUARD (CRITICAL for AV Sync)
if os.environ.get('XDG_SESSION_TYPE') == 'wayland':
    raise RuntimeError(
        "CRITICAL: Wayland session detected. PsychoPy requires bare-metal VBLANK access. "
        "Log out, click the gear icon on the GDM login screen, select 'Ubuntu on Xorg', "
        "and log back in before running this experiment."
    )

# 2. IMPORT PREFS FIRST
from psychopy import prefs

# 3. SET AUDIO ENGINE PREFERENCES
# Prioritizing 'ptb' (PsychToolbox) for sub-millisecond timing.
# audioSpeaker must be set to 'default' to fix the DeviceNotConnectedError.
prefs.hardware['audioLib'] = ['sounddevice', 'ptb']
prefs.hardware['audioLatencyMode'] = [3]  
prefs.hardware['audioSpeaker'] = ['default']

# 4. RESOLVE AND PIN HARDWARE
# We use 'default' because your hardware scan marked it as the primary active ALSA bridge.
try:
    import sounddevice as _sd
    _devs = _sd.query_devices()
    
    # On your system, 'default' (Index 14) is the confirmed PipeWire/Pulse bridge.
    # We pin it as a list to satisfy the 2025 hardware manager.
    prefs.hardware['audioDevice'] = ['default']
    print("[AUDIO] Hardware Sync: Pinned to 'default' bridge")
            
except Exception as _e:
    print(f"[AUDIO] Could not pin hardware: {_e} — using system defaults")



# 4. IMMEDIATELY import the sound module to lock in ALL preferences
from psychopy import sound

# 5. Now import everything else
import numpy as np
import random
import csv
from datetime import datetime
from PIL import Image
from psychopy import visual, core, event, logging
from psychopy.hardware import keyboard

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("WARNING: pydub not installed — audio normalization disabled. "
          "Run: pip install pydub")


# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================

# --- File paths ---
STUDY_DIR = '/run/user/{uid}/gvfs/smb-share:server=psyc-files.ucsc.edu,share=jamal/Experiments/Anthony/AudioVisualSpatiotemporalStudy-codex-sanji-runtime-bundle'.format(
    uid=os.getuid() if hasattr(os, 'getuid') else 1000
)
if not os.path.exists(STUDY_DIR):
    print(f"WARNING: SMB mount not found at {STUDY_DIR}, trying local Desktop fallback...")
    STUDY_DIR = os.path.expanduser('~/Desktop/AV_Study')
    if not os.path.exists(STUDY_DIR):
        print(f"WARNING: ~/Desktop/AV_Study not found, trying script directory...")
        STUDY_DIR = os.path.dirname(os.path.abspath(__file__))
        print(f"Using script directory: {STUDY_DIR}")

os.chdir(STUDY_DIR)
print(f"Working directory: {STUDY_DIR}")

# --- Privileged target selection ---
PT_COUNT_PER_GROUP = 2      

# --- PT SOA (fixed per PT for whole experiment) ---
PT_SOA_MIN = 0.8            
PT_SOA_MAX = 3.0

# --- Privileged Distractor config ---
PD_COUNT_PER_BLOCK = 2      
PD_SOA_MIN = 1.0            
PD_SOA_MAX = 3.0

# --- Trial counts ---
NUM_ANIMATE_TRIALS   = 5   
NUM_INANIMATE_TRIALS = 5   

PT_SUBBLOCK_ORDER = 'random'
ALLOW_BOTH_PTS_SAME_TRIAL = False

# --- Stimulus appearance counts per trial (randomly sampled each trial) ---
TRIAL_PT_MIN   = 2      
TRIAL_PT_MAX   = 3
TRIAL_NPT_MIN  = 1      
TRIAL_NPT_MAX  = 4
TRIAL_PD_MIN   = 1      
TRIAL_PD_MAX   = 3
TRIAL_NPD_MIN  = 2      
TRIAL_NPD_MAX  = 6

# --- Spatial bias ---
TARGET_SPATIAL_BIAS = 0.80  

# --- Visual timing (seconds) ---
FADE_IN_DUR   = 0.5
PEAK_HOLD_DUR = 0.2
FADE_OUT_DUR  = 0.5
STIM_DUR      = FADE_IN_DUR + PEAK_HOLD_DUR + FADE_OUT_DUR  
MIN_VISUAL_ONSET_GAP = 0.25
MIN_SAME_ITEM_GAP = 0.75

# --- Trial timing ---
TRIAL_CONTENT_DUR  = 20.0   
TRIAL_BUFFER_DUR   = 2.0    
WINDOW_EXTEND_SEC  = 3.0    
MAX_WINDOW_EXTENDS = 5      

BETWEEN_PT_STIMULUS_GAP = 1.0  

# --- Audio ---
SOUND_DUR     = 1.0     
MIN_AUDIO_GAP = 0.2     
TARGET_DBFS   = -20.0   
PREFER_CLEANED_AUDIO = True
CLEANED_AUDIO_SUBDIR = '_cleaned'
CANONICAL_AUDIO_HZ = 48000
CANONICAL_AUDIO_CHANNELS = 2
CANONICAL_AUDIO_SAMPLE_WIDTH_BYTES = 2

# --- Response ---
RESPONSE_WINDOW = 1.5   
FA_LATE_GRACE_SEC = 0.5

# --- Display / debug timing ---
FALLBACK_REFRESH_HZ = 120.0
FRAME_DROP_THRESHOLD_FACTOR = 1.2

# --- Background ---
BG_NOISE_OPACITY = 0.3
BG_SOURCE_FILE   = 'otherblobs.png'
BG_UPDATE_RATE   = 0.4

# --- Visuals ---
IMAGE_SIZE  = [200, 200]  # Reduced by 50%
MAX_OPACITY = 1.0

# --- Debug overlay ---
# Set to True to show quadrant dividing lines and corner dots during trials.
# Flip to False before real data collection.
DEBUG_OVERLAY = True

# --- Numpad mapping (Linux Safe) ---
CORNER_TO_KEY = {
    'top_left':     ['num_4', 'KP_Left'],
    'top_right':    ['num_5', 'KP_Begin'],
    'bottom_left':  ['num_1', 'KP_End'],
    'bottom_right': ['num_2', 'KP_Down'],
}
# Flatten the list so PsychoPy can listen to all variations
ALL_RESPONSE_KEYS  = [k for keys in CORNER_TO_KEY.values() for k in keys]
ALL_CORNERS        = list(CORNER_TO_KEY.keys())
NON_BIASED_CORNERS = ['top_left', 'bottom_left', 'bottom_right']


# ==============================================================================
# 2. STIMULUS NAME LOOKUP 
# ==============================================================================

ANIMATE_NAMES = {
    1: 'cat',   2: 'frog',    3: 'duck',
    4: 'cow',   5: 'rooster', 6: 'dog',
    7: 'horse', 8: 'lion',    9: 'pig',
   10: 'elephant',
}

ANIMATE_SOUNDS = {
    1: 'meow',  2: 'ribbit',  3: 'quack',
    4: 'moo',   5: 'crow',    6: 'bark',
    7: 'neigh', 8: 'roar',    9: 'oink',
   10: 'trumpet',
}

INANIMATE_NAMES = {
    1: 'camera',     2: 'door',        3: 'phone',
    4: 'toilet',     5: 'clock',       6: 'car',
    7: 'wineglass',  8: 'helicopter',  9: 'motorcycle',
   10: 'ship',
}

INANIMATE_SOUNDS = {
    1: 'click',  2: 'knock',  3: 'ring',
    4: 'flush',  5: 'tick',   6: 'vroom',
    7: 'clink',  8: 'blades', 9: 'rev',
   10: 'horn',
}

def friendly_name(item):
    """Return human-readable name for a stimulus item."""
    n = item['obj_num']
    if item['cat'] == 'animate':
        return f"{ANIMATE_NAMES[n]} ({ANIMATE_SOUNDS[n]})"
    else:
        return f"{INANIMATE_NAMES[n]} ({INANIMATE_SOUNDS[n]})"


# ==============================================================================
# 3. STIMULI DEFINITIONS
# ==============================================================================

def get_path(category, obj_num, file_type='img'):
    if file_type == 'img':
        return os.path.join('20_stimuli', category, 'objects_numbered', f'obj_{obj_num}_bw.png')
    elif file_type == 'snd':
        return os.path.join('20_stimuli', category, 'obj_snds', f'snd_{obj_num}.wav')

animate_pool   = [{'name': f'animate_obj_{i}',   'cat': 'animate',   'obj_num': i} for i in range(1, 11)]
inanimate_pool = [{'name': f'inanimate_obj_{i}', 'cat': 'inanimate', 'obj_num': i} for i in range(1, 11)]

print(f"Loaded {len(animate_pool)} animate and {len(inanimate_pool)} inanimate stimuli")


# ==============================================================================
# 3b. AUDIO NORMALIZATION 
# ==============================================================================

_normalized_cache = {}


def trim_leading_silence(seg, silence_thresh_dbfs=-40.0, chunk_ms=10):
    """Trim leading silence so perceptual onset better matches logged onset."""
    trim_ms = 0
    while trim_ms < len(seg):
        chunk = seg[trim_ms:trim_ms + chunk_ms]
        if chunk.dBFS != float('-inf') and chunk.dBFS > silence_thresh_dbfs:
            break
        trim_ms += chunk_ms
    return seg[trim_ms:]


def get_cleaned_audio_path(snd_path):
    cleaned_path = os.path.join(
        os.path.dirname(snd_path),
        CLEANED_AUDIO_SUBDIR,
        os.path.basename(snd_path),
    )
    if os.path.exists(cleaned_path):
        return cleaned_path
    return None


def normalize_audio(snd_path):
    if PREFER_CLEANED_AUDIO:
        cleaned_path = get_cleaned_audio_path(snd_path)
        if cleaned_path is not None:
            return cleaned_path

    if not PYDUB_AVAILABLE:
        return snd_path

    cache_key = (snd_path, SOUND_DUR, TARGET_DBFS)
    if cache_key in _normalized_cache:
        return _normalized_cache[cache_key]

    try:
        norm_dir = os.path.join(os.path.dirname(snd_path), '_normalized')
        os.makedirs(norm_dir, exist_ok=True)
        stem, ext = os.path.splitext(os.path.basename(snd_path))
        norm_name = f"{stem}_trimmed_{int(SOUND_DUR * 1000)}ms_{int(abs(TARGET_DBFS) * 10)}.wav"
        norm_path = os.path.join(norm_dir, norm_name)

        if not os.path.exists(norm_path):
            seg = AudioSegment.from_wav(snd_path)
            seg = trim_leading_silence(seg)
            seg = seg.set_frame_rate(CANONICAL_AUDIO_HZ)
            seg = seg.set_channels(CANONICAL_AUDIO_CHANNELS)
            seg = seg.set_sample_width(CANONICAL_AUDIO_SAMPLE_WIDTH_BYTES)

            target_ms = int(SOUND_DUR * 1000)
            if len(seg) > target_ms:
                seg = seg[:target_ms]
            elif len(seg) < target_ms:
                seg += AudioSegment.silent(duration=target_ms - len(seg), frame_rate=seg.frame_rate)

            if seg.dBFS != float('-inf'):
                delta = TARGET_DBFS - seg.dBFS
                peak_limited_delta = min(delta, -1.0 - seg.max_dBFS)
                seg = seg.apply_gain(peak_limited_delta)
            seg.export(norm_path, format='wav')
            print(f"  [AUDIO] Normalized {os.path.basename(snd_path)}: "
                  f"trimmed to {SOUND_DUR:.2f}s, matched near {TARGET_DBFS:.1f} dBFS, "
                  f"exported at {CANONICAL_AUDIO_HZ} Hz")
        else:
            print(f"  [AUDIO] Using cached normalized {os.path.basename(snd_path)}")

        _normalized_cache[cache_key] = norm_path
        return norm_path

    except Exception as e:
        print(f"  WARNING: audio normalization failed for {snd_path}: {e} — using original")
        _normalized_cache[cache_key] = snd_path
        return snd_path


# ==============================================================================
# 4. PARTICIPANT ID
# ==============================================================================

participant_pid = datetime.now().strftime('%Y%m%d_%H%M%S')
data_dir        = os.path.join(STUDY_DIR, 'data', participant_pid)
os.makedirs(data_dir, exist_ok=True)
data_filename      = f"participant_{participant_pid}_stimulus.csv"
data_filepath      = os.path.join(data_dir, data_filename)
responses_filename = f"participant_{participant_pid}_responses.csv"
responses_filepath = os.path.join(data_dir, responses_filename)
trials_filename    = f"participant_{participant_pid}_trials.csv"
trials_filepath    = os.path.join(data_dir, trials_filename)

print(f"\nParticipant PID: {participant_pid}")
print(f"Stimulus file:   {data_filename}")
print(f"Responses file:  {responses_filename}")
print(f"Trials file:     {trials_filename}\n")


# ==============================================================================
# 5. PRIVILEGED GROUP ASSIGNMENT
# ==============================================================================

def assign_pt_group():
    animate_pts   = random.sample(animate_pool,   PT_COUNT_PER_GROUP)
    inanimate_pts = random.sample(inanimate_pool, PT_COUNT_PER_GROUP)
    pt_group = {}
    for item in animate_pts + inanimate_pts:
        soa = round(random.uniform(PT_SOA_MIN, PT_SOA_MAX), 2)
        pt_group[item['name']] = {'item': item, 'soa': soa, 'role': 'PT'}
    return pt_group

def assign_pd_group(pt_group, block_type):
    pt_names = set(pt_group.keys())

    if block_type == 'animate':
        base_pool = inanimate_pool
    else:
        base_pool = animate_pool

    distractor_pool = [x for x in base_pool if x['name'] not in pt_names]

    count    = min(PD_COUNT_PER_BLOCK, len(distractor_pool))
    pd_items = random.sample(distractor_pool, count)
    pd_names = {x['name'] for x in pd_items}

    pd_group = {item['name']: {'item': item, 'role': 'PD'} for item in pd_items}
    npd_pool = [x for x in distractor_pool if x['name'] not in pd_names]

    return pd_group, npd_pool


# ==============================================================================
# 6. WINDOW & CORNERS
# ==============================================================================

def default_clock_to(clock_obj, default_clock_time):
    """Convert a logging.defaultClock timestamp into the given clock's timebase."""
    return (
        default_clock_time
        + logging.defaultClock.getLastResetTime()
        - clock_obj.getLastResetTime()
    )


def measure_refresh_hz(window):
    """Measure the achieved refresh rate and fall back gracefully if needed."""
    try:
        measured = window.getActualFrameRate(
            nIdentical=20,
            nMaxFrames=240,
            nWarmUpFrames=60,
            threshold=1,
        )
        if measured:
            return float(measured)
    except Exception as e:
        print(f"WARNING: getActualFrameRate failed: {e}")

    try:
        frame_metrics = window.getMsPerFrame(nFrames=120, showVisual=False)
        reference_ms = None
        if isinstance(frame_metrics, (list, tuple)) and frame_metrics:
            reference_ms = frame_metrics[-1] or frame_metrics[0]
        if reference_ms:
            return 1000.0 / float(reference_ms)
    except Exception as e:
        print(f"WARNING: getMsPerFrame failed: {e}")

    return None

win = visual.Window(
    size=[1920, 1080],
    units='pix',
    color=[0, 0, 0],
    fullscr=True,
    screen=0,
    checkTiming=True
)

actual_size = win.size
print(f"Window size: {actual_size[0]} x {actual_size[1]}")
MEASURED_REFRESH_HZ = measure_refresh_hz(win)
ACTIVE_REFRESH_HZ = MEASURED_REFRESH_HZ or FALLBACK_REFRESH_HZ
FRAME_PERIOD_SEC = 1.0 / ACTIVE_REFRESH_HZ if ACTIVE_REFRESH_HZ else (1.0 / FALLBACK_REFRESH_HZ)
HALF_FRAME_SEC = FRAME_PERIOD_SEC / 2.0
BG_UPDATE_EVERY_FRAMES = max(1, int(round(BG_UPDATE_RATE / FRAME_PERIOD_SEC)))
win.monitorFramePeriod = FRAME_PERIOD_SEC
win.recordFrameIntervals = False
win.refreshThreshold = FRAME_PERIOD_SEC * FRAME_DROP_THRESHOLD_FACTOR
if MEASURED_REFRESH_HZ:
    print(f"Measured refresh rate: {MEASURED_REFRESH_HZ:.2f} Hz")
else:
    print(f"WARNING: Could not measure refresh rate; using fallback {FALLBACK_REFRESH_HZ:.1f} Hz")
w, h = actual_size[0] / 4, actual_size[1] / 4
kb = keyboard.Keyboard()
SHARED_CLOCK = kb.clock

CORNERS = {
    'top_right':    [ w,  h],
    'top_left':     [-w,  h],
    'bottom_left':  [-w, -h],
    'bottom_right': [ w, -h],
}


# ==============================================================================
# 7. BACKGROUND NOISE
# ==============================================================================

def load_background():
    print("Loading background noise...")
    try:
        img_array = np.array(Image.open(BG_SOURCE_FILE).convert('L'))
        print(f"Loaded: {BG_SOURCE_FILE}")
    except FileNotFoundError:
        print(f"WARNING: {BG_SOURCE_FILE} not found — using synthetic noise.")
        img_array = np.random.rand(512, 512) * 255

    frames = []
    for _ in range(20):
        fft_data   = np.fft.fftshift(np.fft.fft2(img_array))
        mag        = np.abs(fft_data)
        rand_phase = -np.pi + 2 * np.pi * np.random.random(fft_data.shape)
        recon      = np.real(np.fft.ifft2(np.fft.ifftshift(mag * np.exp(1j * rand_phase))))
        recon      = (recon - recon.min()) / (recon.max() - recon.min())
        frames.append(visual.ImageStim(win, image=(recon * 2) - 1,
                                       size=win.size, opacity=BG_NOISE_OPACITY))
    print("Background ready.\n")
    return frames

noise_stims = load_background()


def preload_stimulus_resources():
    """Load visual and audio assets once so trial building stays lightweight.

    Sound objects are instantiated here at startup (not per-trial) so that
    make_event() never blocks on audio init after the participant presses a key.
    sounddevice Sound objects are reusable across trials.
    """
    image_cache = {}
    sound_path_cache = {}
    sound_stim_cache = {}

    print("Preloading stimulus resources...")
    for item in animate_pool + inanimate_pool:
        item_name = item['name']

        img_path = get_path(item['cat'], item['obj_num'], 'img')
        try:
            image_cache[item_name] = visual.ImageStim(
                win,
                image=img_path,
                pos=(0, 0),
                size=IMAGE_SIZE,
            )
        except Exception as e:
            print(f"  WARNING: image preload failed {img_path}: {e}")
            image_cache[item_name] = None

        snd_path = get_path(item['cat'], item['obj_num'], 'snd')
        snd_path = normalize_audio(snd_path)
        sound_path_cache[item_name] = snd_path

        # Pre-instantiate Sound object — eliminates blocking init at trial start
        try:
            snd_obj = sound.Sound(snd_path, stereo=True, preBuffer=-1)
            sound_stim_cache[item_name] = snd_obj
            print(f"  [AUDIO] Preloaded {item_name}")
        except Exception as e:
            print(f"  WARNING: sound preload failed {item_name} ({snd_path}): {e}")
            sound_stim_cache[item_name] = None

    print("Stimulus preload complete.\n")
    return image_cache, sound_path_cache, sound_stim_cache


IMAGE_STIM_CACHE, SOUND_PATH_CACHE, SOUND_STIM_CACHE = preload_stimulus_resources()


# ==============================================================================
# 8. TRIAL BUILDER 
# ==============================================================================

def build_trial_appearances(block_type, pt_group, pd_group, npd_pool, active_pt_name):
    pt_names      = set(pt_group.keys())
    active_pt     = pt_group[active_pt_name]

    block_pt_names    = {k for k, v in pt_group.items() if v['item']['cat'] == block_type}
    inactive_pt_names = block_pt_names - {active_pt_name}

    target_pool    = (animate_pool if block_type == 'animate' else inanimate_pool)
    npt_candidates = [x for x in target_pool if x['name'] not in pt_names]
    pd_list        = list(pd_group.values())

    appearances = []

    for i in range(random.randint(TRIAL_PT_MIN, TRIAL_PT_MAX)):
        appearances.append({
            'role': 'PT', 'item': active_pt['item'],
            'soa': active_pt['soa'], 'sound': True, 'app_id': f'PT_{i+1}',
        })

    for i in range(random.randint(TRIAL_NPT_MIN, TRIAL_NPT_MAX)):
        appearances.append({
            'role': 'NPT', 'item': random.choice(npt_candidates),
            'soa': None, 'sound': False, 'app_id': f'NPT_{i+1}',
        })

    for i in range(random.randint(TRIAL_PD_MIN, TRIAL_PD_MAX)):
        appearances.append({
            'role': 'PD', 'item': random.choice(pd_list)['item'],
            'soa': round(random.uniform(PD_SOA_MIN, PD_SOA_MAX), 3),
            'sound': True, 'app_id': f'PD_{i+1}',
        })

    for i in range(random.randint(TRIAL_NPD_MIN, TRIAL_NPD_MAX)):
        appearances.append({
            'role': 'NPD', 'item': random.choice(npd_pool),
            'soa': None, 'sound': False, 'app_id': f'NPD_{i+1}',
        })

    return appearances


def build_timeline(appearances, block_type):
    content_end = [TRIAL_BUFFER_DUR + TRIAL_CONTENT_DUR]

    corner_windows     = {c: [] for c in ALL_CORNERS}
    audio_windows      = []
    target_cat_windows = []
    item_windows       = {}
    visual_onsets      = []

    def is_corner_free(corner, start, end):
        return all(end <= ws or start >= we for (ws, we) in corner_windows[corner])

    def is_audio_free(snd_start, snd_end):
        return all(
            snd_end + MIN_AUDIO_GAP <= ws or snd_start >= we + MIN_AUDIO_GAP
            for (ws, we) in audio_windows
        )

    def is_item_free(item_name, start_vis, end_vis):
        windows = item_windows.get(item_name, [])
        return all(end_vis <= ws or start_vis >= we for (ws, we) in windows)

    def is_item_gap_free(item_name, start_vis, end_vis):
        windows = item_windows.get(item_name, [])
        return all(
            end_vis + MIN_SAME_ITEM_GAP <= ws or start_vis >= we + MIN_SAME_ITEM_GAP
            for (ws, we) in windows
        )

    def is_visual_onset_free(start_vis):
        return all(abs(start_vis - existing) >= MIN_VISUAL_ONSET_GAP
                   for existing in visual_onsets)

    def is_target_cat_slot_free(start_vis, end_vis, snd_start):
        zone_start = min(snd_start, start_vis) if snd_start is not None else start_vis
        zone_end   = end_vis + BETWEEN_PT_STIMULUS_GAP
        return all(zone_end <= ws or zone_start >= we
                   for (ws, we) in target_cat_windows)

    def register(corner, start_vis, peak_vis, end_vis, snd_start, snd_end, is_target, item_name):
        corner_windows[corner].append((start_vis, end_vis))
        visual_onsets.append(start_vis)
        if snd_start is not None:
            audio_windows.append((snd_start, snd_end))
        if is_target:
            zone_start = min(snd_start, start_vis) if snd_start is not None else start_vis
            zone_end   = end_vis + BETWEEN_PT_STIMULUS_GAP
            target_cat_windows.append((zone_start, zone_end))
        if item_name not in item_windows:
            item_windows[item_name] = []
        item_windows[item_name].append((start_vis, end_vis))

    def make_event(app, corner, start_vis, snd_start, snd_end):
        peak_vis  = start_vis + FADE_IN_DUR
        end_vis   = peak_vis + PEAK_HOLD_DUR + FADE_OUT_DUR
        is_target = app['role'] in ('PT', 'NPT')
        
        # --- JITTER CALCULATION ---
        # Sample the object center uniformly from anywhere in its quadrant,
        # with a 100px (half image size) clearance from the center axes and
        # screen edges so the object never crosses the quadrant boundary or
        # clips off screen. This gives the illusion of full-screen randomness
        # while preserving the quadrant structure for spatial analysis.
        half_img = IMAGE_SIZE[0] / 2          # 100px
        half_w   = actual_size[0] / 2         # 960px
        half_h   = actual_size[1] / 2         # 540px
        x_min    = half_img                   # 100px from center axis
        x_max    = half_w - half_img          # 860px from center axis
        y_min    = half_img                   # 100px from center axis
        y_max    = half_h - half_img          # 440px from center axis

        # Sign of each axis determines which quadrant
        x_sign = 1 if 'right' in corner else -1
        y_sign = 1 if 'top'   in corner else -1

        jittered_pos = [
            x_sign * random.uniform(x_min, x_max),
            y_sign * random.uniform(y_min, y_max),
        ]

        item_name = app['item']['name']
        vis_stim = IMAGE_STIM_CACHE.get(item_name)
        aud_stim = None
        snd_init_failed = False
        if app['sound'] and snd_start is not None:
            # Use preloaded Sound object — no blocking init at trial start
            cached_snd = SOUND_STIM_CACHE.get(item_name)
            if cached_snd is not None:
                try:
                    cached_snd.stop()  # reset playhead to start
                except Exception:
                    pass
                aud_stim = cached_snd
            else:
                print(f"  WARNING: no preloaded sound for {item_name} — audio skipped")
                snd_init_failed = True
                snd_start = None
                snd_end = None

        correct_key     = CORNER_TO_KEY[corner] if is_target else None
        resp_window_end = (start_vis + RESPONSE_WINDOW) if is_target else None

        return {
            'app_id':              app['app_id'],
            'role':                app['role'],
            'item':                app['item'],
            'friendly_name':       friendly_name(app['item']),
            'soa':                 app['soa'],
            'corner':              corner,
            'correct_key':         correct_key,
            'scheduled_start_vis': start_vis,
            'scheduled_peak_vis':  peak_vis,
            'scheduled_end_vis':   end_vis,
            'scheduled_start_snd': snd_start,
            'scheduled_end_snd':   snd_end,
            'vis_pos':             jittered_pos,
            'start_vis':           start_vis,
            'peak_vis':            peak_vis,
            'end_vis':             end_vis,
            'start_snd':           snd_start,
            'end_snd':             snd_end,
            'requested_start_snd': None,
            'response_window_end': resp_window_end,
            'vis_stim':            vis_stim,
            'aud_stim':            aud_stim,
            'sound_played':        False,
            'sound_is_playing':    False,
            'sound_failed':        snd_init_failed,
            'sound_stopped':       False,
            'sound_start_source':  'failed' if snd_init_failed else '',
            'visual_started':      False,
            'response_made':       False,
            'response_key':        None,
            'response_time':       None,
            'response_in_window':  False,
        }

    def find_free_time(corner, soa, item_name, n_attempts=400):
        content_start = TRIAL_BUFFER_DUR
        ce            = content_end[0]
        latest        = ce - STIM_DUR
        if latest < content_start:
            latest = content_start

        for _ in range(n_attempts):
            start_vis = round(random.uniform(content_start, latest), 3)
            peak_vis  = start_vis + FADE_IN_DUR
            end_vis   = peak_vis + PEAK_HOLD_DUR + FADE_OUT_DUR

            if not is_corner_free(corner, start_vis, end_vis):
                continue
            if not is_item_free(item_name, start_vis, end_vis):
                continue
            if not is_item_gap_free(item_name, start_vis, end_vis):
                continue
            if not is_visual_onset_free(start_vis):
                continue

            snd_start = snd_end = None
            if soa is not None:
                snd_start = peak_vis - soa
                if snd_start < 0:
                    continue
                snd_end   = snd_start + SOUND_DUR
                if not is_audio_free(snd_start, snd_end):
                    continue

            if not is_target_cat_slot_free(start_vis, end_vis, snd_start):
                continue

            return start_vis, snd_start, snd_end

        return None

    def find_free_time_distractor(corner, soa, item_name, n_attempts=400):
        content_start = TRIAL_BUFFER_DUR
        ce            = content_end[0]
        latest        = ce - STIM_DUR
        if latest < content_start:
            latest = content_start

        for _ in range(n_attempts):
            start_vis = round(random.uniform(content_start, latest), 3)
            peak_vis  = start_vis + FADE_IN_DUR
            end_vis   = peak_vis + PEAK_HOLD_DUR + FADE_OUT_DUR

            if not is_corner_free(corner, start_vis, end_vis):
                continue
            if not is_item_free(item_name, start_vis, end_vis):
                continue
            if not is_item_gap_free(item_name, start_vis, end_vis):
                continue
            if not is_visual_onset_free(start_vis):
                continue

            snd_start = snd_end = None
            if soa is not None:
                snd_start = peak_vis - soa
                if snd_start < 0:
                    continue
                snd_end   = snd_start + SOUND_DUR
                if not is_audio_free(snd_start, snd_end):
                    continue

            return start_vis, snd_start, snd_end

        return None

    pt_apps  = [a for a in appearances if a['role'] == 'PT']
    pd_apps  = [a for a in appearances if a['role'] == 'PD']
    npt_apps = [a for a in appearances if a['role'] == 'NPT']
    npd_apps = [a for a in appearances if a['role'] == 'NPD']

    timeline = []

    for app in pt_apps:
        item_name = app['item']['name']

        def draw_pt_corner():
            return ('top_right' if random.random() < TARGET_SPATIAL_BIAS
                    else random.choice(NON_BIASED_CORNERS))

        corner  = draw_pt_corner()
        result  = find_free_time(corner, app['soa'], item_name)
        if result is None:
            other = [c for c in ALL_CORNERS if c != corner]
            random.shuffle(other)
            for c in other:
                result = find_free_time(c, app['soa'], item_name)
                if result:
                    corner = c
                    break
        extends = 0
        while result is None and extends < MAX_WINDOW_EXTENDS:
            content_end[0] += WINDOW_EXTEND_SEC
            extends += 1
            print(f"  [WINDOW EXTEND] {app['app_id']} couldn't fit — "
                  f"extending to {content_end[0]:.1f}s (#{extends})")
            corner = draw_pt_corner()   
            result = find_free_time(corner, app['soa'], item_name)

        if result is None:
            print(f"  !! CRITICAL: Could not place {app['app_id']} — skipped.")
            continue

        start_vis, snd_start, snd_end = result
        peak_vis = start_vis + FADE_IN_DUR
        end_vis  = peak_vis + PEAK_HOLD_DUR + FADE_OUT_DUR
        register(corner, start_vis, peak_vis, end_vis, snd_start, snd_end,
                 is_target=True, item_name=item_name)
        timeline.append(make_event(app, corner, start_vis, snd_start, snd_end))

    for app in pd_apps:
        item_name = app['item']['name']
        corner    = random.choice(ALL_CORNERS)
        result    = find_free_time_distractor(corner, app['soa'], item_name)
        if result is None:
            other = [c for c in ALL_CORNERS if c != corner]
            random.shuffle(other)
            for c in other:
                result = find_free_time_distractor(c, app['soa'], item_name)
                if result:
                    corner = c
                    break
        if result is None:
            print(f"  WARNING: Could not place {app['app_id']} — skipped.")
            continue
        start_vis, snd_start, snd_end = result
        peak_vis = start_vis + FADE_IN_DUR
        end_vis  = peak_vis + PEAK_HOLD_DUR + FADE_OUT_DUR
        register(corner, start_vis, peak_vis, end_vis, snd_start, snd_end,
                 is_target=False, item_name=item_name)
        timeline.append(make_event(app, corner, start_vis, snd_start, snd_end))

    for app in npt_apps:
        item_name = app['item']['name']
        corner    = random.choice(ALL_CORNERS)
        result    = find_free_time(corner, None, item_name)
        if result is None:
            other = [c for c in ALL_CORNERS if c != corner]
            random.shuffle(other)
            for c in other:
                result = find_free_time(c, None, item_name)
                if result:
                    corner = c
                    break
        if result is None:
            print(f"  WARNING: Could not place {app['app_id']} — skipped.")
            continue
        start_vis, snd_start, snd_end = result
        peak_vis = start_vis + FADE_IN_DUR
        end_vis  = peak_vis + PEAK_HOLD_DUR + FADE_OUT_DUR
        register(corner, start_vis, peak_vis, end_vis, None, None,
                 is_target=True, item_name=item_name)
        timeline.append(make_event(app, corner, start_vis, None, None))

    for app in npd_apps:
        item_name = app['item']['name']
        corner    = random.choice(ALL_CORNERS)
        result    = find_free_time_distractor(corner, None, item_name)
        if result is None:
            other = [c for c in ALL_CORNERS if c != corner]
            random.shuffle(other)
            for c in other:
                result = find_free_time_distractor(c, None, item_name)
                if result:
                    corner = c
                    break
        if result is None:
            print(f"  WARNING: Could not place {app['app_id']} — skipped.")
            continue
        start_vis, snd_start, snd_end = result
        peak_vis = start_vis + FADE_IN_DUR
        end_vis  = peak_vis + PEAK_HOLD_DUR + FADE_OUT_DUR
        register(corner, start_vis, peak_vis, end_vis, None, None,
                 is_target=False, item_name=item_name)
        timeline.append(make_event(app, corner, start_vis, None, None))

    timeline.sort(key=lambda e: e['start_vis'])
    return timeline, content_end[0]


# ==============================================================================
# 10. TIMELINE VALIDATOR
# ==============================================================================

def validate_timeline(timeline):
    errors = []

    for i, ev1 in enumerate(timeline):
        for ev2 in timeline[i+1:]:
            if ev1['corner'] == ev2['corner']:
                if not (ev1['end_vis'] <= ev2['start_vis'] or ev2['end_vis'] <= ev1['start_vis']):
                    errors.append(
                        f"VISUAL OVERLAP [{ev1['corner']}]: "
                        f"{ev1['friendly_name']} {ev1['start_vis']:.2f}-{ev1['end_vis']:.2f}s "
                        f"vs {ev2['friendly_name']} {ev2['start_vis']:.2f}-{ev2['end_vis']:.2f}s"
                    )

    visual_onsets = sorted((ev['start_vis'], ev['friendly_name']) for ev in timeline)
    for i in range(len(visual_onsets) - 1):
        t1, n1 = visual_onsets[i]
        t2, n2 = visual_onsets[i + 1]
        gap = t2 - t1
        if gap < MIN_VISUAL_ONSET_GAP:
            errors.append(
                f"VISUAL ONSET GAP VIOLATION: {n1}@{t1:.3f}s vs {n2}@{t2:.3f}s "
                f"(gap={gap:.3f}s < {MIN_VISUAL_ONSET_GAP:.3f}s)"
            )

    same_item_events = {}
    for ev in timeline:
        same_item_events.setdefault(ev['item']['name'], []).append(ev)
    for item_name, item_events in same_item_events.items():
        item_events.sort(key=lambda ev: ev['start_vis'])
        for i in range(len(item_events) - 1):
            left = item_events[i]
            right = item_events[i + 1]
            if right['start_vis'] < left['end_vis']:
                errors.append(
                    f"SAME ITEM OVERLAP [{item_name}]: "
                    f"{left['friendly_name']} {left['start_vis']:.3f}-{left['end_vis']:.3f}s "
                    f"vs {right['start_vis']:.3f}-{right['end_vis']:.3f}s"
                )
                continue
            gap = right['start_vis'] - left['end_vis']
            if gap < MIN_SAME_ITEM_GAP:
                errors.append(
                    f"SAME ITEM GAP VIOLATION [{item_name}]: "
                    f"{left['friendly_name']} gap={gap:.3f}s < {MIN_SAME_ITEM_GAP:.3f}s"
                )

    audio = sorted(
        (ev['start_snd'], ev['end_snd'], ev['friendly_name'])
        for ev in timeline
        if ev['start_snd'] is not None and ev['end_snd'] is not None
    )
    for i, (s1, e1, n1) in enumerate(audio):
        for s2, e2, n2 in audio[i+1:]:
            gap = s2 - e1
            if gap < MIN_AUDIO_GAP:
                errors.append(
                    f"AUDIO GAP VIOLATION: {n1} {s1:.3f}-{e1:.3f}s vs "
                    f"{n2} {s2:.3f}-{e2:.3f}s (gap={gap:.3f}s < {MIN_AUDIO_GAP:.3f}s)"
                )

    if errors:
        print(f"✗ Validation FAILED — {len(errors)} issue(s):")
        for e in errors: print(f"    {e}")
    else:
        print("✓ Timeline valid")

    return len(errors) == 0, errors


def release_audio_stim(ev, context):
    aud_stim = ev.get('aud_stim')
    if aud_stim is None:
        return

    try:
        aud_stim.stop()
    except Exception as e:
        print(f"  WARNING: {context} stop() failed for {ev.get('friendly_name', '?')}: {e}")
    finally:
        # Do NOT delete the Sound object — it lives in SOUND_STIM_CACHE and is
        # reused across trials. Just clear the reference in this event dict.
        ev['aud_stim'] = None
        ev['sound_is_playing'] = False
        ev['sound_stopped'] = True


# ==============================================================================
# 11. CSV SETUP
# ==============================================================================

with open(data_filepath, 'w', newline='') as f:
    csv.writer(f).writerow([
        'appearance_id', 'role', 'object_id', 'object_name', 'category',
        'sound_lead_sec', 'corner', 'target_key',
        'fade_in_start', 'peak_opacity_time', 'fade_out_end',
        'sound_start', 'sound_end', 'response_deadline',
        'scheduled_fade_in_start', 'scheduled_peak_opacity_time', 'scheduled_fade_out_end',
        'scheduled_sound_start', 'scheduled_sound_end', 'requested_sound_start',
        'visual_onset_error_ms', 'sound_onset_error_ms', 'av_sync_error_ms', 'sound_start_source',
        'response_made', 'response_key', 'response_time', 'rt_from_fade_in',
        'response_in_window', 'response_correct',
        'participant_pid', 'block_type', 'trial_num', 'is_practice',
        'active_pt_name', 'active_pt_friendly',
    ])

with open(responses_filepath, 'w', newline='') as f:
    csv.writer(f).writerow([
        'keypress_time', 'key_pressed', 'response_type',
        'hit_object', 'hit_role', 'hit_corner', 'hit_sound_lead_sec',
        'rt_from_fade_in', 'rt_from_sound_start', 'hit_sound_start_source', 'response_in_window',
        'fa_pre_visual',
        'most_visible_object', 'most_visible_role', 'most_visible_opacity',
        'most_visible_corner', 'most_visible_sound_lead_sec',
        'sound_playing_object', 'sound_playing_role',
        'sounds_in_last_3sec', 'all_visible_at_keypress',
        'participant_pid', 'block_type', 'trial_num', 'is_practice',
        'active_pt_name', 'active_pt_friendly',
    ])

with open(trials_filepath, 'w', newline='') as f:
    csv.writer(f).writerow([
        'participant_pid', 'block_type', 'trial_num', 'is_practice',
        'active_pt_name', 'active_pt_friendly', 'active_pt_soa',
        'pt_corner_this_trial',
        'n_pt_appearances', 'n_npt_appearances',
        'n_pd_appearances', 'n_npd_appearances', 'total_appearances',
        'trial_duration_sec',
        'n_hits', 'n_false_alarms',
        'pt_hit_rate', 'npt_hit_rate',
        'measured_refresh_hz', 'mean_frame_ms', 'median_frame_ms',
        'max_frame_ms', 'n_long_frames',
    ])


def save_trial_data(trial_num, block_type, active_pt_name, timeline, is_practice):
    pt_item = next((ev['item'] for ev in timeline if ev['role'] == 'PT'), None)
    active_pt_friendly = friendly_name(pt_item) if pt_item else "UNKNOWN_PT"
    try:
        with open(data_filepath, 'a', newline='') as f:
            writer = csv.writer(f)
            for ev in timeline:
                rt = (ev['response_time'] - ev['start_vis']) if ev['response_time'] else ''
                if ev['visual_started']:
                    visual_onset_error_ms = round((ev['start_vis'] - ev['scheduled_start_vis']) * 1000, 3)
                else:
                    visual_onset_error_ms = 'NOT_DISPLAYED'
                sound_onset_error_ms = ''
                av_sync_error_ms = ''
                if ev['scheduled_start_snd'] is not None and ev['start_snd'] is not None:
                    sound_onset_error_ms = round((ev['start_snd'] - ev['scheduled_start_snd']) * 1000, 3)
                    if ev['visual_started']:
                        # Derived from the recorded timestamps, not external hardware.
                        planned_av_offset = ev['scheduled_start_vis'] - ev['scheduled_start_snd']
                        logged_av_offset = ev['start_vis'] - ev['start_snd']
                        av_sync_error_ms = round((logged_av_offset - planned_av_offset) * 1000, 3)

                if ev['role'] in ('PT', 'NPT'):
                    resp_corr = (ev['response_made'] and ev['response_in_window']
                                 and ev['response_key'] is not None
                                 and ev['response_key'] in ev['correct_key'])
                    response_in_window = ev['response_in_window']
                else:
                    resp_corr = False if ev['response_made'] else ''
                    response_in_window = 'N/A'

                writer.writerow([
                    ev.get('app_id', ''), ev['role'], ev['item']['name'],
                    ev['friendly_name'], ev['item']['cat'],
                    ev['soa'] if ev['soa'] is not None else '',
                    ev['corner'], ev['correct_key'][0] if ev['correct_key'] else '',
                    round(ev['start_vis'],  4), round(ev['peak_vis'], 4), round(ev['end_vis'], 4),
                    round(ev['start_snd'],  4) if ev['start_snd'] is not None else '',
                    round(ev['end_snd'],    4) if ev['end_snd']   is not None else '',
                    round(ev['response_window_end'], 4) if ev['response_window_end'] is not None else '',
                    round(ev['scheduled_start_vis'], 4), round(ev['scheduled_peak_vis'], 4), round(ev['scheduled_end_vis'], 4),
                    round(ev['scheduled_start_snd'], 4) if ev['scheduled_start_snd'] is not None else '',
                    round(ev['scheduled_end_snd'], 4) if ev['scheduled_end_snd'] is not None else '',
                    round(ev['requested_start_snd'], 4) if ev['requested_start_snd'] is not None else '',
                    visual_onset_error_ms, sound_onset_error_ms, av_sync_error_ms, ev.get('sound_start_source', ''),
                    ev['response_made'],
                    ev['response_key'] if ev['response_key'] else '',
                    round(ev['response_time'], 4) if ev['response_time'] else '',
                    round(rt, 4) if rt != '' else '',
                    response_in_window, resp_corr,
                    participant_pid, block_type, trial_num, is_practice,
                    active_pt_name, active_pt_friendly,
                ])
    except Exception as e:
        print(f"  !! ERROR saving trial data: {e}")


def snapshot_scene(timeline, t):
    visible = []
    for ev in timeline:
        if ev['start_vis'] <= t < ev['end_vis']:
            if t < ev['peak_vis']:
                opacity = (t - ev['start_vis']) / FADE_IN_DUR
            elif t < ev['peak_vis'] + PEAK_HOLD_DUR:
                opacity = 1.0
            else:
                opacity = 1.0 - (t - ev['peak_vis'] - PEAK_HOLD_DUR) / FADE_OUT_DUR
            opacity = max(0.0, min(1.0, opacity))
            if opacity > 0:
                visible.append((ev, round(opacity, 3)))

    visible.sort(key=lambda x: x[1], reverse=True)

    salient_ev      = visible[0][0] if visible else None
    salient_opacity = visible[0][1] if visible else 0.0

    sound_now_ev = next(
        (ev for ev in timeline
         if ev['start_snd'] is not None and ev['start_snd'] <= t <= ev['end_snd']),
        None
    )

    fa_pre_visual = (
        salient_ev is not None
        and salient_ev['start_snd'] is not None
        and salient_ev['start_snd'] <= t < salient_ev['peak_vis']
    )

    all_visible_str = '; '.join(
        f"{ev['friendly_name']}[{ev['role']}]@opacity={op}|corner={ev['corner']}"
        for ev, op in visible
    ) or 'nothing'

    return {
        'salient_ev':      salient_ev,
        'salient_opacity': salient_opacity,
        'fa_pre_visual':   fa_pre_visual,
        'sound_now_ev':    sound_now_ev,
        'all_visible_str': all_visible_str,
    }


def classify_fa_type(key, key_time, timeline, target_cat):
    target_visible = any(
        ev['item']['cat'] == target_cat and ev['start_vis'] <= key_time < ev['end_vis']
        for ev in timeline
    )
    target_recently_gone = any(
        ev['item']['cat'] == target_cat
        and ev['response_window_end'] is not None
        and ev['response_window_end'] < key_time <= ev['response_window_end'] + FA_LATE_GRACE_SEC
        and not ev['response_made']
        for ev in timeline
    )
    anything_visible = any(
        ev['start_vis'] <= key_time < ev['end_vis'] for ev in timeline
    )

    if target_visible:
        return 'fa_wrong_corner'   
    elif target_recently_gone:
        return 'fa_late'           
    elif anything_visible:
        return 'fa_no_target'      
    else:
        return 'fa_empty'          


def save_trial_summary(trial_num, block_type, is_practice, active_pt_name,
                       active_pt_friendly, timeline, trial_duration, n_false_alarms,
                       frame_stats):
    pt_evs  = [ev for ev in timeline if ev['role'] == 'PT']
    npt_evs = [ev for ev in timeline if ev['role'] == 'NPT']
    pd_evs  = [ev for ev in timeline if ev['role'] == 'PD']
    npd_evs = [ev for ev in timeline if ev['role'] == 'NPD']

    pt_corner = pt_evs[0]['corner'] if pt_evs else ''
    active_pt_soa = pt_evs[0]['soa'] if pt_evs else ''

    def hit_rate(evs):
        if not evs:
            return ''
        hits = sum(
            1 for ev in evs
            if ev['response_made'] and ev['response_in_window']
            and ev['response_key'] is not None
            and ev['response_key'] in ev['correct_key']
        )
        return round(hits / len(evs), 4)

    n_hits = sum(
        1 for ev in timeline
        if ev['role'] in ('PT', 'NPT')
        and ev['response_made'] and ev['response_in_window']
        and ev['response_key'] is not None
        and ev['response_key'] in ev['correct_key']
    )

    try:
        with open(trials_filepath, 'a', newline='') as f:
            csv.writer(f).writerow([
                participant_pid, block_type, trial_num, is_practice,
                active_pt_name, active_pt_friendly, active_pt_soa,
                pt_corner,
                len(pt_evs), len(npt_evs), len(pd_evs), len(npd_evs), len(timeline),
                round(trial_duration, 4),
                n_hits, n_false_alarms,
                hit_rate(pt_evs), hit_rate(npt_evs),
                round(frame_stats['refresh_hz'], 4) if frame_stats['refresh_hz'] is not None else '',
                round(frame_stats['mean_frame_ms'], 4) if frame_stats['mean_frame_ms'] is not None else '',
                round(frame_stats['median_frame_ms'], 4) if frame_stats['median_frame_ms'] is not None else '',
                round(frame_stats['max_frame_ms'], 4) if frame_stats['max_frame_ms'] is not None else '',
                frame_stats['n_long_frames'],
            ])
    except Exception as e:
        print(f"  !! ERROR saving trial summary: {e}")


SOUND_LOOKBACK_SEC = 3.0  

def save_response(trial_num, block_type, is_practice, active_pt_name, active_pt_friendly,
                  key, key_time, response_type, hit_ev, scene, sound_history):
    salient_ev = scene['salient_ev']
    sound_ev   = scene['sound_now_ev']

    recent = [
        e for e in sound_history
        if 0 <= key_time - e['fired_at'] <= SOUND_LOOKBACK_SEC
    ]
    recent.sort(key=lambda x: x['fired_at'], reverse=True)
    recent_sounds_str = '; '.join(
        f"{e['ev']['friendly_name']}[{e['ev']['role']}]@t={round(e['fired_at'], 4)}"
        for e in recent
    ) or 'none'

    rt_visual = rt_sound = in_window = None
    hit_item = hit_role = hit_corner = hit_soa = hit_sound_source = None
    if hit_ev:
        rt_visual  = round(key_time - hit_ev['start_vis'], 4)
        if hit_ev['start_snd'] is not None and not hit_ev.get('sound_failed'):
            rt_sound = round(key_time - hit_ev['start_snd'], 4)
        in_window  = hit_ev['response_in_window']
        hit_item   = hit_ev['friendly_name']
        hit_role   = hit_ev['role']
        hit_corner = hit_ev['corner']
        hit_soa    = hit_ev['soa']
        hit_sound_source = hit_ev.get('sound_start_source')

    try:
        with open(responses_filepath, 'a', newline='') as f:
            csv.writer(f).writerow([
                round(key_time, 4), key, response_type,
                hit_item, hit_role, hit_corner, hit_soa,
                rt_visual, rt_sound, hit_sound_source, in_window,
                scene['fa_pre_visual'],
                salient_ev['friendly_name'] if salient_ev else None,
                salient_ev['role']          if salient_ev else None,
                scene['salient_opacity'],
                salient_ev['corner']        if salient_ev else None,
                salient_ev['soa']           if salient_ev else None,
                sound_ev['friendly_name']   if sound_ev else None,
                sound_ev['role']            if sound_ev else None,
                recent_sounds_str,
                scene['all_visible_str'],
                participant_pid, block_type, trial_num, is_practice,
                active_pt_name, active_pt_friendly,
            ])
    except Exception as e:
        print(f"  !! ERROR saving response: {e}")


def phase_opacity(sample_time, start_vis, peak_vis):
    """Compute opacity from the actual onset/phase times."""
    if sample_time < peak_vis:
        opacity = (sample_time - start_vis) / FADE_IN_DUR
    elif sample_time < peak_vis + PEAK_HOLD_DUR:
        opacity = 1.0
    else:
        opacity = 1.0 - (sample_time - peak_vis - PEAK_HOLD_DUR) / FADE_OUT_DUR
    return max(0.0, min(MAX_OPACITY, opacity))


def summarize_frame_intervals(frame_intervals):
    """Return frame timing diagnostics for this trial."""
    if not frame_intervals:
        return {
            'refresh_hz': ACTIVE_REFRESH_HZ,
            'mean_frame_ms': None,
            'median_frame_ms': None,
            'max_frame_ms': None,
            'n_long_frames': 0,
        }

    intervals = np.array(frame_intervals, dtype=float)
    expected_frame_ms = FRAME_PERIOD_SEC * 1000.0
    median_frame_ms = float(np.median(intervals) * 1000.0)
    return {
        'refresh_hz': (1000.0 / median_frame_ms) if median_frame_ms > 0 else ACTIVE_REFRESH_HZ,
        'mean_frame_ms': float(np.mean(intervals) * 1000.0),
        'median_frame_ms': median_frame_ms,
        'max_frame_ms': float(np.max(intervals) * 1000.0),
        'n_long_frames': int(np.sum((intervals * 1000.0) > (expected_frame_ms * FRAME_DROP_THRESHOLD_FACTOR))),
    }


# ==============================================================================
# 12. DEBUG SCREEN
# ==============================================================================

def show_debug_screen(pt_group, pd_group_animate, npd_pool_animate,
                      pd_group_inanimate, npd_pool_inanimate):
    lines = [
        "━━━  DEBUG: Participant Stimulus Assignment  ━━━\n",
        "PRIVILEGED TARGETS  (sound plays a fixed amount before image appears — same every time)",
        f"  Sound lead time range: {PT_SOA_MIN}–{PT_SOA_MAX}s   "
        f"(e.g. 2.45s = sound plays 2.45s before image reaches full brightness)",
    ]
    for name, info in pt_group.items():
        lines.append(f"    [{info['item']['cat'].upper()[:4]}]  "
                     f"{friendly_name(info['item']):35s}  "
                     f"sound leads by {info['soa']:.2f}s (fixed)")

    lines.append("\n── ANIMATE BLOCK  (target = animate, distractors = inanimate) ──")
    lines.append("  Privileged Distractors  [have sound, but lead time is random every appearance]:")
    for name, info in pd_group_animate.items():
        lines.append(f"    [PD]   {friendly_name(info['item']):35s}  "
                     f"random lead {PD_SOA_MIN}–{PD_SOA_MAX}s each time")
    lines.append("  Non-Privileged Distractors  [no sound, visual only]:")
    for item in npd_pool_animate:
        lines.append(f"    [NPD]  {friendly_name(item)}")
    lines.append(f"  Pool sizes: {len(pd_group_animate)} PD  |  {len(npd_pool_animate)} NPD")

    lines.append("\n── INANIMATE BLOCK  (target = inanimate, distractors = animate) ──")
    lines.append("  Privileged Distractors  [have sound, but lead time is random every appearance]:")
    for name, info in pd_group_inanimate.items():
        lines.append(f"    [PD]   {friendly_name(info['item']):35s}  "
                     f"random lead {PD_SOA_MIN}–{PD_SOA_MAX}s each time")
    lines.append("  Non-Privileged Distractors  [no sound, visual only]:")
    for item in npd_pool_inanimate:
        lines.append(f"    [NPD]  {friendly_name(item)}")
    lines.append(f"  Pool sizes: {len(pd_group_inanimate)} PD  |  {len(npd_pool_inanimate)} NPD")

    lines.append(f"\n  Block order: {' → '.join(b.upper() for b in block_order)}")
    lines.append("\nPress any key to continue to instructions.")

    visual.TextStim(win, text='\n'.join(lines),
                    height=20, wrapWidth=1700, color='white', pos=[0, 0]).draw()
    win.flip()
    event.waitKeys()


# ==============================================================================
# 13. TRIAL RUNNER
# ==============================================================================

def run_trial(trial_num, block_type, active_pt_name, pt_group, pd_group, npd_pool, is_practice=False):
    appearances          = build_trial_appearances(block_type, pt_group, pd_group, npd_pool, active_pt_name)
    timeline, actual_content_end = build_timeline(appearances, block_type)
    is_valid, _          = validate_timeline(timeline)

    if not is_valid:
        print("  *** WARNING: Timeline issues detected. Continuing. ***")

    total_dur = actual_content_end + TRIAL_BUFFER_DUR

    active_pt_friendly = "UNKNOWN_PT"
    try:
        active_pt_friendly = friendly_name(pt_group[active_pt_name]['item'])
    except KeyError as e:
        print(f"  WARNING: active_pt_name '{active_pt_name}' not found in pt_group: {e}")

    print(f"\n  Trial {trial_num} ({block_type.upper()}) — "
          f"target group: {block_type.upper()} — duration: {total_dur:.1f}s")
    for ev in timeline:
        snd = (f"  sound@{ev['start_snd']:.2f}s (SOA {ev['soa']:.2f}s)"
               if ev['start_snd'] is not None else "")
        print(f"    [{ev['role']:3s}] {ev['friendly_name']:28s} {ev['corner']:13s} "
              f"vis={ev['start_vis']:.2f}-{ev['end_vis']:.2f}s{snd}")

    # Use the keyboard backend clock for both stimulus and response timing so
    # keypress.rt and our onset timestamps stay in the same timebase.
    trial_clock = SHARED_CLOCK
    trial_clock.reset()
    kb.clearEvents()

    sound_history = []
    false_alarms = 0
    frame_intervals = []
    last_flip_trial = None

    # ── DEBUG MARKERS ─────────────────────────────────────────────────────────
    # Controlled by DEBUG_OVERLAY in config -- flip to False before real runs.
    if DEBUG_OVERLAY:
        _hw, _hh = win.size[0] / 2, win.size[1] / 2
        debug_fix_h = visual.Line(win, start=(-_hw, 0), end=(_hw, 0), lineColor='white', lineWidth=1)
        debug_fix_v = visual.Line(win, start=(0, -_hh), end=(0, _hh), lineColor='white', lineWidth=1)
        debug_corner_dots = [
            visual.Circle(win, radius=8, pos=CORNERS[c], fillColor='red', lineColor='red')
            for c in ALL_CORNERS
        ]
        debug_timer = visual.TextStim(win, text='t=0.0000s | frame=0', pos=(0, -_hh + 30),
                                      height=22, color='yellow', bold=True)
    # ─────────────────────────────────────────────────────────────────────────

    frame_n = 0

    while trial_clock.getTime() < total_dur:
        t = trial_clock.getTime()

        noise_stims[(frame_n // BG_UPDATE_EVERY_FRAMES) % len(noise_stims)].draw()

        if DEBUG_OVERLAY:
            debug_fix_h.draw()
            debug_fix_v.draw()
            for dot in debug_corner_dots:
                dot.draw()
            debug_timer.text = (
                f't={t:.4f}s | frame={frame_n} | '
                f'display={ACTIVE_REFRESH_HZ:.2f}Hz'
            )
            debug_timer.draw()

        next_flip_trial = win.getFutureFlipTime(clock=trial_clock)
        next_flip_ptb = win.getFutureFlipTime(clock='ptb')
        frame_sample_t = next_flip_trial + HALF_FRAME_SEC

        frame_visual_onsets = []
        frame_sound_onsets = []
        for ev in timeline:
            if (ev['aud_stim'] is not None
                    and ev['sound_played']
                    and not ev.get('sound_stopped', False)
                    and ev['end_snd'] is not None
                    and t >= ev['end_snd']):
                try:
                    ev['aud_stim'].stop()
                except Exception as e:
                    print(f"  WARNING: stop() failed for {ev['friendly_name']}: {e}")
                ev['sound_is_playing'] = False
                ev['sound_stopped'] = True

            if (ev['scheduled_start_snd'] is not None and ev['aud_stim'] is not None
                    and not ev['sound_played']
                    and next_flip_trial >= ev['scheduled_start_snd'] - HALF_FRAME_SEC):
                try:
                    # sounddevice backend does not support when= — call play() directly.
                    # PTB's when= scheduling is not available here; post-flip latency
                    # is ~0.5–1 frame (8ms at 60Hz) which is acceptable on this hardware.
                    ev['aud_stim'].play()
                    ev['sound_played'] = True
                    frame_sound_onsets.append((ev, next_flip_trial, True))
                except Exception as e:
                    print(f"  ERROR playing sound: {e}")
                    ev['sound_played'] = True
                    ev['sound_failed'] = True
                    ev['start_snd'] = None
                    ev['end_snd'] = None
                    ev['sound_start_source'] = 'failed'
                    ev['sound_is_playing'] = False
                    ev['sound_stopped'] = True

            if not ev['visual_started']:
                visual_start = ev['scheduled_start_vis']
                peak_vis = ev['scheduled_peak_vis']
                visual_end = ev['scheduled_end_vis']
                if visual_start <= next_flip_trial < visual_end:
                    frame_visual_onsets.append(ev)
                    visual_start = next_flip_trial
                    peak_vis = visual_start + FADE_IN_DUR
                    visual_end = peak_vis + PEAK_HOLD_DUR + FADE_OUT_DUR
            else:
                visual_start = ev['start_vis']
                peak_vis = ev['peak_vis']
                visual_end = ev['end_vis']

            if ev['vis_stim'] is not None and visual_start <= frame_sample_t < visual_end:
                ev['vis_stim'].pos = ev['vis_pos']
                ev['vis_stim'].opacity = phase_opacity(next_flip_trial, visual_start, peak_vis)
                ev['vis_stim'].draw()

        flip_time_default = win.flip()
        flip_time = (
            default_clock_to(trial_clock, flip_time_default)
            if flip_time_default is not None else trial_clock.getTime()
        )
        if last_flip_trial is not None:
            frame_intervals.append(flip_time - last_flip_trial)
        last_flip_trial = flip_time
        frame_n += 1

        for ev in frame_visual_onsets:
            if ev['visual_started']:
                continue
            ev['visual_started'] = True
            ev['start_vis'] = flip_time
            ev['peak_vis'] = flip_time + FADE_IN_DUR
            ev['end_vis'] = ev['peak_vis'] + PEAK_HOLD_DUR + FADE_OUT_DUR
            if ev['role'] in ('PT', 'NPT'):
                ev['response_window_end'] = ev['start_vis'] + RESPONSE_WINDOW

        for ev, requested_sound_time, needs_postflip_play in frame_sound_onsets:
            if needs_postflip_play:
                # sounddevice: play() already called in scheduling block above;
                # log the actual post-flip time as the onset timestamp.
                start_snd = trial_clock.getTime()
                ev['sound_start_source'] = 'sounddevice_postflip'
            else:
                start_snd = requested_sound_time
                ev['sound_start_source'] = 'ptb_preflight'
            ev['requested_start_snd'] = requested_sound_time if requested_sound_time is not None else start_snd
            ev['start_snd'] = start_snd
            ev['end_snd'] = start_snd + SOUND_DUR
            ev['sound_is_playing'] = True
            ev['sound_stopped'] = False
            sound_history.append({'ev': ev, 'fired_at': start_snd})

        keys = kb.getKeys(keyList=ALL_RESPONSE_KEYS + ['escape'], waitRelease=False, clear=True)
        for keypress in keys:
            key = keypress.name
            key_time = keypress.rt
            if key == 'escape':
                save_trial_data(trial_num, block_type, active_pt_name, timeline, is_practice)
                for ev in timeline:
                    release_audio_stim(ev, context='escape cleanup')
                win.close()
                core.quit()

            elif key in ALL_RESPONSE_KEYS:
                target_cat = block_type
                scene      = snapshot_scene(timeline, key_time)

                hit_ev = None
                for ev in timeline:
                    if (ev['visual_started']
                            and ev['item']['cat'] == target_cat
                            and not ev['response_made']
                            and key in ev['correct_key']
                            and ev['start_vis'] <= key_time <= ev['response_window_end']):
                        hit_ev = ev
                        break

                if hit_ev:
                    hit_ev['response_made']      = True
                    hit_ev['response_key']       = key
                    hit_ev['response_time']      = key_time
                    hit_ev['response_in_window'] = True

                    response_type = 'hit'
                    rt = key_time - hit_ev['start_vis']
                    print(f"  ✓ [{hit_ev['role']:3s}] {hit_ev['friendly_name']} "
                          f"key={key} RT={rt:.3f}s | "
                          f"salient: {scene['salient_ev']['friendly_name'] if scene['salient_ev'] else 'none'} | "
                          f"sound: {scene['sound_now_ev']['friendly_name'] if scene['sound_now_ev'] else 'none'}")

                    save_response(trial_num, block_type, is_practice,
                                  active_pt_name, active_pt_friendly,
                                  key, key_time, response_type,
                                  hit_ev, scene, sound_history)

                else:
                    fa_type = classify_fa_type(key, key_time, timeline, target_cat)
                    false_alarms += 1
                    matched_late_ev = None

                    if fa_type == 'fa_late':
                        for ev in timeline:
                            if (ev['item']['cat'] == target_cat
                                    and not ev['response_made']
                                    and key in ev['correct_key']
                                    and ev['response_window_end'] is not None
                                    and ev['response_window_end'] < key_time <= ev['response_window_end'] + FA_LATE_GRACE_SEC):
                                ev['response_made']      = True
                                ev['response_key']       = key
                                ev['response_time']      = key_time
                                ev['response_in_window'] = False
                                matched_late_ev = ev
                                break

                    salient = scene['salient_ev']
                    snd_now = scene['sound_now_ev']
                    print(f"  ✗ FA [{fa_type}] key={key} t={key_time:.3f}s | "
                          f"salient: {salient['friendly_name'] if salient else 'nothing'} "
                          f"({scene['salient_opacity']:.0%}) | "
                          f"sound: {snd_now['friendly_name'] if snd_now else 'none'} | "
                          f"pre-vis: {scene['fa_pre_visual']}")

                    save_response(trial_num, block_type, is_practice,
                                  active_pt_name, active_pt_friendly,
                                  key, key_time, fa_type,
                                  matched_late_ev, scene, sound_history)

    for ev in timeline:
        release_audio_stim(ev, context='trial cleanup')

    save_trial_data(trial_num, block_type, active_pt_name, timeline, is_practice)
    frame_stats = summarize_frame_intervals(frame_intervals)

    valid_responses = sum(
        1 for ev in timeline
        if ev['role'] in ('PT', 'NPT')
        and ev['response_made']
        and ev['response_in_window']
        and ev['response_key'] is not None
        and ev['response_key'] in ev['correct_key']
    )

    if frame_stats['mean_frame_ms'] is not None:
        print(f"  Frame timing: median={frame_stats['median_frame_ms']:.3f} ms | "
              f"max={frame_stats['max_frame_ms']:.3f} ms | "
              f"long frames={frame_stats['n_long_frames']}")

    active_pt_friendly_local = "UNKNOWN_PT"
    try:
        active_pt_friendly_local = friendly_name(pt_group[active_pt_name]['item'])
    except KeyError:
        pass
    save_trial_summary(
        trial_num, block_type, is_practice,
        active_pt_name, active_pt_friendly_local,
        timeline, total_dur, false_alarms, frame_stats,
    )

    return {
        'valid_responses': valid_responses,
        'false_alarms':    false_alarms,
        'target_group':    block_type.upper(),
        'total_stimuli':   len(timeline),
    }


# ==============================================================================
# 14. EXPERIMENT SETUP & ASSIGNMENT
# ==============================================================================

pt_group = assign_pt_group()

pd_group_animate,   npd_pool_animate   = assign_pd_group(pt_group, 'animate')
pd_group_inanimate, npd_pool_inanimate = assign_pd_group(pt_group, 'inanimate')

block_order = random.choice([['animate', 'inanimate'], ['inanimate', 'animate']])

print("\nPT Group:")
for name, info in pt_group.items():
    print(f"  {friendly_name(info['item'])} — SOA {info['soa']}s")
print(f"\nPD Animate block: {[friendly_name(v['item']) for v in pd_group_animate.values()]}")
print(f"PD Inanimate block: {[friendly_name(v['item']) for v in pd_group_inanimate.values()]}")
print(f"Block order: {block_order}")

show_debug_screen(pt_group, pd_group_animate, npd_pool_animate,
                  pd_group_inanimate, npd_pool_inanimate)


# ==============================================================================
# 15. INSTRUCTIONS
# ==============================================================================

visual.TextStim(
    win,
    text="""Welcome to the AV Spatiotemporal Awareness Study

You will see objects appear and disappear in the corners of the screen.
Some objects will be accompanied by sounds.

YOUR TASK:
When you see your TARGET object appear, press the NUMPAD key
matching the corner where it appeared — as quickly as possible.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    4 = Top Left     |  5 = Top Right
    1 = Bottom Left  |  2 = Bottom Right
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You have 1.5 seconds after the target appears to respond.
Only respond when you see YOUR TARGET — ignore everything else.

Press any key to begin the practice trial.""",
    height=26, wrapWidth=1400, color='white'
).draw()
win.flip()
event.waitKeys()


# ==============================================================================
# 16. PRACTICE
# ==============================================================================

practice_schedule = []
for pt_name, pt_info in pt_group.items():
    cat          = pt_info['item']['cat']
    cat_pt_group = {k: v for k, v in pt_group.items() if v['item']['cat'] == cat}
    pd_g         = pd_group_animate   if cat == 'animate' else pd_group_inanimate
    npd_p        = npd_pool_animate   if cat == 'animate' else npd_pool_inanimate
    practice_schedule.append({
        'block_type': cat,
        'pt_name':    pt_name,
        'pt_group':   cat_pt_group,
        'pd_group':   pd_g,
        'npd_pool':   npd_p,
    })

random.shuffle(practice_schedule)  

total_practice = len(practice_schedule)

for p, prac in enumerate(practice_schedule):
    pt_label = friendly_name(prac['pt_group'][prac['pt_name']]['item'])
    visual.TextStim(
        win,
        text=f"PRACTICE TRIAL {p+1}/{total_practice}\n\n"
             f"Find your {prac['block_type'].upper()} target and press its corner.\n"
             f"(Target this trial: {pt_label})\n\n"
             f"Press any key to begin.",
        height=28, wrapWidth=1400, color='yellow'
    ).draw()
    win.flip()
    event.waitKeys()

    print(f"\n{'='*70}\nPRACTICE TRIAL {p+1} — {prac['block_type'].upper()} block\n{'='*70}")
    stats = run_trial(
        p + 1,
        prac['block_type'],
        prac['pt_name'],
        prac['pt_group'],
        prac['pd_group'],
        prac['npd_pool'],
        is_practice=True,
    )

    visual.TextStim(
        win,
        text=f"Practice Trial {p+1}/{total_practice} Complete!\n\n"
             f"Valid target responses: {stats['valid_responses']}\n"
             f"False alarms: {stats['false_alarms']}\n\nPress any key to continue.",
        height=26, wrapWidth=1400, color='white'
    ).draw()
    win.flip()
    event.waitKeys()


# ==============================================================================
# 17. REAL TRIALS
# ==============================================================================

visual.TextStim(
    win,
    text=f"Practice complete! Now beginning REAL TRIALS.\n\n"
         f"Block order: {block_order[0].upper()} → {block_order[1].upper()}\n\n"
         f"Press any key to begin.",
    height=28, wrapWidth=1400, color='white'
).draw()
win.flip()
event.waitKeys()


def make_pt_sequence(block_type, pt_group, n_trials):
    block_pts = [k for k, v in pt_group.items() if v['item']['cat'] == block_type]

    if ALLOW_BOTH_PTS_SAME_TRIAL or len(block_pts) == 1:
        return [random.choice(block_pts) for _ in range(n_trials)]

    pt_a, pt_b   = block_pts[0], block_pts[1]
    n_a          = (n_trials + 1) // 2
    n_b          = n_trials - n_a
    raw_sequence = [pt_a] * n_a + [pt_b] * n_b

    if PT_SUBBLOCK_ORDER == 'grouped':
        return raw_sequence
    elif PT_SUBBLOCK_ORDER == 'alternating':
        seq = []
        for i in range(n_trials):
            seq.append(pt_a if i % 2 == 0 else pt_b)
        return seq[:n_trials]
    elif PT_SUBBLOCK_ORDER == 'random':
        random.shuffle(raw_sequence)
        return raw_sequence
    else:
        print(f"  WARNING: Unknown PT_SUBBLOCK_ORDER '{PT_SUBBLOCK_ORDER}' — defaulting to random.")
        random.shuffle(raw_sequence)
        return raw_sequence


trial_counter = 0
block_config  = {
    'animate':   (NUM_ANIMATE_TRIALS,   pd_group_animate,   npd_pool_animate),
    'inanimate': (NUM_INANIMATE_TRIALS, pd_group_inanimate, npd_pool_inanimate),
}

for block_type in block_order:
    n_trials, pd_group, npd_pool = block_config[block_type]
    pt_sequence = make_pt_sequence(block_type, pt_group, n_trials)

    block_pts   = {k: v for k, v in pt_group.items() if v['item']['cat'] == block_type}
    pt_name_map = {k: friendly_name(v['item']) for k, v in block_pts.items()}
    subblock_str = ' → '.join(pt_name_map[p] for p in pt_sequence[:6])
    if n_trials > 6:
        subblock_str += f'  … ({n_trials} trials total)'

    visual.TextStim(
        win,
        text=f"Beginning {block_type.upper()} BLOCK\n\n"
             f"{n_trials} trials — find your {block_type} target!\n\n"
             f"Sub-block order (first 6): {subblock_str}\n\n"
             f"Press any key to start.",
        height=26, wrapWidth=1500, color='cyan'
    ).draw()
    win.flip()
    event.waitKeys()

    for t in range(n_trials):
        trial_counter  += 1
        active_pt_name  = pt_sequence[t]
        active_pt_label = friendly_name(pt_group[active_pt_name]['item'])

        print(f"\n{'='*70}\nTRIAL {trial_counter} — {block_type.upper()} "
              f"({t+1}/{n_trials})\n{'='*70}")

        stats = run_trial(trial_counter, block_type, active_pt_name,
                          pt_group, pd_group, npd_pool, is_practice=False)

        is_last = (trial_counter == NUM_ANIMATE_TRIALS + NUM_INANIMATE_TRIALS)
        visual.TextStim(
            win,
            text=f"Trial {t+1}/{n_trials} Complete!\n\n"
                 f"Valid target responses: {stats['valid_responses']}\n"
                 f"False alarms: {stats['false_alarms']}\n\n"
                 f"{'Press any key to continue.' if not is_last else 'Press any key for summary.'}",
            height=26, wrapWidth=1400, color='white'
        ).draw()
        win.flip()
        event.waitKeys()


# ==============================================================================
# 18. FINAL SUMMARY
# ==============================================================================

total_target_appearances, total_valid, total_fa = 0, 0, 0
try:
    with open(data_filepath, 'r') as f:
        for row in csv.DictReader(f):
            if row['is_practice'] == 'False' and row['role'] in ('PT', 'NPT'):
                total_target_appearances += 1
    with open(responses_filepath, 'r') as f:
        for row in csv.DictReader(f):
            if row['is_practice'] == 'False':
                if row['response_type'] == 'hit':   
                    total_valid += 1
                elif row['response_type'].startswith('fa_'):
                    total_fa += 1
except Exception as e:
    print(f"  WARNING: Could not read summary: {e}")

hit_rate = (total_valid / total_target_appearances * 100) if total_target_appearances > 0 else 0

visual.TextStim(
    win,
    text=f"Experiment Complete!\n\nParticipant: {participant_pid}\n\n"
         f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
         f"Target Appearances: {total_target_appearances}\n"
         f"Valid Responses: {total_valid} ({hit_rate:.1f}%)\n"
         f"False Alarms: {total_fa}\n"
         f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
         f"Data saved to:\n{data_filename}\n{responses_filename}\n{trials_filename}\n\n"
         f"Thank you!\n\nPress any key to exit.",
    height=24, wrapWidth=1400, color='white'
).draw()
win.flip()
event.waitKeys()

win.close()
core.quit()