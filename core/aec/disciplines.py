"""Canonical AEC discipline taxonomy used by takeoff, BOQ and project contracts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Discipline:
    key: str
    title_fa: str
    families: tuple[str, ...]


DISCIPLINES = (
    Discipline("architecture", "معماری", ("finishes", "doors_windows", "partitions", "ceilings")),
    Discipline("structural_concrete", "سازه بتنی", ("concrete", "rebar", "formwork")),
    Discipline("structural_steel", "سازه فولادی", ("steel", "connections", "deck")),
    Discipline("masonry", "بنا و دیوارچینی", ("block", "brick", "mortar", "stone")),
    Discipline("timber", "سازه چوبی", ("timber", "panels", "connections")),
    Discipline("composite", "سازه مرکب", ("composite", "deck", "steel_concrete")),
    Discipline("mechanical", "تأسیسات مکانیکی", ("hvac", "plumbing", "fire_protection")),
    Discipline("electrical", "تأسیسات برقی", ("power", "lighting", "low_voltage")),
    Discipline("renovation", "بهسازی و مرمت", ("demolition", "repair", "restoration")),
    Discipline("site_external", "محوطه و عملیات بیرونی", ("earthwork", "landscape", "external_utilities")),
)


def all_disciplines() -> tuple[Discipline, ...]:
    return DISCIPLINES


def get_discipline(key: str) -> Discipline:
    for item in DISCIPLINES:
        if item.key == key:
            return item
    raise KeyError(key)
