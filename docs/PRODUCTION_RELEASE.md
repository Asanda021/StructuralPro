# Production Release

This boundary turns a verified release-preparation record into a deterministic production-release record. It requires the release version, source commit, preparation fingerprint, artifact manifest with SHA-256 digests, and an explicit rollback commit.

The repository's available GitHub integration can merge and verify release commits but cannot create GitHub Release objects; therefore this gate records and verifies the production release state in-repository rather than claiming an external deployment.
