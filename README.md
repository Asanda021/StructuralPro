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

## Windows release

The canonical application version is stored in `VERSION`. Windows packaging is reproducible through `packaging/build_windows.ps1` and `packaging/structuralpro.spec`. The installer template is `packaging/installer.iss` and the Windows release workflow runs on `v*` tags after verifying the tag matches `VERSION`.

The release layer also defines an offline licensing boundary in `core/platform/release.py`. License signature verification is injected so a production asymmetric-key verifier can be supplied without embedding a signing secret in the desktop client.

The commercial license lifecycle boundary also validates expiration, revocation, entitlement uniqueness and fail-closed identity/signature conditions. See `docs/COMMERCIAL_LICENSE_LIFECYCLE.md`.

## Release documentation

- [User Guide](docs/USER_GUIDE.md)
- [Installation Guide](docs/INSTALLATION.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [Configuration](docs/CONFIGURATION.md)
- [Licensing](docs/LICENSE.md)
- [Commercial License Lifecycle](docs/COMMERCIAL_LICENSE_LIFECYCLE.md)
- [Backup and Restore](docs/BACKUP_RESTORE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Release Checklist](docs/RELEASE_CHECKLIST.md)
- [Versioning and Release Process](docs/RELEASE_PROCESS.md)


## In-app help
The offline help contract is available in `core/help/content.py` and covers startup, takeoff, reports, backup/recovery, and AI usage. It is intentionally deterministic and does not depend on network access.
