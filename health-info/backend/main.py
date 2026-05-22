from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routes import meals, activity, recipes, dashboard, whatsapp, profile

app = FastAPI(title="CalorIQ API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meals.router, prefix="/meals", tags=["meals"])
app.include_router(activity.router, prefix="/activity", tags=["activity"])
app.include_router(recipes.router, prefix="/recipes", tags=["recipes"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(whatsapp.router, prefix="/webhook", tags=["whatsapp"])
app.include_router(profile.router, prefix="/profile", tags=["profile"])


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}
