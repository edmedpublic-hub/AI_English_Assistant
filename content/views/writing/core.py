# content/views/writing/core.py
#
# Shared utilities, evaluation logic, and helper functions
# used across all writing views.
#
# Nothing in this file handles HTTP requests directly.
# Everything here is called by hub.py, teach.py, practice.py, test.py.
#
# Responsibilities:
#   - Stage unlock logic (is this stage available to this student?)
#   - Automatic evaluation (capital, full stop, word count, verb, keywords)
#   - Sentence-level intervention detection (paragraph stages onward)
#   - Cooldown enforcement
#   - Mastery grant logic
#   - AI evaluation call (Anthropic API)
#   - Cooldown task generation

import re
import json
import logging
from datetime import timedelta

from django.utils import timezone
from django.conf import settings

from content.models.writing import (
    WritingStage,
    WritingStageContent,
    WritingAttempt,
    WritingStageMastery,
    WritingIntervention,
    WritingAcademicYear,
    PHASE_DISSECT,
    PHASE_IMITATE,
    PHASE_PRODUCE,
    EVAL_AUTOMATIC,
    EVAL_KEYWORD,
    EVAL_TEACHER,
    EVAL_AI_TEACHER,
    STATUS_PENDING,
    STATUS_PASSED,
    STATUS_FAILED,
    STATUS_COOLDOWN,
    STATUS_APPROVED,
    TIER_SENTENCE,
    TIER_PARAGRAPH,
    TIER_GENRE,
)

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================

COOLDOWN_HOURS = 24

# Coordinating conjunctions — Stage 3 check
COORDINATING_CONJUNCTIONS = {
    "for", "and", "nor", "but", "or", "yet", "so"
}

# Subordinating conjunctions — Stage 4 check
SUBORDINATING_CONJUNCTIONS = {
    "after", "although", "as", "because", "before",
    "even though", "if", "in order that", "once",
    "provided that", "since", "so that", "though",
    "unless", "until", "when", "whenever", "where",
    "wherever", "while", "whether",
}

# Common English verbs for verb-presence check
# This is a practical list — not exhaustive, but covers
# the most common verbs a matric student would use
COMMON_VERB_PATTERNS = re.compile(
    r'\b(is|are|was|were|am|be|been|being|'
    r'has|have|had|'
    r'do|does|did|'
    r'will|would|shall|should|'
    r'can|could|may|might|must|'
    r'go|goes|went|gone|'
    r'come|comes|came|'
    r'get|gets|got|'
    r'make|makes|made|'
    r'take|takes|took|'
    r'see|sees|saw|'
    r'know|knows|knew|'
    r'think|thinks|thought|'
    r'look|looks|looked|'
    r'want|wants|wanted|'
    r'give|gives|gave|'
    r'use|uses|used|'
    r'find|finds|found|'
    r'tell|tells|told|'
    r'ask|asks|asked|'
    r'seem|seems|seemed|'
    r'feel|feels|felt|'
    r'try|tries|tried|'
    r'leave|leaves|left|'
    r'call|calls|called|'
    r'keep|keeps|kept|'
    r'let|lets|'
    r'begin|begins|began|'
    r'show|shows|showed|'
    r'hear|hears|heard|'
    r'play|plays|played|'
    r'run|runs|ran|'
    r'move|moves|moved|'
    r'live|lives|lived|'
    r'believe|believes|believed|'
    r'hold|holds|held|'
    r'bring|brings|brought|'
    r'happen|happens|happened|'
    r'write|writes|wrote|'
    r'provide|provides|provided|'
    r'sit|sits|sat|'
    r'stand|stands|stood|'
    r'lose|loses|lost|'
    r'pay|pays|paid|'
    r'meet|meets|met|'
    r'include|includes|included|'
    r'continue|continues|continued|'
    r'set|sets|'
    r'learn|learns|learned|learnt|'
    r'change|changes|changed|'
    r'lead|leads|led|'
    r'understand|understands|understood|'
    r'watch|watches|watched|'
    r'follow|follows|followed|'
    r'stop|stops|stopped|'
    r'create|creates|created|'
    r'speak|speaks|spoke|'
    r'read|reads|'
    r'spend|spends|spent|'
    r'grow|grows|grew|'
    r'open|opens|opened|'
    r'walk|walks|walked|'
    r'win|wins|won|'
    r'offer|offers|offered|'
    r'remember|remembers|remembered|'
    r'love|loves|loved|'
    r'consider|considers|considered|'
    r'appear|appears|appeared|'
    r'buy|buys|bought|'
    r'wait|waits|waited|'
    r'serve|serves|served|'
    r'die|dies|died|'
    r'send|sends|sent|'
    r'expect|expects|expected|'
    r'build|builds|built|'
    r'stay|stays|stayed|'
    r'fall|falls|fell|'
    r'cut|cuts|'
    r'reach|reaches|reached|'
    r'kill|kills|killed|'
    r'raise|raises|raised|'
    r'pass|passes|passed|'
    r'sell|sells|sold|'
    r'decide|decides|decided|'
    r'return|returns|returned|'
    r'explain|explains|explained|'
    r'hope|hopes|hoped|'
    r'develop|develops|developed|'
    r'carry|carries|carried|'
    r'break|breaks|broke|'
    r'receive|receives|received|'
    r'agree|agrees|agreed|'
    r'support|supports|supported|'
    r'hit|hits|'
    r'produce|produces|produced|'
    r'eat|eats|ate|'
    r'cover|covers|covered|'
    r'catch|catches|caught|'
    r'draw|draws|drew|'
    r'choose|chooses|chose|'
    r'cause|causes|caused|'
    r'require|requires|required|'
    r'report|reports|reported)\b',
    re.IGNORECASE
)


