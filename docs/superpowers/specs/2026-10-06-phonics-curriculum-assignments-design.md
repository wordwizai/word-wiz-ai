# Phonics curriculum and teacher assignments

## Goal

Give Word Wiz AI a real phonics curriculum. The 113 practice-word patterns in
`frontend/src/data/phonicsPatterns.ts` become an ordered scope and sequence of
18 units. Any signed-in child can work through it from the Practice page, and a
teacher can assign single patterns or whole units to a class or a small group,
then see who has mastered each sound.

Today those patterns only power the public SEO pages and the guest `/try` flow,
which saves nothing. Classes exist (create, join by code, per-student stats and
sound insights), but there is no way for a teacher to give a student specific
work, and no signed-in mode that focuses on one sound.

## Decisions

| Question | Decision |
|---|---|
| What "curriculum" means | An ordered sequence of units. Teachers assign from it and can see where each student is. |
| What a session contains | The pattern's word list in short lines, then its decodable sentences. Fixed content, no GPT. |
| Who can be assigned work | The whole class by default, or chosen students. |
| Who can use the sequence | Everyone. It lives on the Practice page, with teacher assignments shown on top. |
| What teachers see | A status and a pattern score per student, with Mastered at 80% or more. |
| Architecture | One `phonics-pattern` activity. The pattern lives on a side table keyed by session. Progress is computed from sessions, never stored on assignments. |

Out of scope for this build are due dates, auto-advancing students through the
sequence, re-reading a line within a session, and a public scope and sequence
page. The last one may deserve to come right after, since it is the clearest
public evidence of the curriculum and a natural SEO page.

## Curriculum data

A new `frontend/src/data/phonicsCurriculum.json` holds the units in order. It
is JSON so the TypeScript frontend can import it and the Python export script
can read it without parsing TypeScript.

```json
{
  "units": [
    {
      "id": "short-a",
      "title": "Short a word families",
      "grade": "Kindergarten",
      "patterns": ["at-family", "an-family", "ap-family", "ad-family", "ag-family", "am-family", "ab-family"]
    }
  ]
}
```

Every pattern in `phonicsPatterns.ts` appears in exactly one unit, and every
slug in the file exists. The export script below refuses to run otherwise,
and a backend test runs it.

The app pages never import this file or `phonicsPatterns.ts`. The patterns
file is over 3,000 lines of teaching text, so the backend serves pattern
names and unit order to the signed-in pages instead.

The draft order follows the usual systematic phonics progression. It is a
first draft for review.

| # | id | Title | Grade | Patterns |
|---|---|---|---|---|
| 1 | short-a | Short a word families | Kindergarten | at an ap ad ag am ab (-family) |
| 2 | short-i | Short i word families | Kindergarten | ig in ip it id |
| 3 | short-o | Short o word families | Kindergarten | op ot og ob ox |
| 4 | short-u | Short u word families | Kindergarten | ug un ut ub um up |
| 5 | short-e | Short e word families | Kindergarten | ed en et eg |
| 6 | digraphs | Digraphs | Kindergarten–Grade 1 | sh ch th wh ph (-digraph), ash unch (-family) |
| 7 | ck-tch | ck and tch | Kindergarten–Grade 1 | ck-digraph, ack eck ick ock uck atch (-family) |
| 8 | double-letters | Double letters | Kindergarten–Grade 1 | ill ell oss uff |
| 9 | s-blends | S-blends | Kindergarten–Grade 1 | st sp sk sm sn sw sc tw (-blend) |
| 10 | l-blends | L-blends | Grade 1 | bl cl fl gl pl sl |
| 11 | r-blends | R-blends | Grade 1 | br cr dr fr gr pr tr |
| 12 | ending-nd-nt-mp | Ending blends -nd, -nt, -mp | Grade 1 | and end ond ent amp imp ump |
| 13 | ending-st-ft-lt | Ending blends -st, -ft, -lt | Grade 1 | ast est ist ust ift oft elt ilt |
| 14 | glued-sounds | Glued sounds ng and nk | Grade 1 | ng-digraph, ang ing ong ank ink unk |
| 15 | silent-e | Silent e | Grade 1 | a-e i-e o-e u-e (-magic-e) |
| 16 | r-controlled | R-controlled vowels | Grade 1–2 | ar or er ir ur (-r-controlled) |
| 17 | long-vowel-teams | Long vowel teams | Grade 1–2 | ai ay ee ea oa oe ie ue ui (-vowel-team) |
| 18 | other-vowel-teams | Other vowel teams | Grade 1–2 | oo ow ou oi oy au aw (-vowel-team) |

The ph digraph sits last in unit 6 even though it is often taught later.
Teachers who want to hold it back can leave it out when assigning the unit.

