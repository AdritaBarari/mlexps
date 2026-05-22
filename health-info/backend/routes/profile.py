from fastapi import APIRouter
from database import get_conn
from models import ProfileUpdate

router = APIRouter()


@router.get("")
def get_profile():
    conn = get_conn()
    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    conn.close()
    return dict(row)


@router.put("")
def update_profile(update: ProfileUpdate):
    fields = update.model_dump(exclude_none=True)
    if not fields:
        conn = get_conn()
        row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
        conn.close()
        return dict(row)

    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [1]
    conn = get_conn()
    conn.execute(f"UPDATE profile SET {set_clause} WHERE id = ?", values)
    conn.commit()
    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    conn.close()
    return dict(row)
