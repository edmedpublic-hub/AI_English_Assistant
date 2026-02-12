# Punctuation Module — Architecture & Educational Documentation

## 1. Purpose of This Document

This document explains **how the Punctuation module is designed, why it is structured this way, and how it should guide future LMS modules** such as Grammar, Comprehension, Writing, and Pronunciation.

It serves two roles:

* **Developer reference** → precise architectural contract
* **Educational guide** → explains reasoning behind design decisions

The punctuation module is the **first fully production‑ready vertical slice** of the LMS. Therefore, it becomes the **reference implementation for all future domains**.

---

# 2. Conceptual Overview

## 2.1 Learning Philosophy Implemented in Code

The module follows a strict **Mastery‑Based Learning Model**:

1. **Teach** → student learns rules
2. **Practice** → student receives feedback (no grading persistence)
3. **Test** → graded attempt stored in database
4. **Result** → mastery decision (100% required)
5. **Lock/Unlock** → controls curriculum progression

This mirrors real LMS platforms such as:

* Khan Academy mastery flow
* Duolingo skill completion
* Traditional competency‑based education systems

### Key Principle

> **Practice is formative. Test is summative. Only tests create permanent records.**

---

# 3. Data Architecture

## 3.1 Core Hierarchy (Shared Across LMS)

```
Textbook → Unit → Lesson → Chunk → Domain Module (Punctuation)
```

The punctuation module attaches at the **LessonChunk** level.

---

## 3.2 Punctuation Domain Models (Conceptual)

### Focus

Represents a **single learning target** inside a chunk.

Example:

* Commas in lists
* Full stop usage
* Question marks

Each focus contains:

* mark reference
* ordered learning depth
* rule assignments
* test questions

---

### Rule Mapping

```
Focus → FocusRule → Rule → Examples
```

This enables:

* reusable grammar knowledge
* limited rule exposure per focus (max clarity)
* ordered pedagogy

---

### Questions

Each focus has **assessment questions** used for:

* Practice (stateless)
* Test (graded)

---

### Test Attempt (Critical Model)

Stores:

* student
* focus
* total questions
* correct answers
* percentage score
* mastery flag
* timestamp

### Important Design Decision

> **Every submission creates a NEW attempt row.**

This preserves:

* full learning history
* analytics capability
* auditability
* real LMS behavior

---

# 4. View Architecture

## 4.1 Standard Context Contract

All punctuation views rely on:

```
_chunk_context(chunk, focus=None)
```

This guarantees templates always receive:

* chunk
* lesson
* unit
* textbook
* focus (optional)
* mark (derived automatically)

### Why This Matters

Prevents:

* duplicated navigation logic
* broken breadcrumbs
* inconsistent template variables

---

## 4.2 Hub View — Progress Intelligence

**File:** `punctuation/hub.py`

Responsibilities:

* list focuses in correct pedagogical order
* compute mastery state per focus
* calculate global mastery percentage
* avoid N+1 queries via bulk attempt loading

### Performance Strategy

Single query loads all attempts:

```
values_list("focus_id", "is_mastered")
```

Then Python computes:

* mastered
* in‑progress
* not started

This is **database‑efficient and scalable**.

---

## 4.3 Teach View — Pure Instruction Layer

**File:** `punctuation/teach.py`

Loads only:

* rules explicitly mapped to focus
* ordered rule sequence
* related examples via prefetch

### Pedagogical Intent

> Student sees **only the minimum rules required** for clarity.

---

## 4.4 Practice View — Formative Assessment

**File:** `punctuation/practice.py`

Characteristics:

* login required
* immediate correctness feedback
* **no database writes**
* unlocks test only after perfect attempt

### Educational Meaning

Practice is a **safe learning space**, not grading.

---

## 4.5 Test View — Summative Assessment Engine

**File:** `punctuation/test.py`

Implements real LMS rules:

### Entry Conditions

* user authenticated
* not already mastered
* questions exist

### Submission Behavior

* evaluates answers
* calculates score
* **creates new TestAttempt row**
* checks mastery (100%)
* redirects to result page

### Mastery Rule

```
100% required → permanent mastery
```

No partial passing.

---

## 4.6 Result View — Learning Feedback

Shows:

* score
* mastery status
* retry guidance
* navigation back to curriculum

Acts as **psychological closure** for the learner.

---

# 5. Template System Design

## 5.1 Navigation Consistency

All pages maintain:

* breadcrumb logic
* return paths
* curriculum continuity

This avoids **student disorientation**.

---

## 5.2 Visual Learning Signals

Examples:

* mastery badges
* progress bars
* success/failure colors
* unlock buttons

These are **UX translations of pedagogy**.

---

# 6. Mastery & Locking Strategy

## 6.1 Focus‑Level Mastery

Driven exclusively by:

```
PunctuationTestAttempt.is_mastered
```

---

## 6.2 Chunk‑Level Mastery

Controlled in:

```
chunk_hub view
```

Rules:

* previous chunk must be mastered
* otherwise redirect with warning

This enforces **sequential curriculum progression**.

---

# 7. Query Optimization Principles Used

### Techniques Applied

* `select_related` for hierarchy joins
* `prefetch_related` for examples
* bulk attempt loading
* Python‑side state computation

### Result

> Minimal queries with maximal clarity.

This pattern must be reused in **all future modules**.

---

# 8. Reusability Blueprint for Other Domains

Future modules must replicate:

* Teach → Practice → Test → Result lifecycle
* Stateless practice
* Persistent test attempts
* 100% mastery rule
* Sequential chunk locking
* Standard context helper
* Optimized queries

### Domains That Will Reuse This

* Grammar
* Comprehension
* Writing
* Pronunciation
* Vocabulary testing

The punctuation module is therefore:

> **The architectural template of the LMS.**

---

# 9. Educational Significance

This module transforms the project from:

**“content website” → “true learning system.”**

Because it introduces:

* measurable mastery
* controlled progression
* real assessment persistence
* learner feedback loops

These are the **foundations of serious ed‑tech platforms**.

---

# 10. What Comes Next

With punctuation stabilized and documented, the next logical phase is:

## Comprehension Module

It will reuse:

* mastery lifecycle
* attempt tracking
* context system
* locking logic

But introduce:

* passage‑based learning
* multi‑question grouping
* deeper cognitive assessment

---

# 11. Final Architectural Statement

**Punctuation is the first production‑grade domain.**

All future learning modules must:

* follow its mastery architecture
* reuse its lifecycle design
* maintain its query efficiency
* preserve its pedagogical clarity

Only then will the platform evolve into a **coherent, scalable LMS** rather than a collection of disconnected features.

---

**End of Document**
