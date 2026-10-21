Find the places where the documentation and the code disagree.

The documentation is README.md, every file under docs/, the 0.13.0 and 0.12.0 sections of
CHANGELOG.md, .chock/agents.md, .claude/skills/chock/SKILL.md, and the help text in src/usage.rs.
A disagreement is a statement there that the code does not do, does differently, or no longer
has (a flag, a config key, a gate, a default value, a file path, a count, a version).

Rules:
- Report only a disagreement that you can show with a line in the documentation and a line in
  the code. Read both lines before you report.
- Do not report style, wording or a missing explanation.
- If you are not sure, leave the item out. A short correct list is better than a long one.
- At most 40 items, the most harmful to a user first.

Give each item as one line, in this form and nothing else:

DOC <path>:<line> | CODE <path>:<line> | <the difference, in one sentence>

If you find none, write NONE.
