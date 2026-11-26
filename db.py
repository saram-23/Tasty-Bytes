from pathlib import Path
import sqlite3
import json

DB_PATH = Path(__file__).resolve().parent/"data"/"app.db"
recipes_path = Path(__file__).resolve().parent/"data"/"recipes.json"
ingredients_path = Path(__file__).resolve().parent/"data"/"ingredients.json"

def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
	db_path.parent.mkdir(parents=True, exist_ok=True)
	conn = sqlite3.connect(db_path)
	#query results will be sqlite3.Row objects
	conn.row_factory = sqlite3.Row
	conn.execute("PRAGMA foreign_keys = ON;")
	return conn

def create_tables() -> None:
	conn = get_connection()
	try:
		with conn:
			conn.executescript("""
				CREATE TABLE IF NOT EXISTS ingredients (
					ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT,
					name TEXT NOT NULL UNIQUE,
					kcal INTEGER NOT NULL,
					proteins INTEGER NOT NULL,
					carbohydrates INTEGER NOT NULL,
					fats INTEGER NOT NULL
				);

				CREATE TABLE IF NOT EXISTS recipes (
					recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
					title TEXT NOT NULL UNIQUE,
					cooking_h INTEGER NOT NULL,
					cooking_min INTEGER NOT NULL,
					servings INTEGER NOT NULL,
					instructions TEXT NOT NULL
				);

				CREATE TABLE IF NOT EXISTS recipe_ingredients (
					recipe_id INTEGER NOT NULL,
					ingredient_id INTEGER NOT NULL,
					quantity REAL NOT NULL,
					unit TEXT NOT NULL,
					sort_order INTEGER NOT NULL DEFAULT 0,
					PRIMARY KEY (recipe_id, ingredient_id),
					-- when recipe is deleted, so are all connections
					FOREIGN KEY (recipe_id) REFERENCES recipes (recipe_id) ON DELETE CASCADE,
					-- referenced ingredient can't be deleted
					FOREIGN KEY (ingredient_id) REFERENCES ingredients (ingredient_id) ON DELETE RESTRICT
				);

				-- speeds up searching after ingredient_id
				CREATE INDEX IF NOT EXISTS idx_recipe_ingredients_ingredient_id
					ON recipe_ingredients (ingredient_id);
			""")
	finally:
		conn.close()

def normalize(ingredient: str) -> str:
	ingredient = ingredient.lower()
	list = ingredient.rsplit()
	size = len(list)
	res = ""
	if size > 0:
		for x in list[:(size - 1)]:
			res = res + x + " "
		res = res + list[size - 1]
	if res == "":
		return " "
	return res

#initializing the database
create_tables()

#turning the .json files into lists of dictionaries
with open(ingredients_path, mode="r", encoding="utf-8") as read_ingredients:
	i_data = json.load(read_ingredients)

with open(recipes_path, mode="r", encoding="utf-8") as read_recipes:
	r_data = json.load(read_recipes)

#normalizing ingredients
pos = 0;
valid_ingredients = set()
wrong_pos = set()

for i in i_data:
	#kcal
	if not (("kcal" in i.keys()) and isinstance(i["kcal"], int) and not
		isinstance(i["kcal"], bool)):
		wrong_pos.add(pos)
		pos += 1
		continue

	#proteins
	if not (("proteins" in i.keys()) and isinstance(i["proteins"], int) and not
		isinstance(i["proteins"], bool)):
		wrong_pos.add(pos)
		pos += 1
		continue

	#carbohydrates
	if not (("carbohydrates" in i.keys()) and isinstance(i["carbohydrates"], int) and not
		isinstance(i["carbohydrates"], bool)):
		wrong_pos.add(pos)
		pos += 1
		continue

	#fats
	if not (("fats" in i.keys()) and isinstance(i["fats"], int) and not isinstance(i["fats"], bool)):
		wrong_pos.add(pos)
		pos += 1
		continue

	#name
	if isinstance(i["name"], str):
		#normalizing names
		i["name"] = normalize(i["name"])

		#no duplicates
		if i["name"] in valid_ingredients or i["name"] == " ":
			wrong_pos.add(pos)
			pos += 1
			continue
		else:
			valid_ingredients.add(i["name"])
	else:
		wrong_pos.add(pos)
		pos += 1
		continue

	pos += 1

