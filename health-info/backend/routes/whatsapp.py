from datetime import date as _date
from fastapi import APIRouter, Request, Response
from database import get_conn
from services.llm_nutrition import parse_whatsapp_intent, estimate_food_nutrition, estimate_recipe_nutrition
from services.whatsapp_service import send_whatsapp, maybe_send_calorie_alert
import config

router = APIRouter()


def _today() -> str:
    return _date.today().isoformat()


def _get_profile():
    conn = get_conn()
    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else {}


def _handle_log_meal(data: dict, day: str) -> str:
    items = data.get("items", [])
    meal_type = data.get("meal_type", "meal")
    if not items:
        return "I couldn't identify any food items. Try: 'I had 2 rotis and dal for lunch'"

    lines = []
    total_cal = 0.0
    conn = get_conn()
    for item in items:
        n = estimate_food_nutrition(item.get("food", "food"), item.get("quantity", "1 serving"))
        conn.execute(
            """INSERT INTO meals (date, meal_type, food_name, quantity, calories, protein, carbs, fat, fiber, sugar)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (day, meal_type, n.food_name, item.get("quantity"), n.calories,
             n.protein_g, n.carbs_g, n.fat_g, n.fiber_g, n.sugar_g),
        )
        lines.append(f"• {n.food_name}: {round(n.calories)} kcal (P:{n.protein_g}g C:{n.carbs_g}g F:{n.fat_g}g)")
        total_cal += n.calories

    day_total = conn.execute(
        "SELECT COALESCE(SUM(calories), 0) FROM meals WHERE date = ?", (day,)
    ).fetchone()[0]
    conn.commit()
    conn.close()

    profile = _get_profile()
    goal = profile.get("daily_calorie_goal", config.DEFAULT_CALORIE_GOAL)
    summary = f"\n\n📊 Today: {round(day_total)}/{goal} kcal ({round(day_total/goal*100)}%)"

    maybe_send_calorie_alert(day_total, goal, profile.get("whatsapp_number", ""))

    return f"✅ Logged {meal_type}:\n" + "\n".join(lines) + summary


def _handle_log_activity(data: dict, day: str) -> str:
    activity_type = data.get("activity_type", "other")
    steps = data.get("steps", 0)
    duration = data.get("duration_minutes", 0)

    calories_burned = steps * 0.04 if steps else 0
    if not calories_burned and duration:
        met_map = {"walk": 3.5, "run": 8.0, "gym": 5.0, "cycling": 6.0, "other": 4.0}
        met = met_map.get(activity_type, 4.0)
        calories_burned = round(met * 70 * duration / 60, 1)

    conn = get_conn()
    conn.execute(
        "INSERT INTO activity (date, activity_type, steps, duration_minutes, calories_burned) VALUES (?, ?, ?, ?, ?)",
        (day, activity_type, steps, duration, calories_burned),
    )
    conn.commit()
    conn.close()

    parts = []
    if steps:
        parts.append(f"{steps:,} steps")
    if duration:
        parts.append(f"{duration} min")
    return f"🏃 Activity logged: {activity_type} — {', '.join(parts)}\n🔥 ~{round(calories_burned)} kcal burned"


def _handle_recipe(data: dict) -> str:
    ingredients = data.get("ingredients", "")
    servings = int(data.get("servings", 1))
    name = data.get("name", "Recipe")
    if not ingredients:
        return "Please include ingredients. Try: 'recipe: palak paneer - 200g paneer, 500g spinach'"

    n = estimate_recipe_nutrition(ingredients, servings)
    return (
        f"🍳 *{name}* (per serving of {servings}):\n"
        f"• Calories: {round(n.calories)} kcal\n"
        f"• Protein: {n.protein_g}g\n"
        f"• Carbs: {n.carbs_g}g\n"
        f"• Fat: {n.fat_g}g\n"
        f"• Fiber: {n.fiber_g}g"
    )


def _handle_summary(day: str) -> str:
    conn = get_conn()
    totals = conn.execute(
        "SELECT COALESCE(SUM(calories),0) cal, COALESCE(SUM(protein),0) p, "
        "COALESCE(SUM(carbs),0) c, COALESCE(SUM(fat),0) f FROM meals WHERE date=?", (day,)
    ).fetchone()
    burned = conn.execute(
        "SELECT COALESCE(SUM(calories_burned),0) FROM activity WHERE date=?", (day,)
    ).fetchone()[0]
    conn.close()
    profile = _get_profile()
    goal = profile.get("daily_calorie_goal", config.DEFAULT_CALORIE_GOAL)
    cal = round(totals["cal"])
    remaining = max(goal - cal, 0)
    return (
        f"📅 *Today's Summary ({day})*\n"
        f"🍽 Calories in: {cal} / {goal} kcal\n"
        f"🔥 Calories burned: {round(burned)} kcal\n"
        f"⚖️ Net: {cal - round(burned)} kcal\n"
        f"💪 Protein: {round(totals['p'])}g | Carbs: {round(totals['c'])}g | Fat: {round(totals['f'])}g\n"
        f"{'✅ On track!' if cal <= goal else '⚠️ Over goal!'} {remaining} kcal remaining."
    )


@router.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    form = await request.form()
    body = form.get("Body", "").strip()
    sender = form.get("From", config.USER_WHATSAPP)
    day = _today()

    try:
        intent_data = parse_whatsapp_intent(body)
        intent = intent_data.get("intent", "UNKNOWN")

        if intent == "LOG_MEAL":
            reply = _handle_log_meal(intent_data, day)
        elif intent == "LOG_ACTIVITY":
            reply = _handle_log_activity(intent_data, day)
        elif intent == "RECIPE_CALC":
            reply = _handle_recipe(intent_data)
        elif intent == "SUMMARY":
            reply = _handle_summary(day)
        else:
            reply = (
                "👋 CalorIQ here! I can help you:\n"
                "• Log meals: 'had 2 rotis and dal for lunch'\n"
                "• Log activity: 'walked 8000 steps'\n"
                "• Analyze recipes: 'recipe: palak paneer - 200g paneer...'\n"
                "• Get summary: 'how am I doing today?'"
            )
    except Exception as e:
        reply = f"Sorry, I had trouble understanding that. ({str(e)[:80]})"

    # Respond via TwiML
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response><Message>{reply}</Message></Response>"""
    return Response(content=twiml, media_type="application/xml")