# ============================================================
# ACADEMIC YEAR HELPERS
# ============================================================

def get_current_academic_year():
    """
    Return the current WritingAcademicYear or None.
    Logs a warning if no current year is set —
    admin must set one before students can attempt writing.
    """
    year = WritingAcademicYear.get_current()
    if not year:
        logger.warning(
            "No current academic year set. "
            "Admin must mark one WritingAcademicYear as current."
        )
    return year


# ============================================================
# STAGE UNLOCK LOGIC
# ============================================================

def get_stage_status(user, content, academic_year):
    """
    Return the status of a stage for a given student.

    Returns one of:
        'locked'      — previous stage not yet mastered
        'available'   — unlocked, not yet started
        'in_progress' — student has attempts but not mastered
        'mastered'    — student has mastered this stage this year

    content: WritingStageContent instance
    academic_year: WritingAcademicYear instance
    """
    # Check mastery first — fastest path
    if WritingStageMastery.objects.filter(
        user=user,
        content=content,
        academic_year=academic_year,
    ).exists():
        return "mastered"

    # Check if previous stage is mastered (gate check)
    previous_stage = content.stage.unlocks_after()
    if previous_stage:
        # Find the content record for the previous stage in the same unit
        try:
            previous_content = WritingStageContent.objects.get(
                stage=previous_stage,
                unit=content.unit,
            )
        except WritingStageContent.DoesNotExist:
            # Previous stage content not prepared yet — locked
            return "locked"

        previous_mastered = WritingStageMastery.objects.filter(
            user=user,
            content=previous_content,
            academic_year=academic_year,
        ).exists()

        if not previous_mastered:
            return "locked"

    # Has the student started this stage?
    has_attempts = WritingAttempt.objects.filter(
        user=user,
        content=content,
        academic_year=academic_year,
    ).exists()

    return "in_progress" if has_attempts else "available"


def get_all_stage_statuses(user, unit, academic_year):
    """
    Return a list of dicts describing all stages for a unit,
    with status for the given student.

    Used by hub.py to render the staircase journey.

    Returns:
    [
        {
            'content': WritingStageContent,
            'stage': WritingStage,
            'status': 'locked' | 'available' | 'in_progress' | 'mastered',
            'current_phase': 'dissect' | 'imitate' | 'produce' | None,
            'is_in_cooldown': bool,
            'cooldown_ends_at': datetime | None,
        },
        ...
    ]
    """
    contents = (
        WritingStageContent.objects
        .filter(unit=unit, is_complete=True)
        .select_related("stage")
        .order_by("stage__number")
    )

    result = []
    for content in contents:
        status       = get_stage_status(user, content, academic_year)
        current_phase = get_current_phase(user, content, academic_year)
        cooldown_info = get_cooldown_info(user, content, academic_year)

        result.append({
            "content":         content,
            "stage":           content.stage,
            "status":          status,
            "current_phase":   current_phase,
            "is_in_cooldown":  cooldown_info["is_in_cooldown"],
            "cooldown_ends_at": cooldown_info["ends_at"],
        })

    return result


