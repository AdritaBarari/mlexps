from datetime import date as _date
from fastapi import APIRouter, HTTPException
from database import get_conn
from models import ActivityCreate, ActivityResponse

router = APIRouter()

# MET-based calories-per-minute estimates keyed by activity type
_CALORIES_PER_STEP = 0.04  # ~0.04 kcal/step average


def _estimate_calories(activity_type: str, steps: int, duration_minutes: int) -> float:
    if steps and steps > 0:
        return round(steps * _CALORIES_PER_STEP, 1)
    met_map = {
        "walk": 3.5, "run": 8.0, "gym": 5.0,
        "cycling": 6.0, "swimming": 7.0, "yoga": 2.5, "other": 4.0,
    }
    met = met_map.get(activity_type.lower(), 4.0)
    weight_kg = 70  # default body weight assumption
    return round(met * weight_kg * (duration_minutes / 60), 1)


def _today() -> str:
    return _date.today().isoformat()


@router.post("", response_model=ActivityResponse)
def log_activity(act: ActivityCreate):
    day = act.date or _today()
    calories = act.calories_burned
    if calories is None:
        calories = _estimate_calories(act.activity_type, act.steps or 0, act.duration_minutes or 0)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO activity (date, activity_type, steps, duration_minutes, calories_burned)
           VALUES (?, ?, ?, ?, ?)""",
        (day, act.activity_type, act.steps or 0, act.duration_minutes or 0, calories),
    )
    act_id = cur.lastrowid
    conn.commit()
    row = conn.execute("SELECT * FROM activity WHERE id = ?", (act_id,)).fetchone()
    conn.close()
    return dict(row)


@router.get("/{day}", response_model=list[ActivityResponse])
def get_activity(day: str):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM activity WHERE date = ? ORDER BY logged_at", (day,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.delete("/{act_id}")
def delete_activity(act_id: int):
    conn = get_conn()
    result = conn.execute("DELETE FROM activity WHERE id = ?", (act_id,))
    conn.commit()
    conn.close()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Activity not found")
    return {"deleted": act_id}
