"""
Unit-Tests für normalize_form_datetime (siehe Issue #57, Fix-Vorschlag Punkt 3):
deckt die drei laut Docstring akzeptierten Eingabeformate ab (naiv, Browser-UTC
mit "Z", ISO mit explizitem Offset) sowie Leer-/Ungültig-Werte.
"""
from app.form_datetime import normalize_form_datetime


def test_naive_value_is_interpreted_as_berlin_wall_time():
    result = normalize_form_datetime("2026-07-09T14:30")

    assert result == "2026-07-09T14:30:00+02:00"


def test_naive_value_in_winter_uses_winter_offset():
    result = normalize_form_datetime("2026-01-09T14:30")

    assert result == "2026-01-09T14:30:00+01:00"


def test_utc_value_with_z_suffix_is_converted_to_berlin_time():
    # 12:00 UTC im Sommer entspricht 14:00 Berlin-Sommerzeit (+02:00)
    result = normalize_form_datetime("2026-07-09T12:00:00Z")

    assert result == "2026-07-09T14:00:00+02:00"


def test_value_with_explicit_offset_is_converted_to_berlin_time():
    # 09:00 -05:00 entspricht 14:00 UTC, also 16:00 Berlin-Sommerzeit
    result = normalize_form_datetime("2026-07-09T09:00:00-05:00")

    assert result == "2026-07-09T16:00:00+02:00"


def test_none_value_returns_none():
    assert normalize_form_datetime(None) is None


def test_empty_string_returns_none():
    assert normalize_form_datetime("") is None


def test_whitespace_only_string_returns_none():
    assert normalize_form_datetime("   ") is None


def test_invalid_string_returns_none():
    assert normalize_form_datetime("not-a-date") is None