def get_current_phase(user, content, academic_year):
    """
    Return which phase the student should work on next for this stage.

    Logic:
    - If no attempts → None (student chooses entry point)
    - If Produce passed/approved → None (stage complete)
    - If Produce failed and in cooldown → 'cooldown'
    - If Dissect not completed → 'dissect'
    - If Imitate not completed → 'imitate'
    - Otherwise → 'produce'
    """
    attempts = WritingAttempt.objects.filter(
        user=user,
        content=content,
        academic_year=academic_year,
    ).order_by("-created_at")

    if not attempts.exists():
        return None

    # Check if already mastered
    if WritingStageMastery.objects.filter(
        user=user,
        content=content,
        academic_year=academic_year,
    ).exists():
        return None

    # Check cooldown on latest produce attempt
    latest_produce = attempts.filter(phase=PHASE_PRODUCE).first()
    if latest_produce and latest_produce.is_in_cooldown():
        return "cooldown"

    # Check if dissect is done
    dissect_passed = attempts.filter(
        phase=PHASE_DISSECT,
        status__in=(STATUS_PASSED, STATUS_APPROVED),
    ).exists()

    # Check if imitate is done
    imitate_passed = attempts.filter(
        phase=PHASE_IMITATE,
        status__in=(STATUS_PASSED, STATUS_APPROVED),
    ).exists()

    # Route to next needed phase
    if not dissect_passed:
        return PHASE_DISSECT
    if not imitate_passed:
        return PHASE_IMITATE
    return PHASE_PRODUCE


def get_cooldown_info(user, content, academic_year):
    """
    Return cooldown information for a student's latest Produce attempt.
    """
    latest_produce = (
        WritingAttempt.objects
        .filter(
            user=user,
            content=content,
            academic_year=academic_year,
            phase=PHASE_PRODUCE,
        )
        .order_by("-created_at")
        .first()
    )

    if not latest_produce or not latest_produce.is_in_cooldown():
        return {"is_in_cooldown": False, "ends_at": None}

    return {
        "is_in_cooldown": True,
        "ends_at": latest_produce.next_attempt_allowed_at,
    }


# ============================================================
# AUTOMATIC EVALUATION
# ============================================================

