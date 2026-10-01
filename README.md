# StructuralPro

Offline-First construction quantity takeoff, estimation and project platform.

## Current architecture
- Windows desktop first
- Android and Telegram clients planned against the same project/data contracts
- Local project database and local calculations
- Optional cloud synchronization only when internet is available
- Local AI engine with no mandatory API key or AI subscription
- GGUF model support through a local runtime adapter
- Deterministic engineering calculations remain separate from AI

## Offline AI
The application treats AI as a built-in local component. A GGUF model is loaded from the local `models/` directory when available. If no large model is installed, the deterministic local QA engine remains available.

The repository intentionally does **not** commit multi-gigabyte model weights. Production installers can bundle an approved model or install it locally as an optional component after checking its commercial license.

## Engineering principle
AI can inspect, classify, suggest and explain; it must not silently replace deterministic quantity/calculation engines.

## Project status
The working StructuralPro source is being moved into this repository incrementally from the local development build.

## Production gate status

The repository now includes executable production-gate tests for offline DWG conversion/extraction, graphical PDF geometry, IFC/BIM mapping, price-source provenance, local AI hardware/model validation, shared Windows/mobile/Telegram contracts, offline sync E2E, and report/regression paths.

Core work remains offline-first. External provisioning is intentionally explicit: verified official price-list datasets, redistributable GGUF model weights, native platform packaging, and an installed DWG converter are not fabricated or silently replaced by cloud services.


CI production-gate verification checkpoint.
