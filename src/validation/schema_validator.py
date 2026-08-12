"""
src/validation/schema_validator.py
Validates extracted values against the category schema JSON.
No hardcoding — reads min/max/enum/type from the schema file at runtime.
"""
from __future__ import annotations
from typing import Any
from src.models import ValidationResult


# Unit conversion table — only the most common industrial cases
# Keys are units found in documents, values are (target_unit, multiplier)
UNIT_CONVERSIONS: dict[str, dict[str, tuple[str, float]]] = {
    "mm": {
        "cm": ("mm", 10.0),
        "m":  ("mm", 1000.0),
        "in": ("mm", 25.4),
        "inch": ("mm", 25.4),
        "inches": ("mm", 25.4),
    },
    "kn": {
        "n":   ("kN", 0.001),
        "lbf": ("kN", 0.00444822),
        "kgf": ("kN", 0.00980665),
    },
    "kw": {
        "w":  ("kW", 0.001),
        "hp": ("kW", 0.745700),
        "ps": ("kW", 0.735499),
    },
    "m3/h": {
        "l/min":  ("m3/h", 0.06),
        "gpm":    ("m3/h", 0.227125),
        "l/s":    ("m3/h", 3.6),
        "m³/h":   ("m3/h", 1.0),
    },
    "a": {
        # Amperes — no common conversions needed
    },
    "v": {
        # Volts — no common conversions needed
    },
    "ka": {
        "a": ("kA", 0.001),
    },
}


def _try_unit_convert(
    value: float,
    unit_found: str | None,
    target_unit: str | None,
) -> tuple[float, bool]:
    """
    Try to convert value from unit_found to target_unit.
    Returns (converted_value, was_converted).
    """
    if unit_found is None or target_unit is None:
        return value, False

    uf = unit_found.lower().strip()
    tu = target_unit.lower().strip()

    if uf == tu:
        return value, False  # already correct unit

    conversions_for_target = UNIT_CONVERSIONS.get(tu, {})
    if uf in conversions_for_target:
        _, multiplier = conversions_for_target[uf]
        return round(value * multiplier, 6), True

    return value, False


def validate_field(
    value: Any,
    field_def: dict,
    unit_found: str | None = None,
) -> ValidationResult:
    """
    Validate a single extracted value against its schema field definition.

    field_def shape (from schema JSON):
      {
        "type": "number" | "string" | "integer",
        "unit": "mm",
        "min": 0.5,
        "max": 400.0,
        "enum": ["chrome_steel", ...],
        "required": true
      }
    """
    if value is None:
        return ValidationResult(passed=False, reason="value is null")

    field_type = field_def.get("type", "string")
    target_unit = field_def.get("unit")
    converted_value = value

    # ── Type check ────────────────────────────────────────────────────────────
    if field_type in ("number", "integer"):
        try:
            numeric = float(str(value).replace(",", "."))
        except (ValueError, TypeError):
            return ValidationResult(
                passed=False,
                reason=f"value '{value}' cannot be parsed as a number",
            )

        # ── Unit conversion ───────────────────────────────────────────────────
        numeric, was_converted = _try_unit_convert(numeric, unit_found, target_unit)
        if was_converted:
            converted_value = numeric

        # ── Range check ───────────────────────────────────────────────────────
        min_val = field_def.get("min")
        max_val = field_def.get("max")

        if min_val is not None and numeric < min_val:
            return ValidationResult(
                passed=False,
                reason=f"value {numeric} is below minimum {min_val} {target_unit or ''}",
                converted_value=converted_value,
            )
        if max_val is not None and numeric > max_val:
            return ValidationResult(
                passed=False,
                reason=f"value {numeric} exceeds maximum {max_val} {target_unit or ''}",
                converted_value=converted_value,
            )

        return ValidationResult(
            passed=True,
            reason=f"value {numeric} is within [{min_val}, {max_val}] {target_unit or ''}",
            converted_value=converted_value,
        )

    elif field_type == "string":
        enum_values = field_def.get("enum")
        str_value = str(value).strip().lower()

        if enum_values:
            enum_lower = [str(e).lower() for e in enum_values]
            # Exact match first
            if str_value in enum_lower:
                return ValidationResult(
                    passed=True,
                    reason=f"'{value}' is a valid enum value",
                    converted_value=enum_values[enum_lower.index(str_value)],
                )
            # Partial match (e.g. "stainless" matches "stainless_steel")
            for i, ev in enumerate(enum_lower):
                if str_value in ev or ev in str_value:
                    return ValidationResult(
                        passed=True,
                        reason=f"'{value}' partially matched to '{enum_values[i]}'",
                        converted_value=enum_values[i],
                    )
            return ValidationResult(
                passed=False,
                reason=f"'{value}' not in allowed values: {enum_values}",
            )

        # No enum constraint — any non-empty string passes
        if str_value:
            return ValidationResult(passed=True, reason="non-empty string value")
        return ValidationResult(passed=False, reason="empty string value")

    # Unknown type — pass through
    return ValidationResult(passed=True, reason=f"no constraint for type '{field_type}'")
