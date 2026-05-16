import math
from collections import deque

wave_positions  = deque(maxlen=14)
gesture_history = deque(maxlen=9)

def detect_gesture(hand_landmarks):
    lm = hand_landmarks.landmark

    def dist(a, b):
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

    wrist      = lm[0]
    thumb_mcp  = lm[2]
    thumb_ip   = lm[3]
    thumb_tip  = lm[4]

    index_mcp  = lm[5]
    index_pip  = lm[6]
    index_tip  = lm[8]

    middle_mcp = lm[9]
    middle_pip = lm[10]
    middle_tip = lm[12]

    ring_mcp   = lm[13]
    ring_pip   = lm[14]
    ring_tip   = lm[16]

    pinky_mcp  = lm[17]
    pinky_pip  = lm[18]
    pinky_tip  = lm[20]

    # Hand size = wrist to middle MCP (stable reference)
    hand_size = dist(wrist, middle_mcp) or 1e-6

    # ── Core helpers ──────────────────────────────────────────────────────────

    def is_extended(tip, pip):
        """Tip is farther from wrist than PIP → finger is open."""
        return dist(tip, wrist) > dist(pip, wrist) * 1.1

    def is_curled(tip, mcp):
        """Tip is closer to wrist than MCP → finger is definitely folded."""
        return dist(tip, wrist) < dist(mcp, wrist) * 1.05

    # Four fingers
    idx = is_extended(index_tip,  index_pip)
    mid = is_extended(middle_tip, middle_pip)
    rng = is_extended(ring_tip,   ring_pip)
    pnk = is_extended(pinky_tip,  pinky_pip)

    idx_curl = is_curled(index_tip,  index_mcp)
    mid_curl = is_curled(middle_tip, middle_mcp)
    rng_curl = is_curled(ring_tip,   ring_mcp)
    pnk_curl = is_curled(pinky_tip,  pinky_mcp)

    # Thumb: tip higher than IP = thumb up
    thumb_up   = thumb_tip.y < thumb_ip.y - 0.025
    thumb_down = thumb_tip.y > thumb_ip.y + 0.025
    # Thumb curled inward: tip close to index MCP
    thumb_in   = dist(thumb_tip, index_mcp) / hand_size < 0.55

    count_up = sum([idx, mid, rng, pnk])

    # ── 1. HELLO — open hand waving side to side ──────────────────────────────
    wave_positions.append(wrist.x)
    is_waving = False
    if len(wave_positions) == wave_positions.maxlen and count_up == 4:
        xs = list(wave_positions)
        changes = sum(
            1 for i in range(1, len(xs) - 1)
            if (xs[i] - xs[i-1]) * (xs[i+1] - xs[i]) < 0
        )
        is_waving = changes >= 3 and (max(xs) - min(xs)) > 0.08

    # ── 2. STOP — all 4 fingers + thumb extended ──────────────────────────────
    is_stop = count_up == 4 and thumb_up

    # ── 3. THANK YOU — closed fist (ALL tips closer to wrist than their MCP) ──
    # Using distance-to-wrist comparison: robust regardless of hand orientation
    is_fist = idx_curl and mid_curl and rng_curl and pnk_curl

    # ── 4. OKAY — thumb up, all four fingers curled ───────────────────────────
    is_okay = thumb_up and idx_curl and mid_curl and rng_curl and pnk_curl

    # ── 5. NO — only index finger extended ────────────────────────────────────
    is_no = idx and not mid and not rng and not pnk

    # ── 6. PEACE ✌️ — index + middle up, ring + pinky curled ─────────────────
    is_peace = idx and mid and not rng and not pnk and rng_curl and pnk_curl

    # ── 7. CALL ME 🤙 — thumb + pinky up, index + middle + ring curled ────────
    is_call = thumb_up and pnk and idx_curl and mid_curl and rng_curl

    # ── 8. VULCAN SALUTE 🖖 — index + middle up AND ring + pinky up, gap between groups ─
    # All 4 fingers extended, thumb free, middle and ring tips spread apart
    is_vulcan = (
        idx and mid and rng and pnk and
        dist(middle_tip, ring_tip) / hand_size > 0.2
    )

    # ── 9. I LOVE YOU 🤟 — index + pinky + thumb up, middle + ring curled ──────
    is_ily = idx and pnk and thumb_up and mid_curl and rng_curl and not mid and not rng

    # ── 10. DISLIKE 👎 — thumb pointing down, all fingers curled ────────────────
    is_dislike = thumb_down and idx_curl and mid_curl and rng_curl and pnk_curl

    # ── Priority (most specific / overlapping first) ──────────────────────────
    if is_waving:
        raw = "HELLO"
    elif is_okay:           # thumb_up + all curled  (subset of stop, check first)
        raw = "OKAY"
    elif is_stop:
        raw = "STOP"
    elif is_call:           # thumb + pinky
        raw = "CALL ME"
    elif is_peace:          # index + middle
        raw = "PEACE"
    elif is_ily:            # index + pinky + thumb
        raw = "I LOVE YOU"
    elif is_vulcan:         # all 4 fingers up with spread between middle & ring
        raw = "GREETINGS"
    elif is_no:             # index only
        raw = "NO"
    elif is_dislike:
        raw = "DISLIKE"
    elif is_fist:
        raw = "THANK YOU"
    else:
        raw = ""

    # ── Smoothing: majority vote over last 9 frames ───────────────────────────
    gesture_history.append(raw)
    if len(gesture_history) == gesture_history.maxlen:
        counts = {}
        for g in gesture_history:
            counts[g] = counts.get(g, 0) + 1
        best = max(counts, key=counts.get)
        if counts[best] >= 5:
            return best
    return raw
