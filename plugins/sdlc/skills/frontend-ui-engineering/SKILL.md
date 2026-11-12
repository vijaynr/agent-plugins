---
name: frontend-ui-engineering
disable-model-invocation: true
description: Builds stack-neutral, production-quality user interfaces. Use when building or modifying browser, mobile, desktop, terminal, or embedded user-facing interfaces, including layout, interaction, state, accessibility, and visual quality.
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../../references/output-language.md), including for delegated work.

# Frontend UI Engineering

## Overview

Build user interfaces that are accessible, responsive/adaptive, performant, consistent with the product design system, and pleasant to use. The UI should look intentional, not generated: real content, clear hierarchy, consistent spacing, predictable interactions, and complete loading/error/empty states.

This skill is stack-neutral. Apply it to the UI technology in the current project: web, mobile, desktop, terminal, embedded, native, hybrid, or design-system component libraries.

## When to Use

- Building new screens, views, pages, forms, components, widgets, or terminal/desktop flows
- Modifying user-facing interfaces
- Implementing responsive/adaptive layout
- Adding interaction or state management
- Fixing visual, accessibility, usability, or UX issues
- Integrating with a design system or component library

## Interface Architecture

### Follow Existing Project Structure

Use the project’s established conventions for:

- Component/view/screen organization
- Test location and naming
- Stories/previews/examples if the project uses them
- State/data fetching patterns
- Styling/theme/token system
- Accessibility and localization conventions

Do not introduce a new framework, state library, styling system, or directory pattern unless the task explicitly calls for it.

### Use the Project Design System

Read the project's component library, design tokens, accessibility guidance, and approved design references before creating new patterns. Reuse existing components where possible. Ask for missing design references rather than routing to an unbundled plugin. SDLC keeps ownership of lifecycle artifacts and decisions.

### Prefer Composition Over Over-Configuration

Build small pieces that can be composed rather than one component/view with many flags that create hidden modes.

```text
Good:
  Dialog
    DialogHeader
    DialogBody
    DialogActions

Risky:
  Dialog(title, body, primaryAction, secondaryAction, variant, layoutMode,
         showIcon, showClose, align, density, footerMode, ...)
```

Configuration is fine for real variation. Avoid configuration that hides unrelated responsibilities in one component.

### Keep UI Units Focused

A screen/component/view should have a clear responsibility. Split when one unit handles too many concerns:

- Data loading
- Permission decisions
- Domain mutation
- Presentation
- Validation
- Navigation
- Analytics/logging
- Error recovery

Container/presenter, model/view, controller/view, or equivalent separation can help. Use the pattern native to the stack.

### Separate Remote/Data State From Presentation State

Choose the simplest state owner that works:

| State type | Typical owner |
|---|---|
| Local interaction state | The smallest component/view/screen that needs it |
| Shared UI state | Nearest common parent or scoped context/model |
| Navigation/shareable state | Route, URL, command arguments, or platform navigation state |
| Remote/server/device state | Existing data/cache layer or service abstraction |
| App-wide state | Existing global store/model only when genuinely cross-cutting |

Avoid passing state through layers that do not use it. Restructure or introduce a scoped state boundary when necessary.

## Design System Adherence

### Use Project Tokens and Components

Prefer existing design-system components, tokens, and patterns for:

- Color
- Typography
- Spacing
- Elevation/depth
- Radius/corners
- Icons
- Motion
- Form controls
- Feedback/status states

Do not invent raw values when a token or component exists. If no design system exists, establish a small local scale and document it.

### Avoid Generic Generated UI

| Generic default | Better production choice |
|---|---|
| Random accent colors or gradients | Product palette and semantic colors |
| Oversized cards and padding everywhere | Information hierarchy and product spacing scale |
| Placeholder/lorem content | Realistic content with edge-case lengths |
| Shadow-heavy decoration | Depth only when it communicates hierarchy |
| Stock layouts detached from the workflow | Content-first layout based on user tasks |
| Icons without text for critical actions | Clear labels, tooltips, or accessible names |

### Layout and Responsiveness

Design for the range of supported viewports, densities, devices, locales, and input modes.

Check:

- Smallest supported width/height
- Typical laptop/desktop/tablet/mobile sizes when relevant
- High-density or scaled displays
- Long localized text
- Zoom/font scaling
- Reduced motion preferences
- Touch, mouse, keyboard, screen reader, and other supported input modes

Use the project’s breakpoints/layout primitives. Do not hardcode arbitrary pixel values unless the design system requires them.

### Typography and Content Hierarchy

- One clear primary heading/title per view when applicable
- Heading levels/order reflect structure, not visual preference
- Body, secondary, helper, and error text are visually distinct
- Labels are specific and action-oriented
- Empty/error/loading copy tells users what happened and what to do next

### Color and Status

