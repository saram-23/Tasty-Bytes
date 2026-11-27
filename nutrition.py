"""Component 3.4: Nutritional statistics calculation logic.

Calculates total and per-serving macronutrients (calories, protein,
carbohydrates, fats) for recipes based on ingredient quantities and
standard per-100g nutritional values stored in SQLite.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Mapping, Sequence

import db

UNIT_TO_GRAMS: dict[str, float] = {
    "g": 1.0,
    "gram": 1.0,
    "grams": 1.0,
    "kg": 1000.0,
    "mg": 0.001,
    "ml": 1.0,
    "l": 1000.0,
}


def to_grams(quantity: float, unit: str = "g") -> float:
    """Convert an ingredient quantity and unit to grams."""
    if quantity < 0:
        raise ValueError(f"Quantity must be non-negative, got {quantity}")
    normalized_unit = unit.strip().lower()
    if normalized_unit not in UNIT_TO_GRAMS:
        raise ValueError(f"Unsupported unit: {unit!r}")
    return float(quantity) * UNIT_TO_GRAMS[normalized_unit]


def calculate_ingredient_macros(
    kcal_per_100g: float,
    proteins_per_100g: float,
    carbohydrates_per_100g: float,
    fats_per_100g: float,
    quantity: float,
    unit: str = "g",
) -> dict[str, float]:
    """Calculate macros for a single ingredient quantity."""
    grams = to_grams(quantity, unit)
    factor = grams / 100.0
    return {
        "kcal": kcal_per_100g * factor,
        "proteins": proteins_per_100g * factor,
        "carbohydrates": carbohydrates_per_100g * factor,
        "fats": fats_per_100g * factor,
    }


def _round_macros(macros: Mapping[str, float]) -> dict[str, float]:
    """Round nutritional totals to clean display precision."""
    return {
        "kcal": round(macros["kcal"]),
        "proteins": round(macros["proteins"], 1),
        "carbohydrates": round(macros["carbohydrates"], 1),
        "fats": round(macros["fats"], 1),
    }


def calculate_macro_percentages(macros: Mapping[str, float]) -> dict[str, int]:
    """Calculate calorie share percentages for protein, carbs, and fats."""
    protein_kcal = max(0.0, macros["proteins"]) * 4.0
    carb_kcal = max(0.0, macros["carbohydrates"]) * 4.0
    fat_kcal = max(0.0, macros["fats"]) * 9.0
    total_macro_kcal = protein_kcal + carb_kcal + fat_kcal

    if total_macro_kcal <= 0:
        return {"proteins": 0, "carbohydrates": 0, "fats": 0}

    p_pct = round((protein_kcal / total_macro_kcal) * 100)
    c_pct = round((carb_kcal / total_macro_kcal) * 100)
    f_pct = max(0, 100 - p_pct - c_pct)
    return {
        "proteins": p_pct,
        "carbohydrates": c_pct,
        "fats": f_pct,
    }


def calculate_recipe_nutrition(
    ingredients: Sequence[Mapping[str, Any]],
    servings: int,
) -> dict[str, Any]:
    """Sum ingredient macros and compute total and per-serving nutrition."""
    if servings <= 0:
        raise ValueError(f"Servings must be positive, got {servings}")

    totals = {"kcal": 0.0, "proteins": 0.0, "carbohydrates": 0.0, "fats": 0.0}

    for item in ingredients:
        item_macros = calculate_ingredient_macros(
            kcal_per_100g=float(item["kcal"]),
            proteins_per_100g=float(item["proteins"]),
            carbohydrates_per_100g=float(item["carbohydrates"]),
            fats_per_100g=float(item["fats"]),
            quantity=float(item["quantity"]),
            unit=str(item["unit"]) if "unit" in item.keys() else "g",
        )
        for key in totals:
            totals[key] += item_macros[key]

    per_serving_raw = {key: value / servings for key, value in totals.items()}
    per_serving = _round_macros(per_serving_raw)

    return {
        "servings": servings,
        "total": _round_macros(totals),
        "per_serving": per_serving,
        "macro_percentages": calculate_macro_percentages(per_serving_raw),
    }


def get_recipe_nutrition(
    recipe_id: int,
    conn: sqlite3.Connection | None = None,
) -> dict[str, Any] | None:
    """Fetch a recipe's ingredients from SQLite and compute its nutrition."""
    owns_conn = conn is None
    if conn is None:
        conn = db.get_connection()

    try:
        recipe_row = conn.execute(
            "SELECT recipe_id, servings FROM recipes WHERE recipe_id = ?",
            (recipe_id,),
        ).fetchone()
        if recipe_row is None:
            return None

        ingredient_rows = conn.execute(
            """
            SELECT
                i.name,
                i.kcal,
                i.proteins,
                i.carbohydrates,
                i.fats,
                ri.quantity,
                ri.unit
            FROM recipe_ingredients ri
            JOIN ingredients i ON i.ingredient_id = ri.ingredient_id
            WHERE ri.recipe_id = ?
            ORDER BY ri.sort_order ASC, i.name ASC
            """,
            (recipe_id,),
        ).fetchall()

        return calculate_recipe_nutrition(
            ingredients=ingredient_rows,
            servings=int(recipe_row["servings"]),
        )
    finally:
        if owns_conn:
            conn.close()
