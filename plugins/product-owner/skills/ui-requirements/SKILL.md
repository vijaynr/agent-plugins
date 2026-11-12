---
name: ui-requirements
disable-model-invocation: true
description: Create or review engineering-ready UI features, user flows, stories, and acceptance criteria when UX designs or a UI designer are not available. Use for no-design backlog handoffs and UI-heavy feature decomposition.
---

# Product Owner UI Requirements

## Purpose and boundaries

Use this skill to create features, user stories, UI requirements, user flows, and acceptance criteria when a UI designer or approved design is not available. Give engineers and testers enough information to implement and verify the user behavior without guessing product decisions.

Use simplified technical English. Follow the principles below. Do not claim ASD-STE100 compliance unless the team validates the output against the official specification.

Keep these items separate:

1. User problem
2. User goal
3. Functional requirement
4. UI behavior
5. Design suggestion
6. Acceptance criteria

Written requirements define expected behavior. A mockup is a reference, not the only requirement. Do not invent design references. Do not add UI detail that does not serve a user need.

The Product Owner defines the problem, goal, value, actors, scope, flow, product terms, functional behavior, permissions, important errors, UI expectations, and acceptance criteria.

Engineering defines components, internal state, API integration, code structure, technical design, performance implementation, and component reuse. Do not prescribe CSS, pixel sizes, internal classes, database design, or state management unless an approved requirement needs them. Engineering can suggest another interaction that meets the same goal and acceptance criteria.

The Product Owner and engineering share responsibility for usability, accessibility, UI consistency, errors, responsive behavior, and interaction quality.

## Mandatory language rules

Apply these rules to **all generated features, stories, requirements, acceptance criteria, and tracker content**. They are not only rules for writing this skill.

- Use short sentences. Put one main action or condition in each sentence.
- Use active voice. Name the actor: “The system shows an error message.”
- Use the same noun for the same object. Keep existing product labels and role names. For example, use **User Source** throughout if that is the product term. Do not switch to Directory or Identity Source unless these mean different things.
- Prefer simple verbs: show, select, open, close, add, remove, save, cancel, edit, delete, change, start, stop, send, receive, enter, choose, enable, disable.
- Remove vague words such as easy, intuitive, modern, simple, clean, user-friendly, quickly, properly, correctly, seamless, and appropriate from requirements. Replace them with observable behavior.
- Use positive statements when possible. Keep negative statements when a restriction matters.
- Write one requirement for one behavior. Split processing, success, and failure behavior.
- Keep the technical meaning. Do not simplify away a condition, restriction, or approved product term.

Prefer:

> The user selects **Save**.
> The system saves the changes.
> The system shows an error message if the save operation fails.

Avoid:

> Upon selection of Save, the application shall attempt to persist the modifications and provide appropriate feedback.

Instead of “The dialog must be easy to use,” write an agreed behavior such as “The user can complete the operation without opening another page.” Do not turn an example into an unapproved requirement.

## Select the mode

- **Create**: draft a feature or story with the process and output format below.
- **Review**: assess an existing feature or story, then return an improved version.
- **Decompose**: identify flows, propose the minimum set of valuable stories, identify dependencies and UI-heavy stories, then add behavior and acceptance criteria.

For backlog decomposition, explicitly read [to-backlogs](../to-backlogs/SKILL.md) if it is not already in context. Follow its breakdown approval gate before writing final story bodies. Reuse instructions already loaded. Do not load unrelated skills.

This skill drafts requirements. It does not authorize tracker writes. Keep user review and artifact confirmation gates. Publishing requires an explicit request, approval of the final content, and read-after-write verification through the owning tracker plugin.

## Creation process

### 1. Gather evidence and define intent

Use supplied notes, product documents, current behavior, and available screens or designs. Record useful references. Distinguish known behavior from proposed behavior. Ask for a product decision when the answer changes scope or user behavior.

Define:

- **Problem**: who has the problem, what they need to do, what prevents it now, and why it matters. Do not start with a UI solution.
- **Goal**: the result the user needs.
- **User value**: why the result matters. Keep it short. Avoid marketing language.
- **Actors**: existing product roles. Do not invent synonyms for roles.
- **Scope**: functions included in the feature. Add Out of Scope only when it prevents misunderstanding.

Problem example: “An administrator cannot identify the active provider without opening each provider.”

Goal example: “The administrator can identify the active provider from the provider list.”

“The provider table needs an Active column” is a proposed solution, not a problem statement.

### 2. Define the user flow and stories