- Use semantic color roles when available
- Meet contrast requirements for the product/accessibility target
- Do not rely on color alone to communicate state
- Include text/icon/pattern changes for errors, warnings, success, disabled, selected, and pending states

## Accessibility

Meet the accessibility standard required by the product and jurisdiction. For web, WCAG 2.1/2.2 AA is a common baseline; for native/mobile/desktop, use the platform accessibility guidance and APIs.

Minimum checks:

- Every interactive element is reachable and operable with supported input methods
- Focus/selection state is visible and logical
- Screen readers/accessibility APIs expose names, roles, values, and state
- Forms have labels, validation messages, and error summaries where appropriate
- Dialogs, menus, popovers, and navigation manage focus correctly
- Dynamic content changes are announced when necessary
- Motion respects reduced-motion preferences
- Text supports zoom/scaling and localization

Prefer native/platform controls when they satisfy the design. Custom controls must recreate keyboard, focus, state, and assistive-technology behavior.

## User States

Every user-facing flow should handle:

- Initial/default state
- Loading/pending/progress state
- Empty/no-results state
- Validation errors
- Permission/authentication failures
- Network/device/external dependency failures
- Partial success or retryable failure when applicable
- Success/confirmation state
- Disabled/read-only state

Blank screens and silent failures are defects.

## Stable Test Selectors

When browser, component, or E2E tests need stable locators, add explicit test selectors according to project convention. For web projects, prefer `data-testid` only when semantic selectors such as role, label, text, or accessible name are insufficient or too brittle for the test intent.

Rules:

- One selector has one purpose: stable test location. Do not reuse test IDs for styling, analytics, or production logic.
- Name selectors by user/domain intent, not implementation structure: `invite-submit-button`, not `blue-button-3`.
- Add selectors to meaningful interactive or asserted elements: primary actions, form fields, dialogs, table rows/cells, status messages, error summaries, and workflow milestones.
- Avoid selectors on purely decorative wrappers unless the wrapper is the behavior under test.
- Keep selectors stable across visual refactors. Renaming a selector is a test contract change.
- Prefer project-local naming conventions when they exist.

## User-Facing Text and Localization

Follow the project's localization/i18n system for all user-facing text.

Rules:

- Do not hardcode new user-visible strings when the project uses translation catalogs, resource bundles, message files, or equivalent localization infrastructure.
- Translate whole phrases instead of concatenating translated fragments. Fragment concatenation breaks grammar in many languages.
- Keep placeholder names stable and meaningful, such as `{name}` or `{count}`.
- Provide translator context for ambiguous labels, short strings, security-sensitive wording, or domain terms when the project supports comments/metadata.
- Include accessibility text in localization scope: `aria-label`, tooltip text, empty-state text, validation messages, error summaries, and confirmation copy.
- Test with long text, missing keys/fallback behavior, and at least one non-default locale when practical.
- If a project requires updating all locale files, do so or clearly mark untranslated placeholders according to project convention.

## Performance

UI should feel responsive:

- Avoid blocking the main/user-interaction thread with heavy work
- Keep lists/large datasets bounded, virtualized, paginated, or progressively rendered as appropriate
- Avoid unnecessary re-render/re-layout/recomposition work in the project’s UI framework
- Defer non-critical work until after first useful interaction/render
- Use optimized media/assets appropriate to the platform
- Measure before making complex performance changes; use `performance-optimization` for deeper work

## Verification

After building or changing UI:

- [ ] UI follows existing project architecture and design-system conventions
- [ ] Realistic content is used, including long/empty/error cases
- [ ] Loading, empty, error, permission, success, and disabled states are handled where applicable
- [ ] Supported input methods work, including keyboard/focus behavior where relevant
- [ ] Accessibility names/roles/states/labels are correct for the platform
- [ ] Layout works at supported screen sizes, zoom/font scaling, and localization constraints
- [ ] User-facing text follows the project localization convention
- [ ] Stable test selectors are present where tests need them and semantic selectors are insufficient
- [ ] No console/runtime/accessibility warnings are introduced in the relevant environment
- [ ] Relevant unit/component/integration/E2E/manual checks were run and captured

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We'll polish later" | Visual and interaction debt compounds quickly and shapes review confidence. |
| "Accessibility is a nice-to-have" | Accessibility is an engineering quality requirement and often a legal/product requirement. |
| "The design is not final" | Use existing product defaults instead of unstyled or generic generated UI. |
| "It works on my screen" | Users have different devices, zoom, text length, input methods, and permissions. |
| "This is just a prototype" | Prototypes often become production; keep the foundation sound. |

## Red Flags

- New UI framework, state library, styling system, or architecture introduced without approval
- Missing loading/error/empty states
- Interactive elements without accessible names or focus behavior
- Color as the only indicator of state
- Arbitrary spacing/color/type values despite existing tokens
- Layout tested at only one size or locale
- Generic generated look that ignores product design language
- UI change without runtime verification in the relevant environment
