from fastapi import APIRouter
from database import get_conn
from models import RecipeAnalyzeRequest, RecipeResponse
from services.llm_nutrition import estimate_recipe_nutrition

router = APIRouter()


@router.post("/analyze", response_model=RecipeResponse)
def analyze_recipe(req: RecipeAnalyzeRequest):
    nutrition = estimate_recipe_nutrition(req.ingredients_raw, req.servings or 1)

    if req.save:
        conn = get_conn()
        conn.execute(
            """INSERT INTO recipes (name, ingredients_raw, servings, calories_per_serving, protein, carbs, fat)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (req.name, req.ingredients_raw, req.servings, nutrition.calories,
             nutrition.protein_g, nutrition.carbs_g, nutrition.fat_g),
        )
        conn.commit()
        conn.close()

    return RecipeResponse(
        name=req.name or nutrition.food_name,
        servings=req.servings or 1,
        calories_per_serving=nutrition.calories,
        protein=nutrition.protein_g,
        carbs=nutrition.carbs_g,
        fat=nutrition.fat_g,
        ingredients_raw=req.ingredients_raw,
    )


@router.get("", response_model=list[RecipeResponse])
def list_recipes():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM recipes ORDER BY created_at DESC").fetchall()
    conn.close()
    return [
        RecipeResponse(
            name=r["name"],
            servings=r["servings"],
            calories_per_serving=r["calories_per_serving"],
            protein=r["protein"],
            carbs=r["carbs"],
            fat=r["fat"],
            ingredients_raw=r["ingredients_raw"],
        )
        for r in rows
    ]