def evaluate_automatic(response_text, content, phase):
    """
    Run automatic checks on a student's response.

    Checks applied depend on stage number — checks accumulate:
    Stage 1: capital + full_stop + min_word_count + verb
    Stage 2: + adjective/adverb present
    Stage 3: + coordinating conjunction
    Stage 4: + subordinating conjunction
    Stage 5: + both coordinating AND subordinating
    Stage 6+: + keyword check (if required_keywords set)

    Returns:
    {
        'passed': bool,
        'score': int (0-100),
        'checks': {
            'capital_start': bool,
            'full_stop_end': bool,
            'min_word_count': bool,
            'verb_present': bool,
            ... (stage-dependent checks)
        },
        'keywords_found': [...],
        'keywords_missing': [...],
        'word_count': int,
        'feedback': str  — plain English summary for student
    }
    """
    text        = response_text.strip()
    stage_num   = content.stage.number
    min_words   = content.get_min_words()
    keywords    = content.get_required_keywords_list()

    checks      = {}
    feedback_parts = []

    # ── Check 1: Capital letter start ─────────────────────
    checks["capital_start"] = bool(text) and text[0].isupper()
    if not checks["capital_start"]:
        feedback_parts.append(
            "Start your sentence with a capital letter."
        )

    # ── Check 2: Full stop end ────────────────────────────
    checks["full_stop_end"] = bool(text) and text[-1] in ".!?"
    if not checks["full_stop_end"]:
        feedback_parts.append(
            "End your sentence with a full stop."
        )

    # ── Check 3: Minimum word count ───────────────────────
    word_count = len(text.split())
    checks["min_word_count"] = word_count >= min_words
    if not checks["min_word_count"]:
        feedback_parts.append(
            f"Your response is too short. "
            f"Write at least {min_words} words. "
            f"You wrote {word_count}."
        )

    # ── Check 4: Verb present (all stages) ────────────────
    checks["verb_present"] = bool(COMMON_VERB_PATTERNS.search(text))
    if not checks["verb_present"]:
        feedback_parts.append(
            "Your sentence needs a verb — "
            "a word that shows an action or a state. "
            "Example: run, is, was, seems."
        )

    # ── Check 5: Adjective or adverb (Stage 2+) ──────────
    if stage_num >= 2:
        adj_adv_pattern = re.compile(
            r'\b(very|quite|rather|really|extremely|'
            r'slowly|quickly|carefully|suddenly|'
            r'beautiful|beautiful|tall|short|old|young|'
            r'big|small|large|little|good|bad|happy|'
            r'sad|angry|bright|dark|warm|cold|'
            r'clearly|quietly|loudly|strongly|deeply|'
            r'nearly|almost|always|never|often|'
            r'hard|fast|early|late|long|high|low)\b',
            re.IGNORECASE
        )
        checks["modifier_present"] = bool(
            adj_adv_pattern.search(text)
        )
        if not checks["modifier_present"]:
            feedback_parts.append(
                "Add a describing word — an adjective or adverb — "
                "to expand your sentence. "
                "Example: 'The old man walked slowly.'"
            )

    # ── Check 6: Coordinating conjunction (Stage 3+) ──────
    if stage_num >= 3:
        words_lower = set(re.findall(r'\b\w+\b', text.lower()))
        found_coord = words_lower & COORDINATING_CONJUNCTIONS
        checks["coordinating_conjunction"] = bool(found_coord)
        if not checks["coordinating_conjunction"]:
            feedback_parts.append(
                "Use a joining word to connect two ideas. "
                "Try: for, and, but, or, yet, so."
            )

    # ── Check 7: Subordinating conjunction (Stage 4+) ─────
    if stage_num >= 4:
        found_sub = _find_subordinating_conjunction(text)
        checks["subordinating_conjunction"] = bool(found_sub)
        if not checks["subordinating_conjunction"]:
            feedback_parts.append(
                "Use a word that shows a relationship between ideas. "
                "Try: because, although, when, if, since, while."
            )

    # ── Check 8: Both conjunction types (Stage 5+) ────────
    if stage_num >= 5:
        has_both = (
            checks.get("coordinating_conjunction", False)
            and checks.get("subordinating_conjunction", False)
        )
        checks["both_conjunction_types"] = has_both
        if not has_both:
            feedback_parts.append(
                "A compound-complex sentence needs both a joining word "
                "(and, but, or) AND a relationship word "
                "(because, although, when)."
            )

    # ── Check 9: Keywords (Stage 6+) ─────────────────────
    keywords_found   = []
    keywords_missing = []
    if stage_num >= 6 and keywords:
        text_lower = text.lower()
        for kw in keywords:
            if kw.lower() in text_lower:
                keywords_found.append(kw)
            else:
                keywords_missing.append(kw)
        checks["keywords_present"] = len(keywords_missing) == 0
        if keywords_missing:
            feedback_parts.append(
                f"Use these words from the unit in your writing: "
                f"{', '.join(keywords_missing)}."
            )

    # ── Calculate score ───────────────────────────────────
    total_checks = len(checks)
    passed_checks = sum(1 for v in checks.values() if v)
    score = int((passed_checks / total_checks) * 100) if total_checks else 0

    all_passed = all(checks.values())

    # Build feedback string
    if all_passed:
        feedback = "Well done. Your response passes all checks."
    else:
        feedback = " ".join(feedback_parts)

    return {
        "passed":           all_passed,
        "score":            score,
        "checks":           checks,
        "keywords_found":   keywords_found,
        "keywords_missing": keywords_missing,
        "word_count":       word_count,
        "feedback":         feedback,
    }


def _find_subordinating_conjunction(text):
    """
    Check for subordinating conjunctions in text.
    Handles multi-word conjunctions like 'even though'.
    """
    text_lower = text.lower()
    for conj in SUBORDINATING_CONJUNCTIONS:
        if conj in text_lower:
            return conj
    return None


# ============================================================
# SENTENCE-LEVEL INTERVENTION DETECTION
# ============================================================

