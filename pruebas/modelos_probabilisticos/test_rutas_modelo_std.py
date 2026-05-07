"""Constantes de rutas citadas en STD 4.6.1 (comprobacion trivial, sin simulador Petri)."""

from __future__ import annotations


def test_happy_path_places_ordering() -> None:
    happy = ("P1", "P2", "P3", "P4", "P5", "P8", "P9", "P10", "P11")
    assert happy[0] == "P1"
    assert happy[-1] == "P11"


def test_resilience_loop_includes_p12() -> None:
    resilience = ("P12", "T11", "P1")
    assert "P12" in resilience
