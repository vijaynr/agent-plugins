# Threat Modelling User Story Description Format

Use this when constructing or validating a consolidated threat-model Octane user story description.

The story is used when the user chooses to track all identified threat-model findings in one remediation story instead of creating one defect per threat. The description must be detailed enough for engineering, QA, and security reviewers to implement and verify all mitigations without reopening the entire threat model.

`tm-document-defects` must convert the structured source content into an ALM Octane rich-text HTML string before creating the story, for example:

```html
<html><body>...</body></html>
```

## Required HTML structure

```html
<html><body>
<h2>Threat Model Findings</h2>
<p>
  Consolidated remediation story for threat-model findings under feature
  <b>&lt;feature/system name&gt;</b>. This story tracks all identified threats
  from the completed threat model and must be implemented and verified as a unit.
</p>

<h2>Issues</h2>

<h3>THR-### — &lt;short threat summary&gt;</h3>
<table>
  <tr><th>Severity</th><td>&lt;Low | Medium | High | Critical&gt;</td></tr>
  <tr><th>CVSS</th><td>&lt;score&gt; — <code>CVSS:3.1/...</code></td></tr>
  <tr><th>STRIDE Category</th><td>&lt;category&gt;</td></tr>
  <tr><th>Affected Scope</th><td>&lt;component / asset / data flow / trust boundary&gt;</td></tr>
  <tr><th>Evidence</th><td>&lt;DFD, code, architecture, audit evidence&gt;</td></tr>
  <tr><th>Required Mitigation</th><td>&lt;specific engineering change&gt;</td></tr>
  <tr><th>Security Test</th><td>&lt;SEC-TEST-### or verification&gt;</td></tr>
</table>

<!-- Repeat one h3 + table for every identified threat. -->

<h2>Required Mitigations</h2>
<ul>
  <li><b>MIT-###:</b> &lt;mitigation mapped to THR-###&gt;</li>
</ul>

<h2>Acceptance Criteria Summary</h2>
<p>
  Acceptance criteria are maintained in the Octane story's separate
  <code>acceptance_criteria</code> field. This section may summarize the
  verification approach, but it is not a substitute for the separate field.
</p>

<h2>References</h2>
<ul>
  <li>Threat Model Report: <code>threat-model-report.md</code></li>
  <li>Threat Catalog: <code>threat-catalog.xlsx</code> / <code>threat-catalog.md</code></li>
  <li>DFD: <code>data-flow-diagram.md</code></li>
  <li>Initial Analysis: <code>initial-analysis-form.docx</code> / <code>initial-analysis-form.md</code></li>
</ul>
</body></html>
```

## Required content rules

1. Include every identified threat exactly once in the `Issues` section.
2. Include each threat ID (`THR-###`), severity, CVSS score, and CVSS vector exactly as rated.
3. Include affected scope, evidence, required mitigation, and security test for every threat.
4. Acceptance criteria must be supplied as the story's separate Octane `acceptance_criteria` field and must cover every threat, not just High/Critical items.
5. The HTML description may include an `Acceptance Criteria Summary`, but the authoritative criteria belong in the separate `acceptance_criteria` field.
6. The created story must have `threat-catalog.xlsx` and `threat-catalog.md` attached directly to the story when available.
7. Do not omit lower-severity threats unless the orchestrator explicitly revised the identified threat list before story creation.

## Suggested story title

```text
[TM] Address threat model findings for <feature/system>
```

Do not include severity labels or individual `THR-*` IDs in the story title.
