List every call site of these six functions in the whole repository.

1. `normalized`, defined at src/gates/proofs/patch.rs:78
2. `copied`, defined at src/gates/proofs/patch.rs:93
3. `copied`, defined at src/oracle.rs:274 (a different function with the same name)
4. `run_paced`, defined at src/exec/mod.rs:353
5. `Finding::sort_by_place`, defined at src/run/report.rs:121
6. `relative`, defined at src/project/mod.rs:42

Rules:
- A call site is a line that calls the function or names it as a value. Count calls inside
  closures, inside tests, and a call of the function from inside itself.
- Resolve each name the way rustc does: through `use` lines, module paths and scope. The method
  `Iterator::copied` or `Option::copied` is not function 2 or 3. `relative` at
  src/gates/proofs/tla.rs:284 and the test helper `relative` at src/run/baseline.rs:1016 are
  other functions; a call that resolves to them is not a call of function 6.
- Give the line of the call itself, not the first line of the function that holds it.

Give each call site as one line, in this form and nothing else:

<number of the function> | <path>:<line of the call> | <name of the enclosing function>

After the last line, write END.