def detect_sentence_interventions(response_text, stage_number):
    """
    Split a paragraph into sentences and check each one
    for structural problems.

    Only applied for paragraph stages (Stage 6+).

    Returns a list of dicts:
    [
        {
            'sentence': str,
            'issue': str,       — plain English problem description
            'fix_exercise': str — targeted exercise for the student
        },
        ...
    ]
    Returns empty list if no issues found.
    """
    if stage_number < 6:
        return []

    # Split into sentences
    sentences = _split_into_sentences(response_text)
    interventions = []

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        issue        = None
        fix_exercise = None

        # Check 1: No capital letter
        if sentence and not sentence[0].isupper():
            issue = "This sentence does not start with a capital letter."
            fix_exercise = (
                f"Rewrite this sentence starting with a capital letter: "
                f'"{sentence}"'
            )

        # Check 2: No full stop
        elif sentence and sentence[-1] not in ".!?":
            issue = "This sentence does not end with a full stop."
            fix_exercise = (
                f"Add the correct punctuation at the end of this sentence: "
                f'"{sentence}"'
            )

        # Check 3: No verb detected
        elif not COMMON_VERB_PATTERNS.search(sentence):
            issue = "This sentence may not have a verb."
            fix_exercise = (
                f"Add an action word or state word to complete this sentence: "
                f'"{sentence}"'
            )

        # Check 4: Very short — likely a fragment
        elif len(sentence.split()) < 3:
            issue = (
                "This looks like an incomplete sentence — "
                "it is too short to express a complete idea."
            )
            fix_exercise = (
                f"Expand this into a complete sentence with a subject "
                f'and a verb: "{sentence}"'
            )

        if issue:
            interventions.append({
                "sentence":     sentence,
                "issue":        issue,
                "fix_exercise": fix_exercise,
            })

    return interventions


def _split_into_sentences(text):
    """
    Split text into individual sentences.
    Handles common abbreviations to avoid false splits.
    """
    # Protect common abbreviations
    protected = text
    abbreviations = [
        "Mr.", "Mrs.", "Ms.", "Dr.", "Prof.",
        "St.", "etc.", "e.g.", "i.e.", "vs.",
    ]
    for abbr in abbreviations:
        protected = protected.replace(abbr, abbr.replace(".", "DOTPROTECT"))

    # Split on sentence-ending punctuation
    raw_sentences = re.split(r'(?<=[.!?])\s+', protected)

    # Restore abbreviations
    sentences = [
        s.replace("DOTPROTECT", ".") for s in raw_sentences
    ]
    return sentences


# ============================================================
# COOLDOWN TASK GENERATION
# ============================================================

def generate_cooldown_task(evaluation_result, content):
    """
    Generate a directed focus task to show the student
    immediately on the fail screen.

    The task is specific to what failed — not a generic message.

    Returns a plain English string the student reads
    during their 24-hour cooldown.
    """
    checks   = evaluation_result.get("checks", {})
    stage    = content.stage
    tasks    = []

    if not checks.get("capital_start", True):
        tasks.append(
            "Practice: Write five sentences. "
            "Check that every sentence starts with a capital letter."
        )

    if not checks.get("full_stop_end", True):
        tasks.append(
            "Practice: Write five sentences. "
            "Check that every sentence ends with a full stop."
        )

    if not checks.get("verb_present", True):
        tasks.append(
            "Go back to the Grammar section and review verbs. "
            "Then write three sentences — each with a clear action word."
        )

    if not checks.get("min_word_count", True):
        min_words = content.get_min_words()
        tasks.append(
            f"Your response was too short. "
            f"Before your next attempt, write a practice response "
            f"of at least {min_words} words on the same topic."
        )

    if not checks.get("modifier_present", True):
        tasks.append(
            "Go back to the Dissect phase and study how the model sentence "
            "uses describing words. "
            "Write three sentences each containing an adjective or adverb."
        )

    if not checks.get("coordinating_conjunction", True):
        tasks.append(
            "Study these joining words: for, and, nor, but, or, yet, so. "
            "Write three compound sentences — "
            "each joining two simple sentences with one of these words."
        )

    if not checks.get("subordinating_conjunction", True):
        tasks.append(
            "Study these relationship words: "
            "because, although, when, if, since, while. "
            "Write three complex sentences using one of these words in each."
        )

    if not checks.get("keywords_present", True):
        missing = evaluation_result.get("keywords_missing", [])
        if missing:
            tasks.append(
                f"You did not use these required words: "
                f"{', '.join(missing)}. "
                f"Look them up in the unit vocabulary section. "
                f"Write a sentence for each word before your next attempt."
            )

    if not tasks:
        tasks.append(
            "Read the model sentence in the Dissect phase again carefully. "
            "Think about what makes it a good "
            f"{stage.name.lower()}. "
            "Then try again tomorrow."
        )

    cooldown_task = (
        f"Before your next attempt tomorrow, complete these tasks:\n\n"
        + "\n\n".join(f"{i+1}. {t}" for i, t in enumerate(tasks))
    )

    return cooldown_task


