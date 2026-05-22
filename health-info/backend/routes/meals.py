from datetime import date as _date
from fastapi import APIRouter, HTTPException
from database import get_conn
from models import MealCreate, MealResponse
from services.llm_nutrition import estimate_food_nutrition
from services.whatsapp_service import maybe_send_calorie_alert

router = APIRouter()


def _today() -> str:
    return _date.today().isoformat()


@router.post("", response_model=MealResponse)
def log_meal(meal: MealCreate):
    day = meal.date or _today()
    nutrition = estimate_food_nutrition(meal.food_name, meal.quantity or "1 serving")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO meals (date, meal_type, food_name, quantity, calories, protein, carbs, fat, fiber, sugar)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (day, meal.meal_type, nutrition.food_name, meal.quantity,
         nutrition.calories, nutrition.protein_g, nutrition.carbs_g,
         nutrition.fat_g, nutrition.fiber_g, nutrition.sugar_g),
    )
    meal_id = cur.lastrowid

    # Check calorie total and send WhatsApp alert if needed
    cur.execute("SELECT COALESCE(SUM(calories), 0) FROM meals WHERE date = ?", (day,))
    total_today = cur.fetchone()[0]
    cur.execute("SELECT daily_calorie_goal, whatsapp_number FROM profile WHERE id = 1")
    profile = cur.fetchone()
    conn.commit()
    conn.close()

    if profile:
        maybe_send_calorie_alert(total_today, profile["daily_calorie_goal"], profile["whatsapp_number"])

    conn2 = get_conn()
    row = conn2.execute("SELECT * FROM meals WHERE id = ?", (meal_id,)).fetchone()
    conn2.close()
    return dict(row)


@router.get("/{day}", response_model=list[MealResponse])
def get_meals(day: str):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM meals WHERE date = ? ORDER BY logged_at", (day,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.delete("/{meal_id}")
def delete_meal(meal_id: int):
    conn = get_conn()
    result = conn.execute("DELETE FROM meals WHERE id = ?", (meal_id,))
    conn.commit()
    conn.close()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Meal not found")
    return {"deleted": meal_id}