Write a numbered main flow. Use one user action or system response per step. Include relevant alternate paths. Do not include internal calls or implementation steps.

Example:

1. The administrator opens the Identity Providers page.
2. The system shows the configured providers.
3. The administrator opens the row actions for an inactive provider.
4. The administrator selects **Activate**.
5. The system starts the activation.
6. The system updates the provider status after success.

Use this story format:

> As a <role>,
> I want to <action>,
> so that I can <user result>.

Keep detail outside the story sentence. Each story must deliver user value. Do not split only into database, REST endpoint, or UI component stories. Those can be engineering tasks. For large features, identify the main flows, propose the minimum useful story set, and state dependencies. Do not invent dependencies or split into many small stories without value.

### 3. Define UI information and interaction

Describe the information and actions needed for the outcome:

- Main information and important groups
- Main action and secondary actions
- Status information
- Tables, lists, forms, and dialogs when needed
- Required product labels

For forms, specify required inputs, allowed values, defaults, validation, and unsaved-value behavior where these affect the user. For navigation or dialogs, describe entry, exit, cancel, and return behavior where relevant. Mark unknown product rules as questions rather than inventing values.

For tables and lists, check search, filter, sort, pagination, selection, and bulk actions. Include only functions with a user need. For large data sets, describe how the user finds and acts on items. Leave implementation to engineering.

Select UI patterns in this order:

1. Existing behavior in the same feature
2. Existing product pattern
3. Existing shared component
4. Platform convention
5. Simple new interaction
6. Custom interaction

Check relevant tables, row actions, forms, dialogs, confirmations, status indicators, notifications, validation messages, search, filters, tabs, side panels, empty states, and loading states.

If a reference is known, write “Use the same interaction pattern as <screen or component>.” Otherwise, write “Use an existing product pattern where possible.” Do not claim an unverified pattern exists. Use a custom interaction only when other patterns do not meet the need.

Separate mandatory behavior from design preference:

- **Requirement**: “The administrator must be able to see the provider status from the provider list.”
- **Expected Interaction**: “Show the provider status in the provider row.” Mark this as a suggestion unless the interaction itself is required.
- **Design Flexibility**: engineering can choose the status component and layout. The status must remain visible without opening the provider.

### 4. Define applicable UI states

For each important interaction, check the states below. Include only states that apply. Do not require an invented state to fill a template.

| State | Required information when applicable |
|---|---|
| Initial / default | What the user sees when the UI opens. Include current values or status. |
| User action | What the user selects or enters. State the preconditions. |
| Loading / processing | What remains available during the request. State whether repeated actions are blocked. Add an indicator only when it helps explain the state. |
| Success | What data or status changes. Define the resulting screen or dialog state. Require a notification only if the visible change is not enough feedback. |
| Error / failure | What failed, what state remains, and what the user can do next. Preserve entered values when required. |
| Empty | What appears when no data exists. Show a creation action only when the user has permission. |
| Disabled | When an action is disabled. Give a way to understand the reason if it is not clear. |
| Read-only / permission restricted | Which roles can view or change data. Follow the product rule for hiding, disabling, or showing read-only controls. |
| Selected | What selection means and which actions it enables. |
| New / modified / removed | How pending changes appear and what save, cancel, or undo does. |

Do not infer permission policy from a visible control. If the policy is unknown, raise an open product question. UI visibility alone does not define authorization.

Error requirements must explain what failed, what state remains, and the next action. For example: the add-user dialog stays open after failure; entered values remain; the system shows the available reason. Avoid “Something went wrong” when more useful information is available. Do not expose sensitive internal details in messages.

For delete or remove, check data loss, undo, and the existing confirmation pattern. Require confirmation only when needed. If required, state what it explains, including the item name and the known effect. Do not guess deletion policy.

### 5. Define shared quality expectations

Include applicable accessibility behavior:

- The user can access interactive controls with the keyboard.
- Controls have accessible names.
- Status does not rely on color alone.
- Focus moves to a logical element when a dialog opens or closes.
- Assistive technology can access error information.

Describe responsive behavior as an outcome. For example: “The action remains available on a narrow screen.” Use exact breakpoints only when the product has approved standard breakpoints. Do not prescribe pixel offsets.

### 6. Write acceptance criteria

Make criteria short, observable, testable, and tied to user behavior. Use Given / When / Then when it improves clarity. Put one action or condition in each sentence or clause line. Cover applicable processing, success, failure, permission, and edge behavior, not only the happy path.

Use stable labels such as AC1 and AC2 so engineers and testers can refer to them. Check that each mandatory behavior has a criterion. Do not make optional design suggestions mandatory through acceptance criteria.

