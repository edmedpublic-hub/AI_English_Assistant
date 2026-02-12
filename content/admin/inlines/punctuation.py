from django.contrib import admin
from django.core.exceptions import ValidationError
from content.models.punctuation import (
    PunctuationRule,
    PunctuationExample,
    ChunkPunctuationFocusRule,
    PunctuationQuestion,
)

# ============================================================
# RULES under a MARK
# ============================================================

class PunctuationRuleInline(admin.TabularInline):
    model = PunctuationRule
    extra = 1
    fields = ("rule_text",)
    ordering = ("id",)
    show_change_link = True


# ============================================================
# EXAMPLES under a RULE
# ============================================================

class PunctuationExampleInline(admin.TabularInline):
    model = PunctuationExample
    extra = 1
    fields = ("sentence",)
    ordering = ("id",)
    show_change_link = True


# ============================================================
# RULES linked to a CHUNK FOCUS
# ============================================================

class FocusRuleInline(admin.TabularInline):
    """Allows teachers to select which global rules apply to this lesson."""
    model = ChunkPunctuationFocusRule
    extra = 1
    autocomplete_fields = ("rule",)
    ordering = ("order",)


# ============================================================
# QUESTIONS under a CHUNK FOCUS
# ============================================================

class PunctuationQuestionInline(admin.StackedInline):
    """
    Main authoring surface for punctuation questions.
    Enforces pipe-separated options and correct answer matching.
    """
    model = PunctuationQuestion
    extra = 1
    fields = (
        "question_text",
        "question_type",
        "options",
        "correct_answer",
        "explanation",
    )
    ordering = ("id",)
    show_change_link = True

    def clean(self):
        super().clean()
        for form in self.forms:
            # Skip empty forms or forms marked for deletion
            if not hasattr(form, "cleaned_data") or form.cleaned_data.get('DELETE'):
                continue

            q_type = form.cleaned_data.get("question_type")
            options_raw = form.cleaned_data.get("options")
            correct = form.cleaned_data.get("correct_answer")

            if q_type == 'mcq':
                if not options_raw:
                    raise ValidationError(
                        "MCQ questions must include options separated by a pipe '|'."
                    )

                # Use the pipe separator for safety as per our new model standard
                parsed = [o.strip() for o in options_raw.split("|") if o.strip()]

                if len(parsed) < 2:
                    raise ValidationError(
                        "MCQ must contain at least two options (e.g., Option 1 | Option 2)."
                    )

                if correct not in parsed:
                    raise ValidationError(
                        f"Correct answer ('{correct}') must exactly match one of the options: {parsed}"
                    )