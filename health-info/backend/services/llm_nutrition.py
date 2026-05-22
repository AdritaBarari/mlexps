import json
import os
import re
from dotenv import load_dotenv
from groq import Groq
from models import NutritionResult
import config

_client = None


def _get_client():
    global _client
    if _client is None:
        # Reload env at client creation time in case dotenv ran before CWD was set
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
        api_key = os.getenv("GROQ_API_KEY") or config.GROQ_API_KEY
        _client = Groq(api_key=api_key)
    return _client


FOOD_PROMPT = """\
You are a precise nutrition database. Given the food and quantity below, return ONLY a valid JSON object with these exact keys (no markdown, no extra text):
{{
  "food_name": "<cleaned food name>",
  "calories": <number>,
  "protein_g": <number>,
  "carbs_g": <number>,
  "fat_g": <number>,
  "fiber_g": <number>,
  "sugar_g": <number>
}}

Use typical cooked values per the given quantity. Be accurate.
Food: {food}
Quantity: {quantity}"""


RECIPE_PROMPT = """\
You are a nutrition expert. Analyze this recipe and return ONLY a valid JSON object (no markdown):
{{
  "food_name": "<recipe name>",
  "calories": <total calories for all servings>,
  "protein_g": <total protein grams>,
  "carbs_g": <total carbs grams>,
  "fat_g": <total fat grams>,
  "fiber_g": <total fiber grams>,
  "sugar_g": <total sugar grams>
}}

Recipe ({servings} servings):
{ingredients}"""


def _call_llm(prompt: str) -> str:
    client = _get_client()
    response = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=256,
    )
    return response.choices[0].message.content.strip()


def _parse_json(text: str) -> dict:
    # Strip markdown code fences if present
    text = re.sub(r"```(?:json)?", "", text).strip("` \n")
    return json.loads(text)


def estimate_food_nutrition(food: str, quantity: str = "1 serving") -> NutritionResult:
    prompt = FOOD_PROMPT.format(food=food, quantity=quantity)
    raw = _call_llm(prompt)
    data = _parse_json(raw)
    return NutritionResult(
        food_name=data.get("food_name", food),
        calories=float(data.get("calories", 0)),
        protein_g=float(data.get("protein_g", 0)),
        carbs_g=float(data.get("carbs_g", 0)),
        fat_g=float(data.get("fat_g", 0)),
        fiber_g=float(data.get("fiber_g", 0)),
        sugar_g=float(data.get("sugar_g", 0)),
    )


def estimate_recipe_nutrition(ingredients: str, servings: int = 1) -> NutritionResult:
    prompt = RECIPE_PROMPT.format(ingredients=ingredients, servings=servings)
    raw = _call_llm(prompt)
    data = _parse_json(raw)
    total_cal = float(data.get("calories", 0))
    total_protein = float(data.get("protein_g", 0))
    total_carbs = float(data.get("carbs_g", 0))
    total_fat = float(data.get("fat_g", 0))
    total_fiber = float(data.get("fiber_g", 0))
    total_sugar = float(data.get("sugar_g", 0))
    s = max(servings, 1)
    return NutritionResult(
        food_name=data.get("food_name", "Recipe"),
        calories=round(total_cal / s, 1),
        protein_g=round(total_protein / s, 1),
        carbs_g=round(total_carbs / s, 1),
        fat_g=round(total_fat / s, 1),
        fiber_g=round(total_fiber / s, 1),
        sugar_g=round(total_sugar / s, 1),
    )


INTENT_PROMPT = """\
Classify the intent of this WhatsApp message and extract structured data.
Return ONLY a JSON object with no markdown:

For LOG_MEAL:
{{"intent": "LOG_MEAL", "meal_type": "<breakfast|lunch|dinner|snack|meal>", "items": [{{"food": "<food name>", "quantity": "<quantity>"}}]}}

For LOG_ACTIVITY:
{{"intent": "LOG_ACTIVITY", "activity_type": "<steps|walk|run|gym|cycling|other>", "steps": <int or 0>, "duration_minutes": <int or 0>}}

For RECIPE_CALC:
{{"intent": "RECIPE_CALC", "name": "<recipe name>", "ingredients": "<raw ingredients text>", "servings": <int>}}

For SUMMARY:
{{"intent": "SUMMARY"}}

For UNKNOWN:
{{"intent": "UNKNOWN"}}

Message: {message}"""


def parse_whatsapp_intent(message: str) -> dict:
    prompt = INTENT_PROMPT.format(message=message)
    raw = _call_llm(prompt)
    return _parse_json(raw)
