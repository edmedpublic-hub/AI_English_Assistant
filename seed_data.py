from vocab_master.models import Textbook, Unit, Lesson, Vocabulary

# Create hierarchy
tb = Textbook.objects.create(title="English - 11", description="Seeded from Unit 1 Lesson 1")
unit = Unit.objects.create(textbook=tb, title="Unit 1", order=1)
lesson = Lesson.objects.create(unit=unit, title="Lesson 1: Early Years of Rasoolullah", order=1)

# Vocabulary entries extracted from passage
words = [
    {"word": "loss", "part_of_speech": "noun", "definition": "The state of losing something", "urdu_meaning": "نقصان", "reviewed": True},
    {"word": "orphan", "part_of_speech": "noun", "definition": "A child whose parents have died", "urdu_meaning": "یتیم", "reviewed": False},
    {"word": "guardian", "part_of_speech": "noun", "definition": "A person who protects or cares for someone", "urdu_meaning": "سرپرست", "reviewed": True},
    {"word": "character", "part_of_speech": "noun", "definition": "The qualities that define a person", "urdu_meaning": "کردار", "reviewed": False},
    {"word": "justice", "part_of_speech": "noun", "definition": "Fair treatment and moral rightness", "urdu_meaning": "انصاف", "reviewed": True},
    {"word": "respect", "part_of_speech": "noun", "definition": "Admiration for someone’s qualities", "urdu_meaning": "عزت", "reviewed": False},
    {"word": "pact", "part_of_speech": "noun", "definition": "A formal agreement", "urdu_meaning": "معاہدہ", "reviewed": True},
    {"word": "alliance", "part_of_speech": "noun", "definition": "A union formed for mutual benefit", "urdu_meaning": "اتحاد", "reviewed": False},
    {"word": "dispute", "part_of_speech": "noun", "definition": "A disagreement or argument", "urdu_meaning": "جھگڑا", "reviewed": True},
    {"word": "conflict", "part_of_speech": "noun", "definition": "A serious disagreement or struggle", "urdu_meaning": "تنازعہ", "reviewed": False},
    {"word": "admiration", "part_of_speech": "noun", "definition": "Respect and warm approval", "urdu_meaning": "تعریف", "reviewed": True},
    {"word": "truthfulness", "part_of_speech": "noun", "definition": "The quality of being honest", "urdu_meaning": "سچائی", "reviewed": False},
    {"word": "humility", "part_of_speech": "noun", "definition": "A modest view of one’s importance", "urdu_meaning": "انکساری", "reviewed": True},
    {"word": "generosity", "part_of_speech": "noun", "definition": "The quality of being kind and giving", "urdu_meaning": "سخاوت", "reviewed": False},
    {"word": "integrity", "part_of_speech": "noun", "definition": "Honesty and strong moral principles", "urdu_meaning": "دیانتداری", "reviewed": True},
    {"word": "gentleness", "part_of_speech": "noun", "definition": "Kindness and softness in behavior", "urdu_meaning": "نرمی", "reviewed": False},
    {"word": "fairness", "part_of_speech": "noun", "definition": "Impartial and just treatment", "urdu_meaning": "انصاف پسندی", "reviewed": True},
    {"word": "profound", "part_of_speech": "adjective", "definition": "Very great or intense", "urdu_meaning": "گہرا", "reviewed": False},
    {"word": "exceptional", "part_of_speech": "adjective", "definition": "Unusually good", "urdu_meaning": "غیر معمولی", "reviewed": True},
    {"word": "steadfast", "part_of_speech": "adjective", "definition": "Firm and unwavering", "urdu_meaning": "ثابت قدم", "reviewed": False},
    {"word": "impartial", "part_of_speech": "adjective", "definition": "Treating all rivals equally", "urdu_meaning": "غیر جانبدار", "reviewed": True},
    {"word": "insightful", "part_of_speech": "adjective", "definition": "Showing deep understanding", "urdu_meaning": "بصیرت والا", "reviewed": False},
]

# Insert into database
for w in words:
    Vocabulary.objects.create(
        lesson=lesson,
        word=w["word"],
        part_of_speech=w["part_of_speech"],
        definition=w["definition"],
        urdu_meaning=w["urdu_meaning"],
        reviewed=w["reviewed"]
    )