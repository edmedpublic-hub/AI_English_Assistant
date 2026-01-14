import random
import re


def build_questions(vocab_items, max_questions=10):
    clean = [v for v in vocab_items if v.word and v.word.strip()]
    pools = []

    def add(q, pool):
        if q.get("question") and q.get("options") and q.get("answer"):
            pool.append(q)

    meaning, synonym, antonym, sentence = [], [], [], []

    for v in clean:
        if v.meaning:
            distractors = [x.meaning for x in clean if x.id != v.id and x.meaning]
            if distractors:
                opts = random.sample(distractors, min(3, len(distractors))) + [v.meaning]
                random.shuffle(opts)
                add({"question": f"What is the meaning of '{v.word}'?", "options": opts, "answer": v.meaning}, meaning)

        if v.synonyms:
            syns = [s.strip() for s in v.synonyms.split(",") if s.strip()]
            if syns:
                correct = syns[0]
                pool = []
                for o in clean:
                    if o.id != v.id and o.synonyms:
                        pool.extend(s.strip() for s in o.synonyms.split(",") if s.strip())
                if len(pool) >= 2:
                    opts = random.sample(pool, min(3, len(pool))) + [correct]
                    random.shuffle(opts)
                    add({"question": f"The most appropriate synonym of '{v.word}' is:", "options": opts, "answer": correct}, synonym)

        if v.antonyms:
            ants = [a.strip() for a in v.antonyms.split(",") if a.strip()]
            if ants:
                correct = ants[0]
                distractors = [x.word for x in clean if x.id != v.id]
                if distractors:
                    opts = random.sample(distractors, min(3, len(distractors))) + [correct]
                    random.shuffle(opts)
                    add({"question": f"The most appropriate antonym of '{v.word}' is:", "options": opts, "answer": correct}, antonym)

        if v.example_sentence:
            sentences = [s.strip() for s in v.example_sentence.split(".") if s.strip()]
            if sentences:
                blank = re.sub(re.escape(v.word), "____", sentences[0], flags=re.IGNORECASE)
                distractors = [x.word for x in clean if x.id != v.id]
                if distractors:
                    opts = random.sample(distractors, min(3, len(distractors))) + [v.word]
                    random.shuffle(opts)
                    add({"question": f"Complete the sentence: {blank}", "options": opts, "answer": v.word}, sentence)

    all_pools = [meaning, synonym, antonym, sentence]
    selected = []

    while len(selected) < max_questions and any(all_pools):
        for pool in all_pools:
            if pool and len(selected) < max_questions:
                selected.append(pool.pop())

    random.shuffle(selected)
    return selected
