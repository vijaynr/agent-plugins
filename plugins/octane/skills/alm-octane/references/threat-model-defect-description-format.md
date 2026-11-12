# Threat Modelling Defect Description Format

Use this only when constructing or validating a threat-model Octane defect description.

The description must be detailed enough for an engineer, tester, and security reviewer to understand and verify the issue without reopening the whole threat model.

ALM Octane defect descriptions are rich-text HTML strings in the JSON payload, for example `"description": "<html><body>...</body></html>"`. The `create-defect` command automatically converts Markdown/plain-text headings, lists, and code fences into safe Octane HTML before sending the payload. Existing `<html>...</html>` descriptions are passed through unchanged.

Author descriptions may use this Markdown/plain-text source structure:

```text
## Threat Summary
Threat ID: THR-###
Source: Threat Model
STRIDE Category: <Spoofing | Tampering | Repudiation | Information Disclosure | Denial of Service | Elevation of Privilege>
Threat Catalog Category: <catalog category>
Scenario: <concrete abuse case in 2-4 sentences>

## Affected Scope
Feature/Flow: <feature or flow name>
Affected Component(s): <component/process/service>
Affected Asset(s): <data/credential/resource>
Affected Data Flow(s): <DFD flow IDs or names>
Trust Boundary: <boundary crossed, if any>
User/Attacker Preconditions: <required role, access, tenant context, network position, etc.>

## Evidence
DFD Evidence: <component/flow/boundary evidence from data-flow-diagram.md>
Architecture/Code Evidence: <file paths, APIs, configs, or architecture notes supporting reachability>
Audit Disposition: <kept by tm-threat-auditor, including rationale>
Existing Controls: <controls already present and why residual risk remains>

## Risk Rating
CVSS Vector: <CVSS:3.1/...>
Base Score: <score>
Severity: <Low | Medium | High | Critical>
Impact: <confidentiality/integrity/availability/privacy/audit impact>
Exploitability Notes: <why exploitation is realistic or constrained>

## Required Mitigation
Mitigation ID(s): <MIT-###>
Recommended Fix: <specific engineering change expected>
Security Test ID(s): <SEC-TEST-###>
Residual Risk After Fix: <expected residual risk or validation expectation>

## References
Threat Model Report: threat-model-report.md
DFD: data-flow-diagram.md
Threat Catalog: threat-catalog.xlsx / threat-catalog.md
Initial Analysis: initial-analysis-form.docx / initial-analysis-form.md
```

Include the acceptance criteria in the description body because defect creation has no separate acceptance-criteria field.
