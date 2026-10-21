You read the whole repository of chock, a Rust CLI. After this text come its files: `src/**/*.rs`,
`tests/*.rs`, `docs/*.md`, `README.md`, `schema/config-v1.json` and `Cargo.toml`. Each line has
its line number before `|`. Answer three questions from the files alone. Each answer must be a
fact that you can point to in the files. Do not guess, and do not repeat an item.

# Question 1: callers

For each of these five functions, list every function, method, closure owner or test in the
repository that calls it or names it as a value. Give the file and the name of the enclosing
function, such as `src/a.rs: check`. Count callers in tests too.

- `normalized` in `src/gates/proofs/patch.rs`
- `copied` in `src/gates/proofs/patch.rs`
- `run_paced` in `src/exec/mod.rs` (or wherever it is defined)
- `sort_by_place` on `Finding` in `src/run/report.rs` (or wherever it is defined)
- `relative` in `src/project/mod.rs`

# Question 2: config keys and docs

`src/project/config.rs` defines the keys of `.chock/config.json`. List every key, with its full
path for a nested one, such as `tla.smt_encoding` or `proof.timeout_s`. Use the name as JSON
spells it (after any serde rename). For each key, say whether any file under `docs/` names it,
and whether `schema/config-v1.json` defines it.

# Question 3: dead code

List each function or method outside `#[cfg(test)]` code that nothing in the repository calls,
names as a value, or uses through a trait. For each, give the file, the line, and the reason you
believe nothing uses it. If you find none, give an empty list.

# The answer

Give one JSON object and nothing else:

{"callers": {"normalized": ["src/a.rs: check", ...], "copied": [...], "run_paced": [...],
             "sort_by_place": [...], "relative": [...]},
 "config_keys": [{"key": "tla.smt_encoding", "in_docs": true, "in_schema": true}, ...],
 "dead": [{"file": "src/a.rs", "line": 10, "name": "f", "why": "..."}]}
