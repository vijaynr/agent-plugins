---
name: using-context-engineering
description: Route local context-tooling setup requests for RTK, ripgrep, or Caveman. Use before loading installation instructions.
---

# Context Tooling Router

Read only the selected skill file, relative to this file:

- Token-filtered shell output: [setup-rtk](../setup-rtk/SKILL.md).
- Fast repository search: [setup-ripgrep](../setup-ripgrep/SKILL.md).
- Caveman installation or removal: [setup-caveman](../setup-caveman/SKILL.md).

Do not install tools merely because this router was loaded. Keep each skill's approval and verification gates. Do not let terse-output tools override required language, safety, or evidence rules.

Supporting skills are not automatically invoked. Read the selected file explicitly before acting. Load references only when the current step needs them. Reuse instructions already in context. Report missing files instead of scanning all plugins. Keep replies and command output concise; preserve failures and verification evidence.
