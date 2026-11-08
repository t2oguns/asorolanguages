# FSRS review scheduling

`LexemeProgress` stores one Py-FSRS card per `(user_progress, lexeme_sense)`.
Different meanings of the same word are scheduled independently. Recognition and
production currently share that sense's schedule; separate skills can be added
later if the learning design requires them.

The project pins `fsrs==6.3.2`. Scheduling uses the library's default parameters,
learning/relearning steps and maximum interval. The default desired retention is
0.9 and interval fuzzing is enabled. Django settings `FSRS_DESIRED_RETENTION` and
`FSRS_ENABLE_FUZZING` can override retention and fuzzing. All scheduler timestamps
are converted to UTC. Configuration and library version are recorded per review.

Sources: [official Py-FSRS usage](https://github.com/open-spaced-repetition/py-fsrs#usage)
and [the installed release](https://pypi.org/project/fsrs/6.3.2/).

## Card state

The model persists `state`, `step`, `stability`, `difficulty`, `due` and
`last_review`. New cards start in Learning at step 0 with no initialized stability
or difficulty. FSRS initializes these memory parameters on the first review.
`reps` counts recorded FSRS reviews. `lapses` counts Again ratings from the Review
state, rather than every failed attempt during initial learning.

Database constraints enforce one card per learner/sense, valid states, valid
state/step combinations, positive initialized stability, difficulty between 1 and
10, and lapses no greater than reps. The due index is `(user_progress, due)`.

## Submission and rating policy

Next.js receives Exercise data with answers, checks each answer locally, and
calculates the stats it displays. A single final batch is independently graded
by `submit_lesson()` against that lesson's frozen Exercise delivery. No per-answer
progress request is needed. Delivery creates no partial learner progress.
Unsubmitted answers exist only in client memory; leaving or reloading discards
them, and every return starts a fresh attempt. Completed progress is retained.
FSRS and lesson completion commit with all answer records or roll back together. Submission time is the review time.

Only the first assessed occurrence of each sense in a session schedules a review.
Repeated senses and requeued corrections are stored as `ExerciseAttempt` practice
answers without additional scheduling. Failed initial recall followed by a correct
retry schedules Again once. A fresh session may review the sense again; there is
no cross-session cooldown.

Optional `recall_ratings` map sense ID strings to integers 1–4. Defaults are Good
for fully correct recall and Again for failed/partial recall. Learners may choose
Again for a correct guess, or Hard/Good/Easy for successful recall. The backend
silently substitutes Again if the submitted rating claims successful recall but
the server grade is wrong/partial. Malformed ratings, unknown senses and values
outside 1–4 remain validation errors. Per-item scores are averaged per sense for
blanks and matching; a whole-question score is not applied to unrelated senses.

`schedule_answer_reviews()` is internal: its evidence must come from the server
grader. Client-provided due dates and timestamps never drive the scheduler.
Authoritative results are stored privately; API responses acknowledge the save
without replacing the client's visible stats. Requested recall ratings remain available for private audit. Identical retries
do not reschedule; changed submissions after completion are rejected. Session and
learner locks serialize concurrent retries and competing sessions.

## Review history

`LexemeReviewLog` stores the attempt, rating, observed target score, review time,
package and policy versions, scheduler configuration, card state before/after and
the library's native review log. A unique constraint on `(attempt, progress)`
prevents duplicate reviews for the same sense in one attempt. Preserve these logs
for audit, recovery and potential future parameter optimization.

The configuration and native logs can be deserialized with Py-FSRS. When fuzzing
is enabled, rerunning the same review may choose a different randomized due time;
the stored `card_after` records the due time actually assigned.

## Fetching reviews

```python
from apps.progress.scheduling import due_lexeme_progress

cards = due_lexeme_progress(user=user, language_id=language.pk, limit=50)
for card in cards:
    sense = card.lexeme_sense
    # Choose a published exercise targeting this sense.
```

The helper returns due cards ordered by due time and ID, restricted to the
requesting learner and optionally a language. It caps requests at 200 cards and
preloads senses and lexemes. New senses get cards when first reviewed; this queue
does not itself select unseen lesson material or choose an exercise.

## Development migrations

The FSRS models are created directly by the progress migration after the existing
UserProgress/UserLessonProgress migrations. This project uses disposable development
data for the redesign, so no legacy counter conversion or old-model mapping is
needed. New cards receive memory parameters only from actual FSRS reviews.

Tests create fresh schemas and verify the current scheduler, progress updates and
PostgreSQL submission concurrency. Databases migrated with earlier development
iterations need resetting before applying the new migration set. The configured
application database has not been reset by this cleanup.