Example:

### AC1 — Show provider status

**Given** the administrator opens the Identity Providers page,
**When** the system shows the providers,
**Then** the system shows the status of each provider.

### AC2 — Process activation

**Given** a provider is inactive,
**When** the administrator selects **Activate**,
**Then** the system starts the activation.
**And** the system prevents a second activation request while the first request is in progress.

### AC3 — Complete activation

**Given** an activation request is in progress,
**When** the activation succeeds,
**Then** the system shows the new provider status.

### AC4 — Activation failure

**Given** an activation request is in progress,
**When** the activation fails,
**Then** the system keeps the previous provider status.
**And** the system shows an error message that explains the failure and the available next action.

Do not write “works correctly,” “user-friendly,” or “handles errors properly.” State the result. For example: “If the Save request fails, the system keeps the unsaved values in the form.”

### 7. Record assumptions and open decisions

Continue with a safe assumption only when it is clearly marked in **Assumptions**. Do not present assumptions as approved requirements.

Never assume security policy, permission policy, data deletion, compliance, or backward compatibility. Record these as **Open Product Questions**. Do not use a permission rule as a safe-assumption example.

Ask a question only when its answer can change user behavior or scope. Do not ask the Product Owner to choose internal components or technical architecture. Identify affected stories and criteria for unresolved decisions. Mark those stories as draft or blocked for the affected behavior. Do not claim they are ready for implementation until the blocking decision is resolved.

## Default output format

Use this structure unless the user requests another format. Omit sections that do not apply. Repeat the story block for each approved story. For backlog output, retain Parent, Blocked by, and User stories covered references from `to-backlogs` where applicable. Add the UI sections to its What to build content; do not replace its approval process.

```markdown
# Feature: <Name>

## Problem
## Goal
## User Value
## Actors
## Scope
### In Scope
### Out of Scope
## User Flow
1. <One action or system response.>

# User Story: <Name>
> As a <role>,
> I want to <action>,
> so that I can <result>.

## UI Requirements
<Required functional behavior.>
## UI Structure
<Information, actions, labels, inputs, and groups.>
## Initial State
## User Actions
## Processing State
## Success State
## Failure State
## Permission Behavior
## Empty State
## Other Applicable States
<Disabled, read-only, selected, new, modified, or removed behavior.>
## Accessibility
## Responsive Behavior
## Existing Product Pattern
<Known reference, or use an existing product pattern where possible.>
## Expected Interaction
<Design suggestion. Mark any required interaction explicitly.>
## Acceptance Criteria
### AC1 — <Title>
**Given** ...
**When** ...
**Then** ...
## Design Flexibility
Engineering can:
- ...
Engineering must keep:
- ...
## Blocked by
<Confirmed dependency, or none.>
## Assumptions
## Open Product Questions
<Affected behavior and readiness impact.>
```

Each story must contain enough context for independent implementation and testing. Include relevant feature intent, role, scope, and pattern references in its tracker body. Do not rely on a chat transcript or a mockup alone. Provide maximum useful behavior information, not repeated prose or invented detail.

## Review mode

Review the problem, goal, value, scope, flow, UI behavior, loading, success, failure, permissions, edge cases, existing patterns, and acceptance criteria. Identify unnecessary implementation detail and unresolved product decisions.

Return:

- **Strong**: requirements that are clear.
- **Missing**: important behavior that is absent.
- **Unclear**: statements with more than one meaning.
- **Too Detailed**: implementation choices that are not product requirements.
- **Recommended Version**: the improved requirement in the required language style. Keep unresolved product choices visible.

## Final review and mandatory rewrite

Before returning a feature, story, review, or final tracker payload:

- Check that the problem, goal, value, scope, roles, and main flow are clear.
- Check that each story delivers user value and states real dependencies.
- Check all applicable UI states, errors, recovery, permissions, and edge cases.
- Check existing patterns, accessibility, and responsive behavior where applicable.
- Separate requirements from suggestions. Keep engineering design flexibility.
- Check that criteria cover mandatory behavior and are observable and testable.
- Keep assumptions and open decisions visible. Do not claim unresolved stories are ready.
- Remove unnecessary UI and internal implementation detail.
- **Rewrite every requirement so that one sentence contains one main action or condition. Remove vague words. Use the same noun for the same object.**
- Use active voice and the shortest sentence that keeps the technical meaning.

If a check fails, improve the output before returning it. Apply this rewrite to the actual generated story and acceptance-criteria text, including the final Jira or other tracker content, not only to a summary.