## Getting the content to the backend

The backend container never sees the frontend source, so
`backend/scripts/export_guest_sentences.py` is renamed to
`export_phonics_data.py` and extended. It reads `phonicsPatterns.ts` and
`phonicsCurriculum.json` and writes one file, `backend/data/phonics_patterns.json`.

```json
{
  "units": [{ "id": "short-a", "title": "Short a word families", "patterns": ["at-family", "..."] }],
  "patterns": {
    "at-family": {
      "display_name": "-at Word Family",
      "unit": "short-a",
      "position": 0,
      "words": ["cat", "hat", "..."],
      "sentences": ["The cat sat on the mat.", "..."],
      "word_line_count": 3,
      "lines": ["cat hat bat mat rat", "sat fat pat vat that", "flat chat brat scat spat", "The cat sat on the mat.", "..."]
    }
  }
}
```

`position` is the pattern's index in the whole sequence, used to sort.
`word_line_count` says how many of the `lines` come from the word list, so
the scorer knows which lines are word lines.
`guest_sentences.json` is deleted and `routers/guest.py` reads its allowed
sentences from the new file. The existing `--check` mode and the test in
`tests/test_guest_router.py` that runs it move over unchanged in purpose, so a
stale file still fails the backend tests.

A small loader, `core/phonics_data.py`, reads the file once and exposes
`get_pattern(slug)`, `all_patterns()` and `units()`.

### Reading lines

The export script builds `lines` from the word list and the sentences. The
words are dealt into the fewest lines of at most five words, as evenly as
possible (14 words become 5, 5 and 4, and 11 become 4, 4 and 3). The sample
sentences follow, one per line. The -at family comes out at three word lines
and four sentences, so seven readings. Most patterns land between five and ten
readings, about two to four minutes.

## The pattern session

### Storage

A new table, `pattern_sessions`, sits beside `sessions`.

| Column | Type | Notes |
|---|---|---|
| session_id | int, PK, FK sessions.id, cascade delete | one row per pattern session |
| pattern_slug | string(64), indexed | |
| words_correct | int, nullable | set when the session finishes |
| words_total | int, nullable | set when the session finishes |
| completed_at | datetime, nullable | set when the session finishes |

`Session` gets a one-to-one `pattern` relationship. Using a new table instead
of new columns on `sessions` matters for deploys. `main.py` runs
`Base.metadata.create_all` at startup, which creates missing tables but never
adds columns. New columns on `sessions` would break every session query on
prod if the Alembic step were forgotten, while a new table is created on
startup either way.

All pattern sessions belong to a single activity row with
`activity_type="phonics-pattern"`, created on first use by a get-or-create in
`core/phonics_data.py` or the router. `GET /activities` leaves it out, so it
never appears in Today's picks or the Practice page activity lists.
`POST /session/` refuses that activity, so a pattern session can't exist
without a pattern.

### Starting

`POST /phonics/sessions` with `{ "pattern_slug": "at-family" }` returns the
child's newest unfinished session for that pattern if there is one, and
otherwise creates a session and its `pattern_sessions` row. An unknown slug
returns 404. The response is the usual `SessionOut`, which gains nullable
`pattern_slug` and `pattern_name` fields, so the Dashboard and practice
screen can show "-at Word Family" without loading the pattern data.

`GET /session/{id}/current-data` learns about pattern sessions. With no
readings yet it returns the first line, and in both states it includes
`line_index` and `line_count`. `BasePractice` reads the first line from there
instead of from the activity settings, which are empty for this activity.

### The mode

`core/modes/phonics_pattern.py` defines `PhonicsPatternPractice(BaseMode)`.
`get_activity_object` in `routers/ai.py` returns it for `phonics-pattern`
sessions, looking the slug up through the session's `pattern` row.

