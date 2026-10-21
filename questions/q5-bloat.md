Find the source code that makes chock's release binary bigger than it needs to be.

The release binary is 4,323,632 bytes. The release profile is `opt-level = "z"`, `lto = true`,
`codegen-units = 1` and `strip = true`. Do not change the profile, remove a dependency, or remove
a feature or a gate of chock. Every suggestion must keep the behaviour the same.

Look at the whole repository for machine code that the compiler makes more than once or that
does more than the task needs. Examples of what to look for (find the real cases in this code):
a generic function instantiated with many types, a closure type that makes a new copy of a
generic function at each call site, the same logic written in several files, large `match` or
`format!` code, many derives on types that do not need them, and dependency features that are
switched on but not used.

Rules:
- Each item must point to lines in this repository and name the fix.
- Give an estimate of the bytes saved, and say how sure you are: high, medium or low.
- If you are not sure that an item saves bytes, leave it out.
- At most 30 items, the most bytes first.

Give each item as one line, in this form and nothing else:

<path>:<line or line-line> | <what makes the extra code> | <the fix> | <bytes saved> | <high, medium or low>

If you find none, write NONE.
