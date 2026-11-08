# Exercise authoring, grading and attempts

An `Exercise` owns its content, learning language, learning targets and grading
policy directly. `LessonExercise` reuses it across lessons with a position in
each lesson. There are no exercise revisions or content groups.

| Model | Relationship and responsibility |
| --- | --- |
| `ExerciseTarget` | An exercise and the particular vocabulary sense it tests. |
| `PromptBlock` | An ordered block owned by one exercise: text, sense, expression or media. |
| `ExerciseOption` | A choice label, optional media and correctness flag. |
| `ExerciseAcceptedAnswer` | An accepted response for translation, correction or word ordering. |
| `ExerciseFillBlankSlot` | A text range in one prompt block and an optional learning target. |
| `BlankAcceptedAnswer` | One valid response for a particular blank. |
| `ExerciseMatchingPair` | Left/right labels and media, optionally attributed to a learning target. |
| `ExerciseAttempt` | One submitted first answer or practice retry with server evidence. |
| `LessonAttempt` | A learner-owned lesson session, snapshots and saved batch result. |
| `progress.LexemeProgress` | FSRS state for a learner and vocabulary sense. |
| `progress.LexemeReviewLog` | Rating, scheduler configuration and before/after state for a review. |

## Authoring and publication

```python
from apps.exercises.models import Exercise, ExerciseTarget, PromptBlock, ExerciseAcceptedAnswer
from apps.exercises.services import publish_exercise, unpublish_exercise

exercise = Exercise.objects.create(
    language=sense.lexeme.language,
    exercise_type=Exercise.Type.TRANSLATION,
    instruction="Translate the greeting into English",
    level=Exercise.Level.A1,
    explanation="This is an informal greeting.",
    # explanation_media=optional_asset,
)
ExerciseTarget.objects.create(exercise=exercise, sense=sense)
PromptBlock.objects.create(
    exercise=exercise, position=0, block_type="text", text="hola",
)
ExerciseAcceptedAnswer.objects.create(exercise=exercise, text="hello", is_primary=True)
publish_exercise(exercise.pk)

exercise = unpublish_exercise(exercise.pk)
exercise.instruction = "Translate this greeting"
exercise.save()
publish_exercise(exercise.pk)
```

At least one prompt block and learning target are required to publish. Choice
questions need both a correct choice and a distractor. Matching needs at least
two distinguishable pairs. Every blank needs at least one accepted answer.
The validator checks bounds, ownership, target language and required answer data.

Published exercises and their targets, prompt blocks and answers reject normal
edits/deletion. Unpublish before editing; publication services own the state
transition. Bulk authoring writes are disabled because they bypass validation.
Unpublishing removes an exercise from delivery in every lesson that uses it.
Republishing exposes the edited content everywhere under the same exercise ID.

Media remains relational: prompt blocks reference media assets; choices have
`media`; pairs have `left_media`/`right_media`; exercises have `explanation_media`.
Choices and pair sides can combine a label with media. Prompt blocks select
exactly one source; use adjacent blocks for text and media together.

Shared dictionary entries, expressions and media remain library resources.
Attempts capture the rendered text and media metadata used at delivery, not a
copy of the media binary. Storage keys should identify stable objects.

## Exercise delivery contract

The delivery serializer starts with `Exercise`, discriminated by `exercise_type`.
It includes `instruction`, `language`, `level`, the three normalization flags,
`explanation`, `explanation_media`, `targets` and the authored child collections:

| Relationship | Delivered fields used for grading or presentation |
| --- | --- |
| `prompt_blocks` | Ordered blocks with resolved `text`, `block_type` and media. |
| `options` | Choice IDs, labels/media and `is_correct`. |
| `accepted_answers` | Text alternatives and `is_primary` for translation, correction and word ordering. |
| `fill_blank_slots` | Source block, Unicode code-point offsets, optional target, explanation and accepted answers. |
| `matching_pairs` | Pair ID, left/right labels and media, optional target. |
| `targets` | Exercise target ID, vocabulary sense ID, lexeme ID and readable labels. |

The client receives all answer data intentionally. It renders and grades this
Exercise-shaped data directly. There are no separate question/grading-key DTOs,
opaque matching IDs or pre-created exercise-attempt IDs. Next.js imports the Exercise contract from the generated OpenAPI schema,
including its model type values. Empty collections for other types may be
present in JSON. Media URLs use `CLOUDFRONT_DOMAIN`; transcripts are not needed.

Graders in Python and TypeScript use the same rules: exact multiple-choice sets,
accepted text alternatives, each word tile once, proportional blank/matching
credit, and per-target evidence. Unicode uses NFC and collapsed whitespace.
Defaults ignore case and preserve punctuation/diacritics. Shared fixtures under
`shared/` check all six types and normalization behavior in both runtimes.
Blank offsets count Unicode code points; the client uses `Array.from(text)`.

## Attempt models and service boundary

`LessonAttempt` holds one learner-owned, frozen lesson/exercise delivery. It also
stores the original submission, submission timestamp and private `server_result`.
A fetch creates this one internal delivery record, without creating answer rows
or partial learner progress. Every fetch starts fresh; delivery records cannot
be retrieved through a resume endpoint. Frozen data lets
an in-progress learner finish against exactly what was delivered, even if an
editor subsequently unpublishes, edits or republishes an exercise. This is a
record of delivery, not authored exercise versioning. Delivery detects publication
changes while constructing its snapshot and asks the caller to retry.

`ExerciseAttempt` is now a submitted answer: its parent lesson attempt, exercise,
sequence, first-answer flag, raw response, optional recall ratings, optional client
score, authoritative score and target evidence. Practice retries are rows of the
same model. Learner and lesson are obtained through the parent. `LessonResponse`
and the old per-question question/key/target snapshots have been removed.
`LexemeReviewLog.attempt` points to the first submitted answer that scheduled it.

