from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView
from django.db.models import Count, Q
from django.db.models.functions import TruncDate

from .models import Lesson, Vocabulary

def get_template_names(self):
    return ["vocab_master/lesson_list.html"]

class LessonListView(ListView):
    model = Lesson
    template_name = "vocab_master/lesson_list.html"
    context_object_name = "lessons"

    def get_queryset(self):
        return (
            Lesson.objects
            .annotate(
                word_count=Count('vocabulary', distinct=True),
                reviewed_count=Count(
                    'vocabulary',
                    filter=Q(vocabulary__reviewed=True),
                    distinct=True
                ),
            )
            .select_related('unit', 'unit__textbook')
            .order_by('unit__textbook__title', 'unit__order', 'order', 'title')
        )


def lesson_detail(request, pk):
    """Display all vocabulary items for a given lesson, with prev/next navigation."""
    lesson = get_object_or_404(Lesson, pk=pk)

    vocab_items = (
        Vocabulary.objects.filter(lesson=lesson)
        .select_related("lesson")
        .prefetch_related("synonyms", "antonyms", "examples")
        .annotate(
            syn_count=Count("synonyms", distinct=True),
            ant_count=Count("antonyms", distinct=True),
            ex_count=Count("examples", distinct=True),
        )
        .order_by("word")
    )

    for word in vocab_items:
        word.has_synonyms = word.syn_count > 0
        word.has_antonyms = word.ant_count > 0
        word.has_examples = word.ex_count > 0

    previous_lesson = (
        Lesson.objects.filter(unit=lesson.unit, order__lt=lesson.order)
        .order_by("-order").first()
    )
    next_lesson = (
        Lesson.objects.filter(unit=lesson.unit, order__gt=lesson.order)
        .order_by("order").first()
    )

    context = {
        "lesson": lesson,
        "vocab_items": vocab_items,
        "previous_lesson": previous_lesson,
        "next_lesson": next_lesson,
    }
    return render(request, "vocab_master/lesson_detail.html", context)


def learner_dashboard(request):
    # Summary counts
    total_words = Vocabulary.objects.count()
    reviewed_words = Vocabulary.objects.filter(reviewed=True).count()
    unreviewed_words = total_words - reviewed_words
    total_lessons = Lesson.objects.count()

    # Words per lesson with reviewed counts
    per_lesson_qs = (
        Lesson.objects
        .annotate(
            word_count=Count('vocabulary', distinct=True),
            reviewed_count=Count(
                'vocabulary',
                filter=Q(vocabulary__reviewed=True),
                distinct=True
            ),
        )
        .select_related('unit', 'unit__textbook')
        .order_by('unit__textbook__title', 'unit__order', 'order', 'title')
    )

    lessons_with_nav = []
    for lesson in per_lesson_qs:
        lesson.previous_lesson = (
            Lesson.objects.filter(unit=lesson.unit, order__lt=lesson.order)
            .order_by("-order").first()
        )
        lesson.next_lesson = (
            Lesson.objects.filter(unit=lesson.unit, order__gt=lesson.order)
            .order_by("order").first()
        )
        lesson.has_started = lesson.reviewed_count > 0
        lessons_with_nav.append(lesson)

    # Chart data
    per_lesson_labels = [f"{l.unit.title} / {l.title}" for l in lessons_with_nav]
    per_lesson_values = [l.word_count for l in lessons_with_nav]

    added_by_day = (
        Vocabulary.objects
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(total=Count('id'))
        .order_by('day')
    )
    added_labels = [str(row['day']) for row in added_by_day]
    added_values = [row['total'] for row in added_by_day]

    context = {
        'total_words': total_words,
        'reviewed_words': reviewed_words,
        'unreviewed_words': unreviewed_words,
        'total_lessons': total_lessons,
        'reviewed_chart': [reviewed_words, unreviewed_words],
        'per_lesson_chart': {
            'labels': per_lesson_labels,
            'values': per_lesson_values,
        },
        'added_over_time_chart': {
            'labels': added_labels,
            'values': added_values,
        },
        'lesson_progress': lessons_with_nav,
    }
    return render(request, 'vocab_master/dashboard.html', context)