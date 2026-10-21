Find the dead code in chock.

Dead code is a function, method, constant, static, struct, enum, enum variant, field or trait
implementation outside `#[cfg(test)]` code that nothing in the repository uses: no call, no
reference, no use through a trait or a derive, no use from a macro, from tests/, from a binary
target or from a `pub` API that a user of the library crate could call. A `pub` item of the
library crate counts as used only if something in the repository uses it.

Rules:
- Search the whole repository for each name before you report it, and give the reason that
  nothing uses it.
- If you are not sure, leave the item out. A short correct list is better than a long one.
- At most 30 items.

Give each item as one line, in this form and nothing else:

<path>:<line> | <name> | <why nothing uses it>

If you find none, write NONE.
