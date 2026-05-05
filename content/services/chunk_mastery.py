# PATH: content/services/chunk_mastery.py

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

MASTERED    = "mastered"
IN_PROGRESS = "in_progress"
NOT_STARTED = "not_started"
UNAVAILABLE = "unavailable"


def get_chunk_mastery(user, chunk):
    """
    Returns a dict of domain → status for the given user and chunk.

    Statuses:
        mastered      all content for this domain is mastered
        in_progress   at least one attempt exists but not all mastered
        not_started   content exists but no attempts yet
        unavailable   no content configured for this domain
    """

    result = {}

    # ── Punctuation ───────────────────────────────────────────
    punc_focuses = list(
        ChunkPunctuationFocus.objects.filter(
            chunk=chunk
        ).values_list('id', flat=True)
    )
    if not punc_focuses:
        result['punctuation'] = UNAVAILABLE
    else:
        mastered_ids = set(
            PunctuationTestAttempt.objects.filter(
                user=user, focus_id__in=punc_focuses, is_mastered=True
            ).values_list('focus_id', flat=True).distinct()
        )
        attempted_ids = set(
            PunctuationTestAttempt.objects.filter(
                user=user, focus_id__in=punc_focuses
            ).values_list('focus_id', flat=True).distinct()
        )
        if mastered_ids >= set(punc_focuses):
            result['punctuation'] = MASTERED
        elif attempted_ids:
            result['punctuation'] = IN_PROGRESS
        else:
            result['punctuation'] = NOT_STARTED

    # ── Grammar ───────────────────────────────────────────────
    gram_focuses = list(
        ChunkGrammarFocus.objects.filter(
            chunk=chunk
        ).values_list('id', flat=True)
    )
    if not gram_focuses:
        result['grammar'] = UNAVAILABLE
    else:
        mastered_ids = set(
            GrammarTestAttempt.objects.filter(
                user=user, focus_id__in=gram_focuses, is_mastered=True
            ).values_list('focus_id', flat=True).distinct()
        )
        attempted_ids = set(
            GrammarTestAttempt.objects.filter(
                user=user, focus_id__in=gram_focuses
            ).values_list('focus_id', flat=True).distinct()
        )
        if mastered_ids >= set(gram_focuses):
            result['grammar'] = MASTERED
        elif attempted_ids:
            result['grammar'] = IN_PROGRESS
        else:
            result['grammar'] = NOT_STARTED

    # ── Comprehension ─────────────────────────────────────────
    comp_focuses = list(
        ChunkComprehensionFocus.objects.filter(
            chunk=chunk
        ).values_list('id', flat=True)
    )
    if not comp_focuses:
        result['comprehension'] = UNAVAILABLE
    else:
        mastered_ids = set(
            ComprehensionTestAttempt.objects.filter(
                user=user, focus_id__in=comp_focuses, is_mastered=True
            ).values_list('focus_id', flat=True).distinct()
        )
        attempted_ids = set(
            ComprehensionTestAttempt.objects.filter(
                user=user, focus_id__in=comp_focuses
            ).values_list('focus_id', flat=True).distinct()
        )
        if mastered_ids >= set(comp_focuses):
            result['comprehension'] = MASTERED
        elif attempted_ids:
            result['comprehension'] = IN_PROGRESS
        else:
            result['comprehension'] = NOT_STARTED

    # ── Vocabulary ────────────────────────────────────────────
    vocab_count = VocabularyItem.objects.filter(chunk=chunk).count()
    if vocab_count == 0:
        result['vocabulary'] = UNAVAILABLE
    else:
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

    # ── Writing ───────────────────────────────────────────────
    # Writing is unit-level, not chunk-level.
    # We check whether any WritingStageContent exists for this unit
    # and report the student's progress across all stages in the unit.
    from content.models.writing import (
        WritingStageContent,
        WritingStageMastery,
        WritingAttempt,
        WritingAcademicYear,
    )

    unit = chunk.lesson.unit
    year = WritingAcademicYear.get_current()

    writing_contents = WritingStageContent.objects.filter(
        unit=unit, is_complete=True
    )

    if not writing_contents.exists():
        result['writing'] = UNAVAILABLE
    elif not year:
        result['writing'] = NOT_STARTED
    else:
        total    = writing_contents.count()
        mastered = WritingStageMastery.objects.filter(
            user=user,
            content__in=writing_contents,
            academic_year=year,
        ).count()

        if mastered >= total:
            result['writing'] = MASTERED
        elif WritingAttempt.objects.filter(
            user=user,
            content__in=writing_contents,
            academic_year=year,
        ).exists():
            result['writing'] = IN_PROGRESS
        else:
            result['writing'] = NOT_STARTED

    # ── Pronunciation ─────────────────────────────────────────
    result['pronunciation'] = UNAVAILABLE

    return result