# ============================================================
# MASTERY GRANT LOGIC
# ============================================================

def grant_mastery(user, content, academic_year, attempt):
    """
    Create a WritingStageMastery record.
    Safe to call multiple times — uses get_or_create.

    Returns (mastery_record, created_bool).
    """
    mastery, created = WritingStageMastery.objects.get_or_create(
        user=user,
        content=content,
        academic_year=academic_year,
        defaults={
            "mastered_at":     timezone.now(),
            "mastered_via":    content.stage.eval_method,
            "mastery_attempt": attempt,
        },
    )
    return mastery, created


# ============================================================
# ATTEMPT NUMBER HELPER
# ============================================================

def get_next_attempt_number(user, content, academic_year, phase):
    """
    Return the next attempt number for a student's submission.
    Counts all previous attempts for this user/content/year/phase.
    """
    last = (
        WritingAttempt.objects
        .filter(
            user=user,
            content=content,
            academic_year=academic_year,
            phase=phase,
        )
        .order_by("-attempt_number")
        .first()
    )
    return (last.attempt_number + 1) if last else 1


# ============================================================
# AI EVALUATION
# ============================================================

def evaluate_with_ai(response_text, content):
    """
    Send the student's Produce response to the Anthropic API
    for evaluation.

    Returns:
    {
        'score': int (0-100),
        'feedback': str,
        'rubric_scores': dict,
        'error': str | None
    }

    If the API call fails, returns a safe fallback
    so the student sees a pending status rather than an error.
    """
    try:
        import anthropic
    except ImportError:
        logger.error(
            "anthropic package not installed. "
            "Run: pip install anthropic"
        )
        return _ai_fallback("AI evaluation is not available right now.")

    stage    = content.stage
    unit     = content.unit
    rubric   = content.ai_rubric
    min_words = content.get_min_words()

    # Build the evaluation prompt
    system_prompt = _build_ai_system_prompt()
    user_prompt   = _build_ai_user_prompt(
        response_text=response_text,
        stage_name=stage.name,
        stage_description=stage.description,
        produce_prompt=content.produce_prompt,
        unit_title=unit.title,
        class_level=unit.textbook.class_level,
        min_words=min_words,
        rubric=rubric,
        required_keywords=content.get_required_keywords_list(),
    )

    try:
        client   = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        message  = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": user_prompt}],
            system=system_prompt,
        )

        raw_text = message.content[0].text
        return _parse_ai_response(raw_text)

    except Exception as e:
        logger.error(f"AI evaluation failed: {e}")
        return _ai_fallback(
            "AI evaluation could not be completed. "
            "Your teacher will review your work."
        )


def _build_ai_system_prompt():
    return """You are an English writing evaluator for Pakistani matric and 
intermediate students (Class 9-12). These students have an Urdu-medium 
background and are building English writing skills from the ground up.

Your job is to evaluate student writing fairly, kindly, and specifically 
against Pakistani board exam standards — not Cambridge or American standards.

You must respond ONLY with a valid JSON object. No preamble. No explanation 
outside the JSON. The JSON must have exactly these keys:
{
    "score": <integer 0-100>,
    "rubric_scores": {<criterion>: <integer score>},
    "feedback": "<string — plain English feedback for the student>",
    "strengths": "<string — what the student did well>",
    "improvements": "<string — specific things to improve>"
}

Feedback rules:
- Write feedback in simple English a Class 9 student can understand
- Be specific — name what is good and what to fix
- Be kind — never mock or discourage
- Be actionable — tell the student exactly what to do differently
- Keep feedback under 150 words
- Never use linguistic jargon the student would not know"""


