import config

_twilio_client = None


def _get_twilio():
    global _twilio_client
    if _twilio_client is None and config.TWILIO_ACCOUNT_SID and config.TWILIO_AUTH_TOKEN:
        from twilio.rest import Client
        _twilio_client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
    return _twilio_client


def send_whatsapp(to: str, body: str):
    if not to:
        return
    client = _get_twilio()
    if client is None:
        print(f"[WhatsApp STUB] To: {to} | {body}")
        return
    to_number = to if to.startswith("whatsapp:") else f"whatsapp:{to}"
    client.messages.create(
        from_=config.TWILIO_WHATSAPP_FROM,
        to=to_number,
        body=body,
    )


def maybe_send_calorie_alert(total_calories: float, goal: int, whatsapp_number: str):
    if not whatsapp_number or not goal:
        return
    pct = total_calories / goal
    if pct >= config.CALORIE_EXCEED_THRESHOLD:
        over = round(total_calories - goal)
        send_whatsapp(
            whatsapp_number,
            f"🚨 You've exceeded your calorie goal by {over} kcal today!\n"
            f"Total: {round(total_calories)} / {goal} kcal\n"
            f"Consider a light dinner or a walk.",
        )
    elif pct >= config.CALORIE_WARN_THRESHOLD:
        remaining = round(goal - total_calories)
        send_whatsapp(
            whatsapp_number,
            f"⚠️ You're at {round(pct * 100)}% of your daily calorie goal.\n"
            f"Only {remaining} kcal remaining for today.",
        )
