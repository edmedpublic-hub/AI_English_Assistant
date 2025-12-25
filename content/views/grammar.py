# ============================================================
# Grammar Utilities
# ============================================================

import spacy
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response

from ..models import GrammarPoint, Lesson
from ..serializers import GrammarPointSerializer


# Load spaCy model once (fast)
try:
    nlp = spacy.load("en_core_web_sm")
    SPACY_READY = True
except Exception as e:
    print("❌ spaCy failed to load:", e)
    SPACY_READY = False


def extract_advanced_grammar(text):
    """
    Analyze text and extract grammar points using spaCy.
    Returns a list of dictionaries with title, explanation, and example.
    """
    if not SPACY_READY:
        return []

    doc = nlp(text)
    grammar_points = []

    # 1. Tense Detection
    for token in doc:
        if token.tag_ in ["VBD", "VBN"]:
            grammar_points.append({
                "title": "Past Tense",
                "explanation": "Verb forms showing past actions (VBD/VBN).",
                "example": token.sent.text.strip(),
            })
            break

        if token.tag_ in ["VBP", "VBZ"]:
            grammar_points.append({
                "title": "Present Simple",
                "explanation": "Verb forms showing present habitual actions.",
                "example": token.sent.text.strip(),
            })
            break

        if token.tag_ == "VBG":
            grammar_points.append({
                "title": "Present Continuous",
                "explanation": "Uses -ing verb forms to show ongoing actions.",
                "example": token.sent.text.strip(),
            })
            break

    # 2. Modal Verbs
    modals = {"can", "could", "will", "would", "shall", "should", "may", "might", "must"}
    for token in doc:
        if token.text.lower() in modals:
            grammar_points.append({
                "title": "Modal Verb",
                "explanation": f"‘{token.text}’ is a modal verb expressing ability, permission, or probability.",
                "example": token.sent.text.strip(),
            })

    # 3. Passive Voice
    for token in doc:
        if token.dep_ == "auxpass":
            grammar_points.append({
                "title": "Passive Voice",
                "explanation": "Be + past participle structure focusing on the action, not the doer.",
                "example": token.sent.text.strip(),
            })
            break

    # 4. Conditional Sentences
    for sent in doc.sents:
        if "if" in sent.text.lower():
            grammar_points.append({
                "title": "Conditional Sentence",
                "explanation": "A sentence showing a condition and result.",
                "example": sent.text.strip(),
            })

    # 5. Gerunds / Infinitives
    for token in doc:
        if token.tag_ == "VBG" and token.dep_ == "xcomp":
            grammar_points.append({
                "title": "Gerund",
                "explanation": "Verb ending in -ing used as a noun or complement.",
                "example": token.sent.text.strip(),
            })

        if token.tag_ == "VB" and token.dep_ == "xcomp":
            grammar_points.append({
                "title": "Infinitive",
                "explanation": "Base form of verb used after certain verbs.",
                "example": token.sent.text.strip(),
            })

    # 6. Direct Speech
    for sent in doc.sents:
        if "\"" in sent.text or "'" in sent.text:
            grammar_points.append({
                "title": "Direct Speech",
                "explanation": "Sentence contains quoted spoken words.",
                "example": sent.text.strip(),
            })

    # 7. Prepositions
    for token in doc:
        if token.pos_ == "ADP":
            grammar_points.append({
                "title": "Preposition",
                "explanation": f"‘{token.text}’ shows relationship of place, time, or direction.",
                "example": token.sent.text.strip(),
            })
            break

    # 8. Articles
    for token in doc:
        if token.text.lower() in ["a", "an", "the"]:
            grammar_points.append({
                "title": "Article",
                "explanation": f"‘{token.text}’ is an article used before nouns.",
                "example": token.sent.text.strip(),
            })
            break

    return grammar_points


# ============================================================
# Grammar API ViewSets
# ============================================================

class GrammarPointViewSet(viewsets.ModelViewSet):
    """API endpoint for grammar points."""
    queryset = GrammarPoint.objects.all()
    serializer_class = GrammarPointSerializer


class ExtractGrammar(APIView):
    """Analyze lesson text and extract grammar points using spaCy."""
    def post(self, request, lesson_id):
        if not SPACY_READY:
            return Response(
                {"error": "spaCy is not installed correctly."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        lesson = get_object_or_404(Lesson, id=lesson_id)

        if not lesson.english_text:
            return Response(
                {"error": "This lesson has no English text to analyze."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        grammar_points = extract_advanced_grammar(lesson.english_text)

        return Response(
            {
                "lesson_id": lesson_id,
                "grammar_points": grammar_points,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# Grammar Template Views
# ============================================================

def content_grammar_point_detail(request, gp_id):
    """Show details of a grammar point."""
    gp = get_object_or_404(GrammarPoint, id=gp_id)
    return render(request, "content/grammar_point_detail.html", {"gp": gp})