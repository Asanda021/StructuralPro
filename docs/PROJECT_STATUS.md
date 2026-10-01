# StructuralPro implementation status

## Verified in the local development source
- Desktop PySide6 application structure
- Project/takeoff/estimate/report modules
- Pricing and commercial modules
- CAD/DXF/DWG adapter architecture
- IFC/BIM adapter architecture
- Offline mode and synchronization queue architecture
- Local AI facade and deterministic fallback
- 67 existing automated tests passing in the local development tree

## Important production gaps
- The official Iranian annual price-list datasets must be licensed/validated and imported.
- A redistributable GGUF model must be selected and license-checked.
- Windows installer packaging and hardware-based model selection must be completed and tested.
- Android client and Telegram client are separate deliverables sharing the same contracts.
- Native DWG support may require an approved converter/SDK; DXF is the safer direct parsing path.

These are tracked explicitly so the product is not represented as finished when a production dependency is still pending.
