List every key that the file `.chock/config.json` can hold.

Use src/project/config.rs and the types it uses. Give the full dotted path for a nested key, such
as `proof.mutants` or `tla.smt_encoding`, and spell each name as the JSON spells it, after any
serde rename. Include `$schema` if the code accepts it. Do not list a key of a map whose names the
user chooses (such as a model name under `tla.smt_encoding`).

For each key, find:
- the line in src/project/config.rs (or the file that defines its type) where the field is;
- one line under docs/ or in README.md that names the key, or NONE;
- whether schema/config-v1.json defines it: yes or no.

Give each key as one line, in this form and nothing else:

<key> | <path>:<line of the field> | <doc path>:<line> or NONE | schema yes or no

After the last line, write END.
