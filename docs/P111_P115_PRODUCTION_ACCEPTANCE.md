# P111-P115 Production Acceptance

## P111 — Authorized Iranian Data Boundary
The product now has a strict import contract for supplied Iranian price-list CSV data. The caller must provide HTTPS provenance, edition/publisher metadata and the exact SHA-256 of the supplied source. The importer validates schema, numeric values and duplicate codes. It deliberately does **not** promote imported data to “official” merely because a URL looks governmental. Actual authorized files must be supplied and verified separately.

## P112 — Professional Report Pack
A deterministic professional report contract covers BOQ output, Persian/RTL presentation metadata, validation, project identity and revision identity. Existing CSV/XLSX/PDF/DOCX exporters remain the delivery layer; the acceptance gate verifies the report payload before export.

## P113 — Revision and Change Impact
Revision comparison propagates object changes into quantity/material/cost impact. Added, removed and materially changed rows require explicit review. A revision cannot be finalized while required reviews remain pending.

## P114 — Large Project Hardening
A deterministic 5,000-row revision workload is exercised in the production gate. The acceptance threshold is five seconds on the CI runner and the same workload is checked for repeatability. This is a regression guard, not a hardware-independent performance guarantee.

## P115 — Release Readiness
Release readiness validates the canonical semantic version and offline hardening gates, and explicitly records external evidence that still must exist for a commercial release: authorized Iranian datasets, real DWG/IFC runtimes where applicable, Windows release artifacts and production signing credentials when required.

## Cycle
Gap/Acceptance Scope -> Implementation -> Dedicated Tests -> Dedicated CI -> Full Regression -> QA -> Windows -> PR -> Green Gates -> Merge -> Main Verification -> Post-Merge Verification.
