"""Commercial product packaging contract for StructuralPro.

The matrix is intentionally domain-agnostic: StructuralPro is a comprehensive
construction takeoff/BOQ/estimating product, not a concrete-only application.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProductEdition(str, Enum):
    LIGHT = "light"
    STANDARD = "standard"
    PRO = "pro"
    ENTERPRISE = "enterprise"


FEATURES = (
    "takeoff.boq",
    "takeoff.drawing",
    "takeoff.pdf",
    "takeoff.cad",
    "takeoff.bim",
    "takeoff.ai",
    "revision.compare",
    "estimate.cost",
    "reports.export",
    "collaboration",
    "offline.core",
    "local.ai",
    "api.integration",
    "enterprise.controls",
)


@dataclass(frozen=True)
class ProductProfile:
    edition: ProductEdition
    features: frozenset[str]

    def supports(self, feature: str) -> bool:
        return bool(feature) and feature in self.features


def _profile(edition: ProductEdition, *features: str) -> ProductProfile:
    unknown = set(features) - set(FEATURES)
    if unknown:
        raise ValueError(f"Unknown product features: {sorted(unknown)}")
    return ProductProfile(edition, frozenset(features))


_PRODUCT_PROFILES = {
    ProductEdition.LIGHT: _profile(
        ProductEdition.LIGHT,
        "takeoff.boq",
        "takeoff.drawing",
        "takeoff.pdf",
        "reports.export",
        "offline.core",
    ),
    ProductEdition.STANDARD: _profile(
        ProductEdition.STANDARD,
        "takeoff.boq",
        "takeoff.drawing",
        "takeoff.pdf",
        "takeoff.cad",
        "takeoff.bim",
        "revision.compare",
        "estimate.cost",
        "reports.export",
        "offline.core",
        "local.ai",
    ),
    ProductEdition.PRO: _profile(
        ProductEdition.PRO,
        "takeoff.boq",
        "takeoff.drawing",
        "takeoff.pdf",
        "takeoff.cad",
        "takeoff.bim",
        "takeoff.ai",
        "revision.compare",
        "estimate.cost",
        "reports.export",
        "collaboration",
        "offline.core",
        "local.ai",
        "api.integration",
    ),
    ProductEdition.ENTERPRISE: _profile(
        ProductEdition.ENTERPRISE,
        *FEATURES,
    ),
}


def product_profile(edition: ProductEdition | str) -> ProductProfile:
    try:
        edition = ProductEdition(edition)
    except ValueError as exc:
        raise ValueError(f"Unsupported product edition: {edition!r}") from exc
    return _PRODUCT_PROFILES[edition]


def feature_matrix() -> dict[str, tuple[str, ...]]:
    return {
        edition.value: tuple(
            feature for feature in FEATURES if profile.supports(feature)
        )
        for edition, profile in _PRODUCT_PROFILES.items()
    }


def validate_license_features(
    edition: ProductEdition | str,
    licensed_features: tuple[str, ...] | list[str] | set[str],
) -> bool:
    """Return true only when every licensed feature belongs to the edition."""
    profile = product_profile(edition)
    requested = set(licensed_features)
    return requested <= profile.features
