import re
from django.utils.html import escape
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import PronunciationAttempt, ReadingLesson

# Helper utilities (same logic as your frontend helpers but server-side too)
def clean_word(w):
    return (w or "").lower().strip().strip(".,!?;:\"'()[]{}")

def levenshtein(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    m, n = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if a[j - 1] == b[i - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    return dp[n][m]

def soundex(word):
    # simple soundex (same family as frontend)
    w = clean_word(word)
    if not w:
        return ""
    w = w.lower()
    codes = {'b':'1','f':'1','p':'1','v':'1','c':'2','g':'2','j':'2','k':'2','q':'2','s':'2','x':'2','z':'2',
             'd':'3','t':'3','l':'4','m':'5','n':'5','r':'6'}
    first = w[0]
    res = first.upper()
    prev = codes.get(first, '')
    for ch in w[1:]:
        code = codes.get(ch, '')
        if code != prev:
            res += code
        prev = code
    return (res + "000")[:4]

@api_view(["POST"])
@permission_classes([AllowAny])
def feedback_view(request):
    """
    POST payload expected:
    {
      "expected": "full lesson text or sentence(s)",
      "spoken": "transcribed student speech",
      "lesson_id": optional int
    }
    Returns:
    {
      "score": 85.5,
      "feedback": "...",
      "mispronounced": [{"word":"laurels","suggest":"laurels","type":"substitution"} ...]
      "attempt_id": 123 (if saved)
    }
    """
    data = request.data or {}
    expected_text = data.get("expected", "") or ""
    spoken_text = data.get("spoken", "") or ""
    lesson_id = data.get("lesson_id")

    # quick safety
    expected_text = expected_text.strip()
    spoken_text = spoken_text.strip()

    # break into words (simple)
    expected_words = [clean_word(w) for w in re.split(r"\s+", expected_text) if clean_word(w)]
    spoken_words = [clean_word(w) for w in re.split(r"\s+", spoken_text) if clean_word(w)]

    # alignment: simple left-to-right compare with heuristics
    mispronounced = []
    correct_count = 0
    for i, ew in enumerate(expected_words):
        sw = spoken_words[i] if i < len(spoken_words) else ""
        if ew == sw:
            correct_count += 1
            continue
        # soundex similarity
        if soundex(ew) == soundex(sw) and ew:
            correct_count += 1
            continue
        # edit distance similarity
        dist = levenshtein(ew, sw)
        max_len = max(len(ew), len(sw), 1)
        similarity = 1 - (dist / max_len)
        if similarity >= 0.6:
            correct_count += 1
            continue
        # otherwise flagged
        mispronounced.append({"word": ew, "heard": sw, "distance": dist})

    total = len(expected_words) or 1
    score = round((correct_count / total) * 100, 2)

    # friendly feedback generation (short)
    if score >= 90:
        fb = "Excellent pronunciation. Keep it up!"
    elif score >= 75:
        fb = "Good job — a few words need attention."
    elif score >= 50:
        fb = "Fair — work on clearer enunciation of some words."
    else:
        fb = "Needs practice — focus on articulation and pacing."

    # optional: save attempt
    attempt_id = None
    try:
        attempt = PronunciationAttempt.objects.create(
            lesson_id=lesson_id if lesson_id else None,
            expected=expected_text,
            spoken=spoken_text,
            score=score,
            mispronounced=mispronounced,
            feedback=fb
        )
        attempt_id = attempt.id
    except Exception:
        attempt_id = None  # don't fail if DB save fails

    return Response({
        "score": score,
        "feedback": fb,
        "mispronounced": mispronounced,
        "attempt_id": attempt_id,
    })
