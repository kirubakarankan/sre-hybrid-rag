# How this project works, in plain words

## The story

Imagine a new on-call SRE. It is 3 a.m. The pager says a pod is in trouble. On the shelf is a binder with 108 runbooks. The engineer does not know which page to open, so they ask:

> "pod keeps restarting, what do I check?"

This project is a small team of helpers that finds the right page and reads it out.

### 1. The cutter (`ingest.py`)

The binder is too thick to hand over whole. The cutter snips every runbook into small cards, one per section, and writes the alert name on top of each card, for example "KubePodCrashLooping, Diagnosis".

Result: 415 cards. Cards that only said "TODO" are thrown away.

### 2. The word-matcher (BM25, in `search.py`)

This helper cannot read. It only spots matching words.

The engineer said "restarting", and the right card says "CrashLoop". There is no shared word, so this helper missed it. But when the engineer types the exact alert name, this helper is perfect.

### 3. The meaning-matcher (vector search, in `search.py`)

This helper understands that "keeps restarting" and "crash loop" mean the same thing, so it found the card.

It is a bit vague, though: ask for an exact alert name and it also brings back look-alikes.

### 4. The combiner (rank fusion, in `search.py`)

Each helper hands over a list. The combiner says: any card that both of you picked goes to the top.

Now neither helper's blind spot loses the card. The right card was in the pile, though only in 4th place.

### 5. The careful reader (reranker, in `rerank.py`)

This helper is slow but smart. It takes the top 20 cards and reads each one next to the engineer's question.

It moved the right card from 4th place to 1st.

### 6. The writer (the local LLM, in `answer.py`)

The writer gets the 5 best cards and writes a short answer, noting which card each part came from, like `[1]`.

If the cards do not hold the answer, it must say "Not in the docs." Asked about AWS access keys, it did exactly that.

### 7. The report card (evaluation, in `evals/`)

There are 30 quiz questions where the right runbook is already known. Each helper is scored on how often it finds that runbook in its top 5:

| Helper | Right page found |
|---|---|
| Word-matcher alone | 15 out of 30 |
| Meaning-matcher alone | 19 out of 30 |
| Both combined | 22 out of 30 |
| Both combined, then the careful reader | 23 out of 30 |

That gap, 15 against 23, is the whole point of the project.

## The other things

- **Tests:** small checks that shout if a helper stops working.
- **CI:** GitHub runs those checks on every push.
- **Hardening:** the exact binder and the exact helpers are frozen, so the score stays the same next month.

## What is not perfect

The writer sometimes copies a line from the wrong card and still points at a right one. A citation shows where the writer looked, not that the answer is correct.

## The same story as commands

| Helper | Command |
|---|---|
| Cutter | `make ingest` |
| Word-matcher, meaning-matcher, combiner, careful reader | `.venv/bin/python search.py "pod keeps restarting"` |
| Writer | `.venv/bin/python answer.py "pod keeps restarting, what do I check?"` |
| Report card | `make eval` |
