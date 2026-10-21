# vast-10m on a 1.53 M-token Rust repository

We sent the source of [chock](https://github.com/outpostHQ/chock), a Rust CLI, to vast-10m in one
request: 203 of its 204 tracked files, about 1.53 M input tokens. We asked five questions, one
per request. Each question needs facts from many files. This repository holds the corpus
builder, the questions, the request scripts, the answer keys, the scorer and every answer that
the model returned, so that the test can be run again exactly.

By our checks, one of the five answers is right: for q4 the model found no dead code, and neither
does our rustc check. The other four answers are false, a refusal, or not measured:

- q2 (call sites, with a key from rustc): it listed 94 sites. 4 match a key site exactly and 1 is
  within two lines of one. The other 89 are not call sites, and 2 of them are in files that do not
  exist.
- q3: it said that a file was not in the input. The file is in the input.
- q1: its one item is false.
- q5: its two items give byte savings that nothing measured.

## Results

The main run is run 3, on 2026-10-21. It used the Responses API, because only that API reasons.
Each question went in one request. q4 went twice, because the first request failed (see
[Runs](#runs)).

| Question | What a correct answer needs | Answer | Score |
|---|---|---|---|
| [q1-docs](questions/q1-docs.md) | compare README, docs and help text with the code | 1 item | the item is false (see below) |
| [q2-callers](questions/q2-callers.md) | resolve six functions across 203 files | 94 sites | of 100: 4 exact, 1 within 2 lines; 89 invented |
| [q3-keys](questions/q3-keys.md) | list the keys of the serde config structs | no list | refused: "`src/project/config.rs` ... not included" |
| [q4-dead](questions/q4-dead.md) | find code that nothing uses | `NONE` | agrees with our rustc check |
| [q5-bloat](questions/q5-bloat.md) | find code that makes the binary larger | 2 items | not measured; one cites the wrong lines |

**q1.** The one item says that `--skip` must be written `--skip=GATE,...`. This is false.
docs/guide.md:302 documents `chock run --skip GATE`, and src/cli.rs:64 passes every argument
through `args::joined`, which joins `--skip miri` into `--skip=miri`. The test at
src/cli/args.rs:582 checks exactly this. The item cites docs/guide.md:303, which is the row below
the `--skip GATE` row.

**q2.** The key has 100 sites. An invented site is not in the key and is not within two lines of
a key site in the same file. Per function:

| Function | Key | Listed | Exact | Within 2 lines | Invented |
|---|---|---|---|---|---|
| 1 `normalized` | 9 | 2 | 2 | 0 | 0 |
| 2 `copied` (patch.rs) | 4 | 1 | 0 | 0 | 1 |
| 3 `copied` (oracle.rs) | 5 | 2 | 1 | 0 | 1 |
| 4 `run_paced` | 6 | 2 | 1 | 0 | 1 |
| 5 `Finding::sort_by_place` | 6 | 10 | 0 | 0 | 10 |
| 6 `relative` | 70 | 77 | 0 | 1 | 76 |
| all | 100 | 94 | 4 | 1 | 89 |

Of the 77 sites listed for `relative`, 2 are in files that do not exist
(src/gates/cargo/config.rs and src/gates/tools/typos.rs). None of the other 75 is on a line that
contains `relative`, and 42 of them are in files that do not contain the word at all. None of the
10 sites listed for `sort_by_place` is on a line that contains the name, and 9 are in files that
do not contain it. The reasoning text shows that the model knew that a complete list was asked
for, and gave a partial one: "it seems the entire repository might not be included", "I'll list
a representative set, but the question expects all", "I'll assume the answer expects all call
sites".

**q3.** The answer is one sentence: "I cannot answer reliably: `src/project/config.rs` (and
`schema/config-v1.json`) are not included in the provided repository text". Both files are in the
input: their headers are at lines 67,049 and 10,647 of corpus/repo.txt. The answer key has 57
object keys and 29 fields of list items (see [Answer keys](#answer-keys)).

**q4.** `NONE` agrees with [key/check_q4_dead.py](key/check_q4_dead.py), within the limits of that
check (see [Answer keys](#answer-keys)).

**q5.** Both items propose that a generic function return `Box<dyn Any>` in place of its type
parameter; the first also offers a common result type for all callers. They give "2000" and
"5000" bytes saved, with no measurement behind either number. The second item cites
src/gates/metrics/prodlines.rs:250-260 for `for_each_source`, which is defined at line 293. We did
not build either change, so the q5 answer has no score.

### Requests of run 3

| Question | Seconds | First output (s) | Input tokens | Cached | Output tokens | Reasoning tokens |
|---|---|---|---|---|---|---|
| q1-docs | 560 | 273 | 1,532,516 | 0 | 22,718 | 22,678 |
| q2-callers | 254 | 23 | 1,532,604 | 1,532,032 | 18,160 | 16,669 |
| q3-keys | 162 | 35 | 1,532,492 | 1,531,904 | 9,943 | 9,897 |
| q4-dead | 544 | 360 | 1,532,476 | 1,531,904 | 14,585 | 14,581 |
| q5-bloat | 419 | 258 | 1,532,593 | 1,532,032 | 12,714 | 12,496 |

First output is the time to the first streamed text, reasoning or answer. The five requests in
this table ended with status `completed`, far below the 131,072-token output limit. Almost all of
the output tokens are reasoning: the answers themselves are 4 to 4,380 characters.

## Faults and requests

Faults of the model, with the evidence in [Results](#results) and [Runs](#runs):

1. It invents sites: 89 of the 94 q2 sites are not call sites, and 2 of them are in files that do
   not exist.
2. It says that input is missing when it is there (q3), or that it might be (the q2 reasoning).
3. It writes the END marker after a list that its own reasoning calls partial (q2).
4. It makes false statements about the code (q1 in run 2 and in run 3).
5. It gives byte savings without a measurement (q5).
6. Through the chat completions API, which does not reason, it can loop until the token limit.
   This happened in two of the four long chat requests that finished: the run 1 probe repeats
   one item 501 times, and run 2 q2 lists 3,880 sites for one function.

Faults of the API:

1. The chat completions API does not reason, even with `reasoning_effort: high`; only the
   Responses API reasons. The demo app shows a Chat Completions example first, then a Responses
   example, and does not say which one reasons.
2. A long request got HTTP 408 while another long request ran (run 3 q4). The console line is in
   [results/console.txt](results/console.txt).

What works: the API accepted 1.53 M input tokens in one request. Of the nine requests that sent
the full corpus (runs 2 and 3), six completed, one stopped at the output limit (run 2 q2), we
stopped one (run 2 q3), and one got the HTTP 408. In run 3, the cache served 1,531,904 to
1,532,032 of the input tokens of each of q2 to q5. The streamed events were easy to parse.

Requests:

1. Make the chat completions API reason, or document that only the Responses API reasons.
2. Cite only files and lines that exist in the input; a quote of the cited line would let a user
   check each item.
3. Let the model say that a list is partial, instead of writing the requested END marker.
4. Document how many long requests may run at the same time, and return 429 with a retry time
   instead of 408.
5. Let a demo key read the API docs (/docs, /openapi.json, /llms.txt on demo.voltropy.com); they
   return 401 now, with the key and without it ([results/console.txt](results/console.txt)).

## Method

**Corpus.** [corpus/build.py](corpus/build.py) writes the 203 files of
[corpus/files.txt](corpus/files.txt) at chock commit
[e18fff5](https://github.com/outpostHQ/chock/commit/e18fff5a34bbe2d2e1f40bd21d20f89133ff643c)
after a short introduction. e18fff5 is the parent of the v0.13.0 release commit, and its
Cargo.toml already says 0.13.0. Each file starts with `=== FILE: <path> ===`, and each line
starts with its number and `| `. The text is 4,874,834 characters, and build.py checks its sha256
(`3098139443c7e8ca64b74b070a0e2ba3d9e6283a1421122a6451aadc87657ff6`) against the text that we sent.
The commit has 204 tracked files; we left out CLAUDE.md, 15 lines of instructions for a coding
agent. No question depends on it, but the introduction says "Every tracked file is here".

**Requests.** [ask.py](ask.py) sends one request per question to `POST /v1/responses`, with
`model: vast-10m`, `input` = corpus + `"\n\n# THE QUESTION\n\n"` + question,
`max_output_tokens: 131072`, `temperature: 1.0`, `top_p: 1.0` and `stream: true`. There is no
system prompt, no tool and no retrieval. The API fixes the reasoning effort: a request with
`reasoning.effort` returns HTTP 400 "Reasoning is required at the fixed native setting". The
reasoning text arrives as `response.reasoning_summary_text.delta` events, about one per reasoning
token (16,667 events for 16,669 tokens in q2). So we take it as the full reasoning text, but the
API does not say whether it is complete.

**Questions.** Each question names its sources, gives rules for what counts, and fixes the
answer format so that a script can score it. q1, q4 and q5 also ask the model to leave an item
out when it is not sure. q5 gives the release binary size of 0.13.0, 4,323,632 bytes, as
CHANGELOG.md states it at e18fff5.

## Answer keys

| Question | Key | How we made it |
|---|---|---|
| q1 | [key/q1-reviewed.tsv](key/q1-reviewed.tsv) | by hand, only for the items that the model returned; not a complete key |
| q2 | [key/q2-callers.tsv](key/q2-callers.tsv) | rustc: 97 sites, plus 3 by hand |
| q3 | [key/q3-keys.tsv](key/q3-keys.tsv) | parsed from the serde structs |
| q4 | [key/check_q4_dead.py](key/check_q4_dead.py) | rustc's dead_code lint, with the public API judged too |
| q5 | none | the bytes need a build of each change |

**q2.** [key/make_q2_key.py](key/make_q2_key.py) puts `#[deprecated]` in front of the `fn` of each
of the six functions, on the same line, so no line moves. Then it runs `cargo check --all-targets
--all-features`. Each "use of deprecated" warning is one site. rustc cannot report three sites,
which we added by hand and marked in the `how` column: the lint is silent inside the deprecated
function itself, which hides the recursive calls of the two `copied` functions, and one call of
`run_paced` is under `#[cfg(not(target_os = "linux"))]`. The two `use` lines that import a
function are left out.

**q3.** [key/make_q3_key.py](key/make_q3_key.py) reads the `pub struct` blocks of
src/project/config.rs and applies serde renames. It refuses to run if `flatten` or `alias`
appears. The key has 57 object keys and 29 fields of list items, such as `commands[].name`. The
question asks for every key, but its examples name only object keys, so the scorer counts a
list-item field as neither right nor wrong. schema/config-v1.json defines all 86.

**q4.** rustc does not judge a `pub` item of a library, because a user of the crate could call it.
q4 counts such an item as used only if the repository uses it. So
[key/check_q4_dead.py](key/check_q4_dead.py) changes each `pub` in the library to `pub(crate)`
(1,438 text matches; some are inside test strings, where the change does no harm). It adds
src/main.rs and the two files in tests/ to the library as modules, so that their uses still
count, and checks the library with its unit tests. A planted unused function and struct prove
that the lint is on. The check reports the two planted items and one unused re-export,
`render_decisions` in `pub use` at src/setup/init.rs:17. A `use` is not one of the kinds of dead
code that q4 asks for. Limits: rustc does not report an unused trait implementation, and it does
not compile code for another OS.

## Reproduce

Needs Python 3 (standard library only) and git. The q2 and q4 key scripts also need tar, network
access for cargo to download the crates, and the Rust toolchain that chock pins at that commit
(1.99.0; rustup installs it from rust-toolchain.toml). Every script reads commit e18fff5 itself,
so the branch of the chock checkout does not matter.

```sh
git clone https://github.com/outpostHQ/chock
git clone https://github.com/outpostHQ/vast-10m-eval
cd vast-10m-eval
python3 -I corpus/build.py ../chock corpus/repo.txt   # prints the sha256 above, or stops

export VAST_API_KEY=...                  # VAST_BASE_URL changes the endpoint
./run.sh ../chock                        # all five questions, one at a time
python3 -I score.py runs/<UTC time>      # run.sh prints this folder; results/run3 holds ours

mkdir -p runs                            # make the keys again, and compare them with ours
python3 -I key/make_q2_key.py ../chock > runs/q2-callers.tsv
diff runs/q2-callers.tsv key/q2-callers.tsv
python3 -I key/make_q3_key.py ../chock > runs/q3-keys.tsv
diff runs/q3-keys.tsv key/q3-keys.tsv
python3 -I key/check_q4_dead.py ../chock
```

## Runs

We ran three series on 2026-10-21. Times are UTC.

```
15:21     smoke test            chat completions API, "Reply with the single word: ready"
15:22     run 1 bloat           chat completions API, own prompt, 147 files
15:26     run 1 probe           chat completions API, own prompt, 154 files
15:58     smoke test            chat completions API, a one-line corpus and question
15:58     run 2 q1, q2, q3      chat completions API, this corpus and these questions; we stopped q3
16:16     reasoning check       chat completions API vs Responses API, a one-line question
16:16     smoke test            Responses API, a one-line corpus and question
16:16     run 3 q2, q1, q3      Responses API, sequence A
16:16     run 3 q5, q4          Responses API, sequence B, at the same time as A
16:33     run 3 q4 again        alone, after HTTP 408 on the first try
```

**Run 1** (exploratory, [exploratory/ask_chat_1.py](exploratory/ask_chat_1.py), chat completions
API, `temperature: 0.2`). Two prompts of our own:
[probe](exploratory/run1-probe.question.md) asked three questions with a JSON answer, and
[bloat](exploratory/run1-bloat.question.md) asked for binary and source bloat with our measured
numbers. We built them from the working tree some minutes before commit e18fff5, so they cannot be
rebuilt from a commit; the full prompts are in exploratory/ as sent, gzipped. They differ from
e18fff5 in two files:

- tests/cli.rs: neither prompt has the test helper `fake_kani` yet, and the bloat prompt also
  lacks the test `proof_runs_each_mutant_once_every_harness_verifies_and_trips_on_one_that_verifies`.
- docs/configuration.md:45, in the probe prompt only: an older text of the `miri` row.

The probe answer (`max_tokens: 16384`, 454 s, 53,214 characters) repeats one list item 501 times
in a row and ends inside a JSON string, so it most likely stopped at the token limit. The bloat
answer (`max_tokens: 32768`, 132 s, 24,700 characters) is not scored. ask_chat_1.py did not ask
for usage, so run 1 has no token counts. The times and limits of run 1 are in
[results/console.txt](results/console.txt).

**Run 2** ([exploratory/ask_chat_2.py](exploratory/ask_chat_2.py), chat completions API, this
corpus and these questions, `temperature: 1.0`, penalties at their neutral values, `seed: 7`,
`max_tokens: 65536`). The smoke test, q1 and q2 each used 0 reasoning tokens. q1 returned one
item, which says that the registry has 90 gates; it has 68, as README.md:9 says. q2 ran 850 s and
stopped at the 65,536-token limit after 3,880 sites, all for function 1; 3,869 of them cite
src/gates/proofs/patch.rs, and 3,806 of those cite a line past its end (it has 279 lines). We
stopped run 2 during q3, when the reasoning check showed that only the Responses API reasons.

**Run 3** is the main run. Two sequences ran at the same time: sequence A sent q2, q1 and q3, and
sequence B sent q5 and q4. The first try of q4 returned HTTP 408 while q1 of sequence A ran. We
sent q4 again after sequence A ended. q2 and q5, which also ran at the same time as another
request, completed. [run.sh](run.sh) runs the questions one at a time.

**Reasoning check** ([check_reasoning.py](check_reasoning.py),
[results/reasoning-check.txt](results/reasoning-check.txt)). The question: a train leaves at 9:40
and the trip takes 2 h 35 min. The chat completions API with `reasoning_effort: high` used 0
reasoning tokens and answered "10:15", which is wrong. The Responses API used 78 reasoning tokens
and answered "12:15". The Responses API with `reasoning.effort` returned HTTP 400.

**Smoke tests.** Each smoke test returned the one word that it asked for
(results/run1/ping.answer.txt, results/run2/smoke.*, results/run3/smoke.*; inputs in
exploratory/).

## Limits

- Each question has one answer in the main run, at temperature 1.0, so this test gives no
  estimate of the variance. The failures are large, but another run can give another answer.
- Run 3 sent two requests at the same time; one of them failed with HTTP 408 and ran again.
- The cache served 1,531,904 to 1,532,032 input tokens of q2 to q5 from earlier requests with the
  same corpus. We do not know whether the cache changes the answers.
- We wrote the questions and we maintain chock. The keys for q2, q3 and q4 come from rustc and
  from parsing; the q1 verdicts and three q2 sites come from us.
- The scorer counts a q2 site within two lines of a key site, in the same file, as near, not as
  invented.

## Files

```
corpus/build.py, files.txt     the corpus at e18fff5 and its sha256 check
questions/                     the five questions, as sent
ask.py, run.sh                 the main run: Responses API, one question per request
check_reasoning.py             which API reasons
score.py                       scores a run against key/
key/                           answer keys and the scripts that make them
results/run1, run2, run3       every answer; the usage of runs 2 and 3; the reasoning text of run 3
results/reasoning-check.txt    the output of check_reasoning.py
results/console.txt            console lines that no other file records
exploratory/                   run 1 and run 2 scripts, run 1 prompts, smoke-test inputs
```