def _build_ai_user_prompt(
    response_text,
    stage_name,
    stage_description,
    produce_prompt,
    unit_title,
    class_level,
    min_words,
    rubric,
    required_keywords,
):
    rubric_str = (
        json.dumps(rubric, indent=2)
        if rubric
        else '{"content": {"max_score": 40}, '
             '"organisation": {"max_score": 30}, '
             '"language": {"max_score": 30}}'
    )

    keywords_str = (
        ", ".join(required_keywords)
        if required_keywords
        else "None specified"
    )

    return f"""STUDENT PROFILE:
Class level: {class_level}
Writing stage: {stage_name}
Stage description: {stage_description}

WRITING TASK:
{produce_prompt}

REQUIREMENTS:
- Minimum word count: {min_words} words
- Required vocabulary words: {keywords_str}

EVALUATION RUBRIC:
{rubric_str}

STUDENT'S RESPONSE:
{response_text}

Evaluate this response against the rubric. 
Consider the student's class level and Urdu-medium background.
Apply Pakistani board exam standards.
Respond with the JSON object only."""


def _parse_ai_response(raw_text):
    """
    Parse the AI's JSON response.
    Falls back gracefully if JSON is malformed.
    """
    try:
        # Strip markdown code fences if present
        clean = raw_text.strip()
        if clean.startswith("```"):
            clean = re.sub(r'^```[a-z]*\n?', '', clean)
            clean = re.sub(r'\n?```$', '', clean)
            clean = clean.strip()

        data = json.loads(clean)

        return {
            "score":         int(data.get("score", 0)),
            "feedback":      data.get("feedback", ""),
            "rubric_scores": data.get("rubric_scores", {}),
            "strengths":     data.get("strengths", ""),
            "improvements":  data.get("improvements", ""),
            "error":         None,
        }
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.error(f"Failed to parse AI response: {e}\nRaw: {raw_text}")
        return _ai_fallback(
            "AI evaluation result could not be read. "
            "Your teacher will review your work."
        )


def _ai_fallback(message):
    return {
        "score":         0,
        "feedback":      message,
        "rubric_scores": {},
        "strengths":     "",
        "improvements":  "",
        "error":         message,
    }


# ============================================================
# CONTEXT HELPERS  — used by views to build template context
# ============================================================

def build_stage_context(user, content, academic_year):
    """
    Build the common context dict shared across
    teach, practice, and test views for a given stage.
    """
    status        = get_stage_status(user, content, academic_year)
    current_phase = get_current_phase(user, content, academic_year)
    cooldown_info = get_cooldown_info(user, content, academic_year)

    # Latest attempt per phase
    base_qs = WritingAttempt.objects.filter(
        user=user,
        content=content,
        academic_year=academic_year,
    )

    latest_dissect = (
        base_qs.filter(phase=PHASE_DISSECT)
        .order_by("-created_at").first()
    )
    latest_imitate = (
        base_qs.filter(phase=PHASE_IMITATE)
        .order_by("-created_at").first()
    )
    latest_produce = (
        base_qs.filter(phase=PHASE_PRODUCE)
        .order_by("-created_at").first()
    )

    return {
        "content":        content,
        "stage":          content.stage,
        "unit":           content.unit,
        "academic_year":  academic_year,
        "stage_status":   status,
        "current_phase":  current_phase,
        "is_in_cooldown": cooldown_info["is_in_cooldown"],
        "cooldown_ends_at": cooldown_info["ends_at"],
        "latest_dissect": latest_dissect,
        "latest_imitate": latest_imitate,
        "latest_produce": latest_produce,
        "phase_dissect_done": (
            latest_dissect is not None
            and latest_dissect.status in (STATUS_PASSED, STATUS_APPROVED)
        ),
        "phase_imitate_done": (
            latest_imitate is not None
            and latest_imitate.status in (STATUS_PASSED, STATUS_APPROVED)
        ),
        "phase_produce_done": (
            latest_produce is not None
            and latest_produce.status in (STATUS_PASSED, STATUS_APPROVED)
        ),
    }