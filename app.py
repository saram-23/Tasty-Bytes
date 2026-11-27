"""FastAPI web application for Tasty Bytes."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import db
import nutrition

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Tasty Bytes")


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    """Render the fridge ingredient selection page (Component 3.2)."""
    conn = db.get_connection()
    try:
        ingredients = conn.execute(
            "SELECT ingredient_id, name FROM ingredients ORDER BY name ASC"
        ).fetchall()
    finally:
        conn.close()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"ingredients": ingredients},
    )


@app.get("/recipes", response_class=HTMLResponse)
def list_recipes(request: Request) -> HTMLResponse:
    """Render all available recipes."""
    conn = db.get_connection()
    try:
        recipes = conn.execute(
            """
            SELECT recipe_id, title, cooking_h, cooking_min, servings
            FROM recipes
            ORDER BY title ASC
            """
        ).fetchall()
    finally:
        conn.close()

    return templates.TemplateResponse(
        request=request,
        name="results.html",
        context={"recipes": recipes, "page_title": "All Recipes"},
    )


@app.post("/recipes/match", response_class=HTMLResponse)
def match_recipes(
    request: Request,
    ingredient_ids: list[int] = Form(default=[]),
) -> HTMLResponse:
    """Match recipes against selected fridge ingredients (Component 3.3)."""
    selected = set(ingredient_ids)
    matched_recipes: list[dict] = []

    if selected:
        conn = db.get_connection()
        try:
            recipes = conn.execute(
                "SELECT recipe_id, title, cooking_h, cooking_min, servings FROM recipes"
            ).fetchall()
            links = conn.execute(
                "SELECT recipe_id, ingredient_id FROM recipe_ingredients"
            ).fetchall()
        finally:
            conn.close()

        recipe_ingredients_map: dict[int, set[int]] = {}
        for link in links:
            recipe_ingredients_map.setdefault(link["recipe_id"], set()).add(
                link["ingredient_id"]
            )

        for recipe in recipes:
            req_ids = recipe_ingredients_map.get(recipe["recipe_id"], set())
            if not req_ids:
                continue
            matched_count = len(req_ids & selected)
            if matched_count == 0:
                continue
            match_percent = round((matched_count / len(req_ids)) * 100)
            matched_recipes.append(
                {
                    "recipe_id": recipe["recipe_id"],
                    "title": recipe["title"],
                    "cooking_h": recipe["cooking_h"],
                    "cooking_min": recipe["cooking_min"],
                    "servings": recipe["servings"],
                    "matched_count": matched_count,
                    "total_ingredients": len(req_ids),
                    "match_percent": match_percent,
                }
            )

        matched_recipes.sort(
            key=lambda r: (-r["match_percent"], -r["matched_count"], r["title"])
        )

    return templates.TemplateResponse(
        request=request,
        name="results.html",
        context={"recipes": matched_recipes, "page_title": "Matching Recipes"},
    )


@app.get("/recipes/new", response_class=HTMLResponse)
def new_recipe_form(request: Request) -> HTMLResponse:
    """Render the add-recipe form (Component 3.1)."""
    conn = db.get_connection()
    try:
        ingredients = conn.execute(
            "SELECT ingredient_id, name FROM ingredients ORDER BY name ASC"
        ).fetchall()
    finally:
        conn.close()

    return templates.TemplateResponse(
        request=request,
        name="recipe_new.html",
        context={"ingredients": ingredients},
    )


@app.post("/recipes/new")
def create_recipe(
    title: str = Form(...),
    cooking_h: int = Form(0),
    cooking_min: int = Form(0),
    servings: int = Form(1),
    instructions: str = Form(...),
    ingredient_ids: list[int] = Form(...),
    quantities: list[float] = Form(...),
    units: list[str] = Form(...),
) -> RedirectResponse:
    """Persist a new recipe and redirect to its detail page (Component 3.1)."""
    clean_title = title.strip()
    clean_instructions = instructions.strip()
    if not clean_title or not clean_instructions or servings <= 0:
        raise HTTPException(status_code=400, detail="Invalid recipe details")

    conn = db.get_connection()
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO recipes (title, cooking_h, cooking_min, servings, instructions)
                VALUES (?, ?, ?, ?, ?)
                """,
                (clean_title, cooking_h, cooking_min, servings, clean_instructions),
            )
            recipe_id = cursor.lastrowid
            seen_ingredients: set[int] = set()
            for sort_order, (ing_id, qty, unit) in enumerate(
                zip(ingredient_ids, quantities, units)
            ):
                if ing_id in seen_ingredients or qty <= 0:
                    continue
                seen_ingredients.add(ing_id)
                conn.execute(
                    """
                    INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit, sort_order)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (recipe_id, ing_id, qty, unit.strip() or "g", sort_order),
                )
    finally:
        conn.close()

    return RedirectResponse(url=f"/recipes/{recipe_id}", status_code=303)


@app.get("/recipes/{recipe_id}", response_class=HTMLResponse)
def recipe_detail(request: Request, recipe_id: int) -> HTMLResponse:
    """Render recipe details with nutritional breakdown (Components 3.4 & 3.5)."""
    conn = db.get_connection()
    try:
        recipe = conn.execute(
            """
            SELECT recipe_id, title, cooking_h, cooking_min, servings, instructions
            FROM recipes
            WHERE recipe_id = ?
            """,
            (recipe_id,),
        ).fetchone()
        if recipe is None:
            raise HTTPException(status_code=404, detail="Recipe not found")

        ingredients = conn.execute(
            """
            SELECT i.name, ri.quantity, ri.unit
            FROM recipe_ingredients ri
            JOIN ingredients i ON i.ingredient_id = ri.ingredient_id
            WHERE ri.recipe_id = ?
            ORDER BY ri.sort_order ASC, i.name ASC
            """,
            (recipe_id,),
        ).fetchall()

        recipe_nutrition = nutrition.get_recipe_nutrition(recipe_id, conn=conn)
    finally:
        conn.close()

    return templates.TemplateResponse(
        request=request,
        name="recipe_detail.html",
        context={
            "recipe": recipe,
            "ingredients": ingredients,
            "nutrition": recipe_nutrition,
        },
    )
