from pydantic import BaseModel
from typing import Optional


class MealCreate(BaseModel):
    food_name: str
    meal_type: Optional[str] = "meal"
    quantity: Optional[str] = "1 serving"
    date: Optional[str] = None  # defaults to today if omitted


class MealResponse(BaseModel):
    id: int
    date: str
    meal_type: str
    food_name: str
    quantity: Optional[str]
    calories: float
    protein: float
    carbs: float
    fat: float
    fiber: float
    sugar: float
    logged_at: str


class ActivityCreate(BaseModel):
    activity_type: str
    steps: Optional[int] = 0
    duration_minutes: Optional[int] = 0
    calories_burned: Optional[float] = None  # auto-estimated if None
    date: Optional[str] = None


class ActivityResponse(BaseModel):
    id: int
    date: str
    activity_type: str
    steps: int
    duration_minutes: int
    calories_burned: float
    logged_at: str


class RecipeAnalyzeRequest(BaseModel):
    name: Optional[str] = "My Recipe"
    ingredients_raw: str
    servings: Optional[int] = 1
    save: Optional[bool] = False


class RecipeResponse(BaseModel):
    name: str
    servings: int
    calories_per_serving: float
    protein: float
    carbs: float
    fat: float
    ingredients_raw: str


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    daily_calorie_goal: Optional[int] = None
    protein_goal: Optional[int] = None
    carbs_goal: Optional[int] = None
    fat_goal: Optional[int] = None
    whatsapp_number: Optional[str] = None


class NutritionResult(BaseModel):
    food_name: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    sugar_g: float
