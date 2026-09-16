# Spec: reader first, link first

- **Intent:** ./intent.md
- **Author:** Claude (AI agent)
- **Signed-off-by:** Tim WU
- **Accepted-by:** Tim WU
- **Status:** signed-off

## Requirements

1. The live URL <https://timwukp.github.io/ai-native-sdlc/> appears as the first
   actionable line after the title, and again in "How it publishes".
2. A "What you will learn" section lists the outcomes in the page's register: the loop,
   the three enforcement strengths, the four traps, the honest-limits position, the lab.
   Every listed outcome must correspond to a section that exists on the page; nothing on
   the forbidden-phrase list in `verify.py` may appear.
3. The disambiguation paragraph, the non-affiliation line, and all existing maintainer
   sections (Sources, Layout, Verify, checked-by-hand, publishes, built, Licence) are
   retained; reader material precedes maintainer material.
4. `index.html` and `verify.py` are untouched; `verify.py` still passes.

## Out of scope

Repository metadata (description, homepage, topics) is set through the API, not a commit —
recorded in the intent because it is part of the same ask, but it produces no diff here.