for i in sorted(wrong_pos, reverse=True):
	i_data.pop(i)

#normalizing recipes
pos = 0
valid_recipes = set()
wrong_pos = set()

for r in r_data:
	ingredients = set()
	skip = False

	#cookig_h
	if not (("cooking_h" in r.keys()) and isinstance(r["cooking_h"], int) and not
		isinstance(r["cooking_h"], bool)):
		wrong_pos.add(pos)
		pos += 1
		continue

	#cooking_min
	if not(("cooking_min" in r.keys()) and isinstance(r["cooking_min"], int) and not
		isinstance(r["cooking_min"], bool)):
		wrong_pos.add(pos)
		pos += 1
		continue

	#servings
	if not(("servings" in r.keys()) and isinstance(r["servings"], int) and not
		isinstance(r["servings"], bool)):
		wrong_pos.add(pos)
		pos += 1
		continue

	#instructions
	if not (("instructions" in r.keys()) and isinstance(r["instructions"], str)):
		wrong_pos.add(pos)
		pos += 1
		continue

	#ingredients
	if not (("ingredients" in r.keys()) and isinstance(r["ingredients"], list) and
		len(r["ingredients"]) > 0):
		wrong_pos.add(pos)
		pos += 1
		continue

	for i in r["ingredients"]:
		#checking for all the needed fields
		if not (("name" in i.keys()) and ("quantity" in i.keys()) and
			("unit" in i.keys()) and ("sort_order" in i.keys())):
			wrong_pos.add(pos)
			pos += 1
			skip = True
			break

		#checking for proper data types
		if not (isinstance(i["quantity"], (int, float)) and not isinstance(i["quantity"], bool) and
			isinstance(i["unit"], str) and isinstance(i["sort_order"], int) and not
			isinstance(i["sort_order"], bool)):
			wrong_pos.add(pos)
			pos += 1
			skip = True
			break

		#normalizing ingredient names
		if isinstance(i["name"], str):
			i["name"] = normalize(i["name"])
		else:
			wrong_pos.add(pos)
			pos += 1
			skip = True
			break

		#checking that the ingredients exist
		if (i["name"] not in valid_ingredients) or i["name"] == " ":
			wrong_pos.add(pos)
			pos += 1
			skip = True
			break

		#no repeating ingredients
		if i["name"] in ingredients:
			wrong_pos.add(pos)
			pos += 1
			skip = True
			break
		else:
			ingredients.add(i["name"])

	if skip:
		continue

	#no repeating titles
	if ("title" in r.keys()) and isinstance(r["title"], str) and (r["title"] not in valid_recipes):
		valid_recipes.add(r["title"])
	else:
		wrong_pos.add(pos)
		pos += 1
		continue

	pos += 1

for i in sorted(wrong_pos, reverse=True):
	r_data.pop(i)

#populating the database
conn = get_connection()
cursor = conn.cursor()

try:
	with conn:
		#populating the ingredients table
		for i in i_data:
			conn.execute("""
				INSERT OR IGNORE INTO ingredients (name, kcal, proteins, carbohydrates, fats)
				VALUES (:name, :kcal, :proteins, :carbohydrates, :fats)
				""",
				i
			)

		#mapping ingredients to ids
		ingredient_key = {}

		cursor = conn.execute("SELECT name, ingredient_id FROM ingredients ORDER BY ingredient_id")
		for name, ingredient_id in cursor:
			ingredient_key.update({name: ingredient_id})

		#populating the recipes table
		for r in r_data:
			conn.execute("""
				INSERT OR IGNORE INTO recipes (title, cooking_h, cooking_min, servings, instructions)
				VALUES (:title, :cooking_h, :cooking_min, :servings, :instructions)
				""",
				r
			)

		#mapping recipes to ids
		recipe_key = {}

		cursor = conn.execute("SELECT title, recipe_id FROM recipes ORDER BY recipe_id")
		for title, recipe_id in cursor:
			recipe_key.update({title: recipe_id})

		#populating recipe_ingredients table
		for r in r_data:
			for i in r["ingredients"]:
				conn.execute("""
					INSERT OR IGNORE INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit, sort_order)
					VALUES (?, ?, ?, ?, ?)
					""",
					(recipe_key.get(r["title"]), ingredient_key.get(i["name"]), i["quantity"], i["unit"], i["sort_order"])
				)
finally:
	conn.close()
