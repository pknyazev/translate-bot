import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
OPENROUTER_KEY = os.environ["OPENROUTER_KEY"]
ALLOWED_USER_ID = 133213

SYSTEM_PROMPT = """Ты переводчик. Следуй правилам строго:

1. Если сообщение на русском языке — переведи его на китайский разговорный (мандарин, упрощённые иероглифы). Используй живую разговорную речь, как говорят в обычной жизни, не официальный стиль.

2. Если сообщение на китайском языке — переведи его дословно на русский.

Отвечай ТОЛЬКО переводом. Никаких пояснений, никаких вступлений, только сам перевод."""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("Доступ запрещён.")
        return

    user_message = update.message.text
    await update.message.chat.send_action("typing")

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "anthropic/claude-3.5-haiku",
            "messages": [
                {"role": "user", "content": SYSTEM_PROMPT},
                {"role": "assistant", "content": "Понял, буду переводить."},
                {"role": "user", "content": user_message},
            ],
        },
    )

    reply = response.json()["choices"][0]["message"]["content"]
    await update.message.reply_text(reply)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