The service boundary is deliberately small:

- `services.py`: authoring validation, publish and unpublish.
- `serializers.py`: Exercise-shaped delivery and request/receipt validation.
- `grading.py`: pure authoritative Exercise grader.
- `lessons.py`: `deliver_lesson`, `lesson_payload`, `submit_lesson`, `submission_receipt`.
- `progress/scheduling.py`: FSRS from server-produced answer evidence.

The former standalone start/submit/result services have been removed. A lesson
containing one exercise uses the same flow as a longer lesson.

## API and client flow

All endpoints require authentication. Paths are relative to `/api/v1/courses/`.

| Method and path | Purpose |
| --- | --- |
| `POST lesson/{code}/sessions/` | Fetch the lesson and exercises with answers. Every call creates a fresh attempt; no client session ID is accepted for recovery. |
| `POST lesson/{code}/sessions/{id}/submit/` | Submit all raw answers once at the end; returns a save acknowledgement. |

```json
{
  "responses": [
    {
      "exercise_id": "delivered-exercise-uuid",
      "response": "hello",
      "recall_ratings": {"123": 2}
    }
  ]
}
```

`recall_ratings` is optional, keyed by sense ID strings, with integer values:
Again=1, Hard=2, Good=3, Easy=4. The client can collect it after local feedback.
The save acknowledgement contains only `lesson_attempt_id` and `submitted: true`.
It does not expose authoritative grades or corrections to reconcile in the UI.

| Exercise type | Raw response |
| --- | --- |
| Translation / correction | A string. |
| Word ordering | A list of supplied word strings, preserving duplicate counts. |
| Multiple choice | A list of option ID strings. |
| Fill blanks | A dictionary from blank ID strings to answer strings. |
| Matching | A dictionary from left pair ID strings to right pair ID strings. |

The first N responses cover the N delivered exercises once, in delivery order.
Each exercise may then appear once more as practice. The client queues locally
missed answers; the server also accepts these retries when it considers the first
answer correct. This prevents a grading disagreement from blocking submission.

The Next.js route uses the existing `LessonPlayer`, `useLesson`, exercise views,
`LessonFooter` and `LessonComplete`. There is no separate session-player folder.
`types.ts` aliases API types from the generated OpenAPI schema; only UI state,
computed evidence/results and optional presentation-only intro cards have local
types. Run `npm run api:types` in `apps/web` (with the backend schema endpoint
available) to refresh the contract through the existing Django/OpenAPI script.

The flow stays Check → feedback → Continue, with missed exercises requeued once.
The original completion screen displays the locally calculated first-try score
and accuracy. Its Finish button submits the single answer batch and navigates
away after success. A save failure offers Retry saving on that same screen.
No additional save/confirmation screen is introduced.

The client checks answers and calculates lesson stats without per-exercise API
calls. Only raw answers and optional recall ratings are submitted. Completion
stats are calculated locally from first responses; corrections are counted separately. Saving
changes only the save state. Authoritative grades never replace these visible
stats or produce a disagreement message. There is no resume payload or saved
answer retrieval endpoint. Operational failures and malformed submissions
still show a retry message; they are not disguised as successful saves.

Session IDs, answer buffers, ratings and practice queues exist only in memory.
Leaving or reloading discards them. Returning, including browser back/forward
navigation, fetches a fresh lesson and starts at the first exercise. Next.js
Activity teardown and browser page transitions clear memory as well. No answer
buffer is written to localStorage, sessionStorage or another persistent store.

A save failure retains answers only while the lesson remains open, allowing an
identical final-batch retry. Leaving that screen loses unsaved answers. Explicit
exit warns about this loss. There is no background submission on unload. An
already successful submission retains its completed progress and FSRS reviews;
a submission already sent to the server may finish even if the learner leaves.
Media downloads separately.

## Authoritative progress and FSRS

The backend independently grades each response against the frozen Exercise data.
It atomically saves answers, lesson completion/best score, FSRS cards and review
logs. Identical batch retries return the existing acknowledgement; changed answers
or ratings are rejected. Session and learner locks serialize competing submissions.
Delivery and submission are learner-scoped; delivery uses `private, no-store`
caching. `lesson/{code}/sessions/{id}/submit/` is the only completion endpoint.
The older `lesson/{code}/submit/` route has been removed.

Only the first assessed occurrence of a vocabulary sense per lesson session
schedules a review. Other original exercises for that sense and practice retries
are recorded without another FSRS update. A failed first recall followed by a
successful correction schedules Again once. Each sense has an independent card.
Successful recall defaults to Good; incorrect or partial recall defaults to Again.
If a client supplies Hard/Good/Easy but authoritative recall failed, the backend
silently uses Again. Valid ratings are still stored as originally submitted for
audit. Invalid rating shapes, unknown senses and values outside 1–4 are rejected.

See [FSRS scheduling](../progress/README.md) for card state and review history.

## Development migrations and verification

This redesign uses fresh development data. Exercises, vocabulary and media each
have an initial migration for their current models. Progress retains its existing
UserProgress/UserLessonProgress migrations and adds the current FSRS models in
one migration. There are no converters for discarded intermediate schemas, no
legacy practice counters and no legacy delivery-format branch.

The migrations target a fresh database. A development database that used earlier
iterations needs resetting before these migrations are applied. This cleanup does
not itself delete or reset the configured application database.

Backend tests use pytest and create fresh test schemas from these migrations.
They cover final-model constraints, grading, lesson completion, FSRS and concurrent
submission on PostgreSQL. The Next.js player uses the existing Vitest setup.
