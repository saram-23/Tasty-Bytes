"""Tests for Component 3.4 nutritional calculations and Tailwind Jinja2 templates."""

from __future__ import annotations

from pathlib import Path
import unittest

from jinja2 import Environment, FileSystemLoader, select_autoescape

import db
import nutrition

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


class NutritionCalculationTests(unittest.TestCase):
    def test_to_grams_conversions_and_validation(self) -> None:
        self.assertEqual(nutrition.to_grams(250, "g"), 250.0)
        self.assertEqual(nutrition.to_grams(1.5, "kg"), 1500.0)
        self.assertEqual(nutrition.to_grams(500, "mg"), 0.5)
        with self.assertRaises(ValueError):
            nutrition.to_grams(-10, "g")
        with self.assertRaises(ValueError):
            nutrition.to_grams(10, "cups")

    def test_calculate_recipe_nutrition_totals_and_per_serving(self) -> None:
        ingredients = [
            {
                "name": "chicken breast",
                "kcal": 120,
                "proteins": 23,
                "carbohydrates": 0,
                "fats": 2,
                "quantity": 200,
                "unit": "g",
            },
            {
                "name": "olive oil",
                "kcal": 884,
                "proteins": 0,
                "carbohydrates": 0,
                "fats": 100,
                "quantity": 10,
                "unit": "g",
            },
            {
                "name": "white rice",
                "kcal": 365,
                "proteins": 7,
                "carbohydrates": 80,
                "fats": 1,
                "quantity": 100,
                "unit": "g",
            },
        ]
        result = nutrition.calculate_recipe_nutrition(ingredients, servings=2)

        # Total: kcal = 240 + 88.4 + 365 = 693.4 -> 693
        # proteins = 46 + 0 + 7 = 53.0
        # carbs = 0 + 0 + 80 = 80.0
        # fats = 4 + 10 + 1 = 15.0
        self.assertEqual(result["servings"], 2)
        self.assertEqual(
            result["total"],
            {"kcal": 693, "proteins": 53.0, "carbohydrates": 80.0, "fats": 15.0},
        )
        self.assertEqual(
            result["per_serving"],
            {"kcal": 347, "proteins": 26.5, "carbohydrates": 40.0, "fats": 7.5},
        )
        self.assertEqual(sum(result["macro_percentages"].values()), 100)

    def test_invalid_servings_raises(self) -> None:
        with self.assertRaises(ValueError):
            nutrition.calculate_recipe_nutrition([], servings=0)

    def test_get_recipe_nutrition_from_database(self) -> None:
        conn = db.get_connection()
        try:
            row = conn.execute(
                "SELECT recipe_id, servings FROM recipes ORDER BY recipe_id LIMIT 1"
            ).fetchone()
            self.assertIsNotNone(row)
            result = nutrition.get_recipe_nutrition(row["recipe_id"], conn=conn)
            self.assertIsNotNone(result)
            self.assertEqual(result["servings"], row["servings"])
            self.assertGreater(result["per_serving"]["kcal"], 0)
            self.assertIsNone(nutrition.get_recipe_nutrition(-9999, conn=conn))
        finally:
            conn.close()


class TemplateRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def test_all_templates_render_with_tailwind(self) -> None:
        conn = db.get_connection()
        try:
            ingredients = conn.execute(
                "SELECT ingredient_id, name FROM ingredients ORDER BY name LIMIT 5"
            ).fetchall()
            recipe = conn.execute(
                "SELECT recipe_id, title, cooking_h, cooking_min, servings, instructions FROM recipes ORDER BY recipe_id LIMIT 1"
            ).fetchone()
            recipe_ingredients = conn.execute(
                """
                SELECT i.name, ri.quantity, ri.unit
                FROM recipe_ingredients ri
                JOIN ingredients i ON i.ingredient_id = ri.ingredient_id
                WHERE ri.recipe_id = ?
                """,
                (recipe["recipe_id"],),
            ).fetchall()
            recipe_nutrition = nutrition.get_recipe_nutrition(
                recipe["recipe_id"], conn=conn
            )
        finally:
            conn.close()

        index_html = self.env.get_template("index.html").render(ingredients=ingredients)
        self.assertIn("https://cdn.tailwindcss.com", index_html)
        self.assertIn("Find Recipes", index_html)

        results_html = self.env.get_template("results.html").render(
            recipes=[
                {
                    "recipe_id": recipe["recipe_id"],
                    "title": recipe["title"],
                    "cooking_h": recipe["cooking_h"],
                    "cooking_min": recipe["cooking_min"],
                    "servings": recipe["servings"],
                    "match_percent": 80,
                    "matched_count": 4,
                    "total_ingredients": 5,
                }
            ],
            page_title="Matching Recipes",
        )
        self.assertIn("80% match", results_html)

        detail_html = self.env.get_template("recipe_detail.html").render(
            recipe=recipe,
            ingredients=recipe_ingredients,
            nutrition=recipe_nutrition,
        )
        self.assertIn("Nutritional Breakdown", detail_html)
        self.assertIn(str(recipe_nutrition["per_serving"]["kcal"]), detail_html)

        new_html = self.env.get_template("recipe_new.html").render(
            ingredients=ingredients
        )
        self.assertIn("Add a New Recipe", new_html)


if __name__ == "__main__":
    unittest.main()