`get_next_sentence` finds the line just read by matching the attempted
sentence against the pattern's lines, ignoring case and spacing. It can't
count readings instead, because the mic stays available after each reading
and a child may read a line again before tapping Next. It returns the
following line, with `line_index` and `line_count`, and makes no GPT call.
On the last line it returns `{"session_complete": true}` instead. If the
sentence matches no line (which shouldn't happen) it falls back to counting
readings.

### Finishing and scoring

When the mode reports the end, the stream handler saves the reading's
feedback entry as usual, then calls `finish_pattern_session(db, session)`.
That function scores the session, fills in the `pattern_sessions` row, sets
`sessions.is_completed = 1`, and the handler sends a new event.

```json
{ "type": "session_complete", "data": { "words_correct": 11, "words_total": 14, "mastered": false } }
```

The score reads each saved reading's `phoneme_analysis.pronunciation_dataframe`
(the `ground_truth_word` and `per` columns). Only the first reading of each
line counts, so reading a line again can't raise or lower the score.

- Rows with no `ground_truth_word` are inserted sounds and are skipped.
- On a word line, every word counts.
- On a sentence line, a word counts only if it is on the pattern's word list,
  compared in lower case with punctuation stripped.
- A word is read right if its `per` is below 0.15, the same cutoff that turns
  the word badge green in `WordBadge.tsx`. A skipped word has `per` 1.0 and
  counts as wrong.
- Mastered means `words_correct / words_total` is 0.8 or more.

If the final line is read twice, `finish_pattern_session` does nothing for a
session that already has `completed_at` and returns the stored result.

### Practice screen

`frontend/src/config/practiceTypes.ts` gets a `phonics-pattern` entry that uses
`BasePractice` with the Next button. For pattern sessions the stage shows
"Line 3 of 7". After the last line the Next arrow still appears, so the child
hears that line's feedback first, and tapping it opens a finish screen ("You
read 11 of 14 words right.", with a stronger message when mastered). The
screen reads its message aloud and has *Practice again*, which starts a fresh
session for the same pattern, and *Back to practice*. The child never sees the
words "Needs practice". A feedback clip that arrives after the child taps Next
is dropped, so it can't play over the next line or the finish screen.

## Assignments

### Tables

`assignments`

| Column | Type | Notes |
|---|---|---|
| id | int, PK | |
| class_id | int, FK classes.id, cascade delete, indexed | |
| pattern_slug | string(64) | |
| whole_class | bool | |
| created_at | datetime | |

Unique on `(class_id, pattern_slug)`. Assigning a pattern that the class
already has merges into the existing row. New students are added to it, and
assigning it to the whole class turns `whole_class` on.

`assignment_students`

| Column | Type | Notes |
|---|---|---|
| id | int, PK | same shape as `class_memberships` |
| assignment_id | int, FK assignments.id, cascade delete | |
| student_id | int, FK users.id, cascade delete | |

Unique on the pair, and only used when `whole_class` is off.

For a whole-class assignment the recipients are the class's members at the
time of reading, so students who join later get it and students who leave
drop out of it. For a chosen-students assignment, only listed students who are
still members count.

Assigning a unit, or several patterns at once, creates or merges one
assignment per pattern.

### Status

`crud/phonics_progress.py` holds one function that every view uses. Given
student ids and pattern slugs, it runs a single query over `sessions` joined
to `pattern_sessions` and returns a status per pair.

| Status | Rule |
|---|---|
| Not started | No session for the pattern |
| In progress | An unfinished session, and no finished one |
| Mastered | The latest finished session scored 80% or more |
| Needs practice | The latest finished session scored under 80% |

Each result also carries `tries` (the number of finished sessions), the latest
`words_correct` and `words_total`, and `last_completed_at`.

Status counts every session the student has done, including ones from before
the assignment and ones started from the Practice page, so practice at home
shows up for the teacher. On the student's own list, Mastered assignments show
as done and Needs practice ones stay open, so the child keeps working on the
sound until they master it. A teacher who sees a child stuck can delete the
assignment.

### Endpoints

Student endpoints live in a new `routers/phonics.py`, mounted at `/phonics`.

| Method and path | Returns |
|---|---|
| `POST /phonics/sessions` | Start or resume a pattern session (above) |
| `GET /phonics/path` | Every unit in order, each pattern's name and the current user's status on it, and `next_slug`, the first pattern that isn't Mastered |
| `GET /phonics/curriculum` | The units in order with pattern names and no status, for the assign dialog |
| `GET /phonics/assignments` | Every assignment the current user has across their classes, with class name, pattern name, unit and status, in curriculum order |

Teacher endpoints live in a new `routers/assignments.py`, mounted under
`/classes`, with the same "only the teacher of this class" checks as
`routers/classes.py`.

| Method and path | Behavior |
|---|---|
| `POST /classes/{id}/assignments` | Body `{ "pattern_slugs": [...], "student_ids": [...] or null }`, where null means the whole class. 400 for unknown slugs (listing them) or for students who aren't members. Returns the class's assignments, the same list as GET. |
| `GET /classes/{id}/assignments` | Each assignment in curriculum order with its recipients' statuses, plus counts per status |
| `DELETE /classes/{id}/assignments/{assignment_id}` | Removes the assignment. Students' sessions and scores are kept. |
| `GET /classes/{id}/phonics-progress` | The units, plus each student's status for every pattern they have touched, for the class grid |
| `GET /classes/{id}/students/{sid}/phonics-path` | The same payload as `GET /phonics/path`, for one student in the class |

The existing student stats and insights in `routers/classes.py` already count
every session, so pattern sessions show up there with no change.

## Screens

### Student

- **Dashboard.** A "From your teacher" section above Today's picks, shown
  only when the student has open assignments. Each card shows the pattern,
  unit, class, a status chip and Start or Continue.
- **Practice page.** The same "From your teacher" section at the top. Below
  it, a Phonics path section with a Continue card for the first pattern in
  the sequence that isn't Mastered, and a link to all 18 units.
- **`/practice/phonics` page.** The units in order, each a card with its
  patterns as chips that show status (a check for Mastered, a "try again"
  arrow for Needs practice, a dot for In progress), with a key above the list
  so the colours never carry meaning alone. Tapping a chip starts or resumes
  that pattern's session. The unit holding the next pattern starts open and
  the rest show a summary such as "3 of 7 done". It sits under `/practice`
  because the build prerenders every public route and the `/practice` family
  is excluded, and it lights up the Practice nav item. That keeps `/phonics`
  free for a public scope and sequence page.
- **Recent list on the Dashboard.** Pattern sessions show the pattern's name
  instead of the activity title, are grouped per pattern instead of per
  activity, and a finished one restarts through `POST /phonics/sessions`.

### Teacher

All of this lives in the existing `ClassDetailView`.

- **Tabs.** Students (today's table), Assignments and Phonics path.
- **Assign practice dialog.** Units listed with pattern checkboxes, where
  ticking a unit ticks all its patterns. Below, Whole class (the default) or
  a list of students to tick. A summary line ("Assign 7 patterns to 22
  students") sits above the Assign button. With no students yet only Whole
  class can be picked, since whole-class work reaches students as they join.
  A pattern the whole class already has stays whole-class when it's assigned
  to chosen students, and the dialog says so. After assigning, the view
  switches to the Assignments tab and a toast confirms it.
- **Assignments tab.** One row per assignment in curriculum order with who
  it is for and a bar of mastered, needs practice, in progress and not
  started, with a key above the list. Expanding
  a row shows each student's status, score and tries, and it has a delete
  action.
- **Phonics path tab.** A grid of students by units. Each cell shows mastered
  patterns out of the unit's total, shaded by that fraction, and scrolls
  sideways on narrow screens.
- **Student detail.** A read-only copy of the child's path, reusing the
  `/practice/phonics` page's unit component.

## Errors and edge cases

- **A pattern removed from the data.** Students no longer see assignments
  for it. Teachers see a "No longer available" row they can delete. A session
  for it sends an error event ("This practice isn't available anymore.")
  instead of crashing.
- **Not the teacher, or not a member.** 403 and 400, matching `classes.py`.
- **Double tap on Start.** Both calls may create a session. The next start
  resumes the newest unfinished one, so nothing breaks.
- **Network errors.** The existing practice error toasts and `PracticeRouter`
  load errors apply unchanged.

## Deploying

The backend ships first, then the frontend. The new frontend calls routes that
404 until the backend is live. The Alembic migration creates the three new
tables, but checks for each one first, because `create_all` at startup may
already have made them and a plain `CREATE TABLE` would then fail.

## Testing

**Backend** (`unittest`, in the style of `tests/test_guest_router.py`, with no
model and an in-memory SQLite database)

- Line building, including the even distribution and short word lists.
- Scoring. Sentence words count only when on the list, case and punctuation
  are ignored, inserted rows are skipped, the 0.15 cutoff, the 80% mark, and
  only the first reading of each line counts.
- The mode returns the right next line and reports the end on the last line.
- Status. All four states, the latest finished session wins, and `tries`.
- Assignments. Non-teacher gets 403, non-member and unknown slug get 400,
  re-assigning merges, whole-class work reaches a student who joins later,
  and a student who leaves loses it.
- `POST /phonics/sessions` resumes an unfinished session.
- `export_phonics_data.py --check` passes on the committed file.

- Every pattern is in exactly one unit, and every unit slug exists (the
  export script's own check), and `next_slug` is the first pattern that
  isn't Mastered.

**Frontend** (`node --test`)

- The pure helpers in `src/lib/phonics.ts`, which pick the finish message,
  order a student's assignments and shade the grid cells.

**End to end** on `backend/dev_server.py` (seeded SQLite, never `main.py`)
with the fake-mic setup. `dev_server.py` seeds a teacher account and a class
with the demo child in it, so no accounts need making by hand. The teacher
assigns unit 1 to the whole class. The child sees the assignment on the
Dashboard, reads through -at and sees the finish card. The teacher then sees
the status on the Assignments tab and the grid. Screenshots of each step.
