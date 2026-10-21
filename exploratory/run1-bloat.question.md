You review the Rust source of chock, a CLI that runs quality gates on Rust projects. The whole
source follows this text: every `src/**/*.rs`, `tests/*.rs` and `Cargo.toml`. Each line has its
line number before `|`.

# The goal

Find bloat in chock, of two kinds, and say exactly how to remove it without a change in behavior.

1. Binary bloat: code that makes the release binary larger than it needs to be.
2. Source bloat: code a reader pays for and the program does not need, such as two helpers that do
   the same thing, a generic function with one caller, a parameter that is always the same, an
   unused branch, a type that only wraps another, or text built twice.

# What we measured on the release binary (opt-level "z", lto, codegen-units 1, strip)

- The binary is 4,323,632 bytes. Unwind tables are about 700 KB.
- serde code is about 205 KB: 26 `Vec<T>` readers cost 72 KB and 148 `Deserialize` impls 74 KB.
  Each new map value type in a config costs about 3.6 KB.
- Stable sort: 38 monomorphized copies of `quicksort` and `drift::sort` cost 117 KB, about 3 KB
  each. Each `sort_by`/`sort_by_key` closure is a new copy.
- A `collect()` into a `BTreeMap` or `BTreeSet` adds its own sort copy for each iterator type. We
  already replaced 9 of them with `extend`, which saved 41 KB. Look for the ones left.
- `drop_glue` is 119 KB over 1,073 types. `fmt` impls are 38 KB over 222 types.
- `chock::cli::dispatch` is 100 KB in one function, `tla::check` 42 KB,
  `setup::init::write_local_with` 38 KB, `setup::doctor::gathered` 25 KB, `cli::run_gates_code`
  23 KB, `links::inspect` 20 KB. syn's visitors (`visit_item`, `visit_expr` and others) appear in
  18 monomorphized copies each, about 170 KB in total.

# Constraints

- Do not change the release profile, the panic strategy or the dependency list. The owner
  decides those.
- Keep every CLI flag, every message, and every JSON output byte for byte.
- Keep the behavior on Linux, macOS and Windows.
- Each suggestion must be a real change you can see in the source shown. Do not guess about code
  you cannot see.

# The answer

Give a JSON array and nothing else. Rank the items by the bytes they save, most first. Each item:

{"rank": 1, "kind": "binary" | "source", "files": ["src/a.rs:120-140", ...],
 "what": "the bloat, in one or two sentences",
 "change": "the exact change: which calls, types or functions, and how",
 "saves": "an estimate of bytes saved, or lines removed, and how you got it",
 "risk": "what could change in behavior, and how a test would show it"}

Give at most 30 items. Prefer a few large, certain wins over many small, unsure ones. For the sort
copies and syn visitor copies, name each call site that makes a separate copy, and say which ones
can share one copy.
