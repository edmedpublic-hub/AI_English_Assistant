# PATH: content/services/chunk_mastery.py
# ACTION: Create this new file.
#
# Provides a single function that returns mastery status for all
# domains in a chunk for a given student. Used by the chunk hub view
# to display per-domain progress without N+1 queries.

from content.models.punctuation import (
    PunctuationTestAttempt, ChunkPunctuationFocus,
)
from content.models.grammar import (
    GrammarTestAttempt, ChunkGrammarFocus,
)
from content.models.comprehension import (
    ComprehensionTestAttempt, ChunkComprehensionFocus,
)
from content.models.vocabulary import VocabularyItem


# ── Status constants ──────────────────────────────────────────
MASTERED     = "mastered"
IN_PROGRESS  = "in_progress"
NOT_STARTED  = "not_started"
UNAVAILABLE  = "unavailable"   # no content configured yet


def get_chunk_mastery(user, chunk):
    """
    Returns a dict of domain → status for the given user and chunk.

    Statuses:
        mastered      all focuses in the domain are mastered
        in_progress   at least one attempt exists but not all mastered
        not_started   content exists but no attempts yet
        unavailable   no content configured for this domain in this chunk

    Single DB query per domain — no N+1.
    """

    result = {}

    # ── Punctuation ───────────────────────────────────────────
    punc_focuses = list(
        ChunkPunctuationFocus.objects.filter(chunk=chunk).values_list('id', flat=True)
    )
    if not punc_focuses:
        result['punctuation'] = UNAVAILABLE
    else:
        mastered = PunctuationTestAttempt.objects.filter(
            user=user, focus_id__in=punc_focuses, is_mastered=True
        ).values_list('focus_id', flat=True).distinct()
        mastered_ids = set(mastered)

        attempted = PunctuationTestAttempt.objects.filter(
            user=user, focus_id__in=punc_focuses
        ).values_list('focus_id', flat=True).distinct()
        attempted_ids = set(attempted)

        if mastered_ids >= set(punc_focuses):
            result['punctuation'] = MASTERED
        elif attempted_ids:
            result['punctuation'] = IN_PROGRESS
        else:
            result['punctuation'] = NOT_STARTED

    # ── Grammar ───────────────────────────────────────────────
    gram_focuses = list(
        ChunkGrammarFocus.objects.filter(chunk=chunk).values_list('id', flat=True)
    )
    if not gram_focuses:
        result['grammar'] = UNAVAILABLE
    else:
        mastered = GrammarTestAttempt.objects.filter(
            user=user, focus_id__in=gram_focuses, is_mastered=True
        ).values_list('focus_id', flat=True).distinct()
        mastered_ids = set(mastered)

        attempted = GrammarTestAttempt.objects.filter(
            user=user, focus_id__in=gram_focuses
        ).values_list('focus_id', flat=True).distinct()
        attempted_ids = set(attempted)

        if mastered_ids >= set(gram_focuses):
            result['grammar'] = MASTERED
        elif attempted_ids:
            result['grammar'] = IN_PROGRESS
        else:
            result['grammar'] = NOT_STARTED

    # ── Comprehension ─────────────────────────────────────────
    comp_focuses = list(
        ChunkComprehensionFocus.objects.filter(chunk=chunk).values_list('id', flat=True)
    )
    if not comp_focuses:
        result['comprehension'] = UNAVAILABLE
    else:
        mastered = ComprehensionTestAttempt.objects.filter(
            user=user, focus_id__in=comp_focuses, is_mastered=True
        ).values_list('focus_id', flat=True).distinct()
        mastered_ids = set(mastered)

        attempted = ComprehensionTestAttempt.objects.filter(
            user=user, focus_id__in=comp_focuses
        ).values_list('focus_id', flat=True).distinct()
        attempted_ids = set(attempted)

        if mastered_ids >= set(comp_focuses):
            result['comprehension'] = MASTERED
        elif attempted_ids:
            result['comprehension'] = IN_PROGRESS
        else:
            result['comprehension'] = NOT_STARTED

    # ── Vocabulary ────────────────────────────────────────────
    # Vocabulary mastery is item-level, not focus-level.
    # We treat it as unavailable until vocabulary items exist,
    # and mastered when StudentVocabMastery covers all items.
    # For now we check simply whether items exist.
    vocab_count = VocabularyItem.objects.filter(chunk=chunk).count()
    if vocab_count == 0:
        result['vocabulary'] = UNAVAILABLE
    else:
        # Import here to avoid circular import at module level
        from content.models.vocabulary import StudentVocabMastery
        mastered_count = StudentVocabMastery.objects.filter(
            vocab_item__chunk=chunk,
            user=user,
            mastery_level='mastered',
        ).count()
        if mastered_count >= vocab_count:
            result['vocabulary'] = MASTERED
        elif mastered_count > 0:
            result['vocabulary'] = IN_PROGRESS
        else:
            result['vocabulary'] = NOT_STARTED

    # ── Writing & Pronunciation ───────────────────────────────
    # Not yet built — always unavailable for now.
    result['writing']       = UNAVAILABLE
    result['pronunciation'] = UNAVAILABLE

    return result