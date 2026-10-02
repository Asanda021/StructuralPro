# StructuralPro implementation status

## Current verified state

StructuralPro is a Windows-first offline construction quantity, estimation and project platform with executable CI coverage across core application, drawing, persistence, calculation/quantity, UI, reporting/export and release surfaces.

The current Main branch has completed Priority 49, including real Windows installer acceptance testing.

## Verified release surfaces

- Desktop PySide6 application structure
- Project/takeoff/estimate/report modules
- Pricing and commercial modules
- CAD/DXF/DWG adapter architecture
- IFC/BIM adapter architecture
- Offline mode and synchronization queue architecture
- Local AI facade and deterministic fallback
- Reproducible Windows packaging
- Installer install/run/uninstall smoke acceptance
- Regression, QA, drawing and Windows smoke workflows

## Remaining release dependencies

The following require external provisioning or evidence rather than speculative repository implementation:

- Licensed/verified official Iranian annual price-list datasets.
- A redistributable GGUF model and license/checksum evidence if a model is bundled.
- An approved DWG converter/SDK and redistribution/runtime terms if DWG conversion is shipped.
- Windows code-signing certificate and secure signing procedure where required.
- Final third-party dependency/license evidence for the exact release environment.
- Android and Telegram native distribution deliverables, if those clients are included in the release scope.

These dependencies are intentionally explicit so repository tests do not create a false claim of commercial readiness.
