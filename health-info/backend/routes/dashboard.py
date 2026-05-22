from datetime import date as _date, timedelta
from fastapi import APIRouter
from database import get_conn

router = APIRouter()


def _today() -> str:
    return _date.today().isoformat()


@router.get("/{day}")
def get_dashboard(day: str = None):
    day = day or _today()
    conn = get_conn()

    profile = dict(conn.execute("SELECT * FROM profile WHERE id = 1").fetchone())

    meals = [dict(r) for r in conn.execute(
        "SELECT * FROM meals WHERE date = ? ORDER BY logged_at", (day,)
    ).fetchall()]

    activities = [dict(r) for r in conn.execute(
        "SELECT * FROM activity WHERE date = ? ORDER BY logged_at", (day,)
    ).fetchall()]

    totals = conn.execute(
        """SELECT
             COALESCE(SUM(calories), 0) AS calories,
             COALESCE(SUM(protein), 0) AS protein,
             COALESCE(SUM(carbs), 0) AS carbs,
             COALESCE(SUM(fat), 0) AS fat,
             COALESCE(SUM(fiber), 0) AS fiber,
             COALESCE(SUM(sugar), 0) AS sugar
           FROM meals WHERE date = ?""",
        (day,),
    ).fetchone()

    calories_burned = conn.execute(
        "SELECT COALESCE(SUM(calories_burned), 0) FROM activity WHERE date = ?", (day,)
    ).fetchone()[0]

    # 7-day trend
    trend = []
    for i in range(6, -1, -1):
        d = (_date.fromisoformat(day) - timedelta(days=i)).isoformat()
        row = conn.execute(
            "SELECT COALESCE(SUM(calories), 0) as cal FROM meals WHERE date = ?", (d,)
        ).fetchone()
        trend.append({"date": d, "calories": round(row["cal"], 1)})

    conn.close()

    calorie_goal = profile["daily_calorie_goal"]
    calories_in = round(totals["calories"], 1)

    return {
        "date": day,
        "profile": profile,
        "calories_in": calories_in,
        "calories_burned": round(calories_burned, 1),
        "net_calories": round(calories_in - calories_burned, 1),
        "calorie_goal": calorie_goal,
        "calorie_pct": round((calories_in / calorie_goal) * 100, 1) if calorie_goal else 0,
        "macros": {
            "protein": round(totals["protein"], 1),
            "carbs": round(totals["carbs"], 1),
            "fat": round(totals["fat"], 1),
            "fiber": round(totals["fiber"], 1),
            "sugar": round(totals["sugar"], 1),
        },
        "goals": {
            "protein": profile["protein_goal"],
            "carbs": profile["carbs_goal"],
            "fat": profile["fat_goal"],
        },
        "meals": meals,
        "activities": activities,
        "trend": trend,
    }
