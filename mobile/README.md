# StructuralPro Android
The Android client is designed to consume the same provider-neutral core contracts.
Phase 1 keeps the engineering engine authoritative on desktop/local core and defines
the mobile boundary for project list, project open, takeoff entry, report preview and
optional sync. No cloud account or API key is required for offline work.

Planned implementation target: Android 10+ using Kotlin/Jetpack Compose, with the
same project JSON/SyncRecord contracts. The mobile client must never reimplement
engineering formulas independently.
