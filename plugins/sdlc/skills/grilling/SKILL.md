---
name: grilling
disable-model-invocation: true
description: "Grill a plan or design one question at a time with recommended answers."
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../../references/output-language.md), including for delegated work.

## Question UX

Use `vscode/askQuestions` whenever available so the user gets a focused,
interactive question UI. Ask exactly **one question at a time** and wait for the
user's response before continuing. Asking multiple questions at once is
bewildering.

For each question:

1. State the decision or uncertainty being tested.
2. Provide your recommended answer and a brief rationale.
3. Ask one concrete question with clear options when possible.
4. Wait for the user's answer before asking the next question.

If `vscode/askQuestions` is unavailable, ask the same single question directly
in chat using the same structure.

If a question can be answered by exploring the codebase, explore the codebase instead.
