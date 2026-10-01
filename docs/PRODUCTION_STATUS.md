# StructuralPro — production pass

This pass upgrades the deterministic core rather than claiming full product parity.

## Implemented in this pass
- Offline/year-aware price catalog with group/chapter navigation, search, validation and CSV import/export.
- Price snapshots for project-level reproducibility.
- BOQ normalization, aggregation, warnings and summary.
- Cost breakdown with configurable commercial factors.
- PDF inspection plus conservative text/dimension candidate extraction. Candidates are explicitly marked for confirmation; this is not claimed as full computer vision.
- Windows desktop entry shell with RTL-ready Persian labels.
- Regression tests for pricing, BOQ and costing.

## Still not represented as production-complete
- Native binary DWG parsing without an external converter.
- Full IFC quantity extraction.
- Computer-vision PDF plan recognition.
- Complete official Iranian annual price-list datasets.
- Final multi-device cloud synchronization and conflict resolution.
- Full Android/Telegram clients.
- Full commercial-grade reporting designer.

The product remains offline-first: network services are optional and must not be required for core takeoff, calculation or local AI.
