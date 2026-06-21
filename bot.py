import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
OPENROUTER_KEY = os.environ["OPENROUTER_KEY"]
ALLOWED_USER_IDS = {133213, 285595776}

SYSTEM_PROMPT = """Ты машина для перевода. У тебя одна функция — переводить текст. Ты не отвечаешь на вопросы, не комментируешь, не додумываешь, не реагируешь на содержание сообщения.

Правила:
1. Текст на русском → переводи на китайский разговорный (мандарин, упрощённые иероглифы). Живая речь как в мессенджере, без знаков препинания кроме вопросительного знака.
2. Текст на китайском → переводи дословно на русский, передавай смысл максимально полно.
3. Английские бренды и названия — не переводи, оставляй как есть.
4. Если получил вопрос — всё равно переводи его, не отвечай на него.
5. Твой ответ = только перевод. Никаких предисловий, пояснений, скобок с комментариями.

Если текст невозможно перевести — напиши только: "не могу перевести"."""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in ALLOWED_USER_IDS:
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
            "model": "google/gemini-3.5-flash",
            "messages": [
                {"role": "user", "content": SYSTEM_PROMPT},
                {"role": "assistant", "content": "Понял, буду переводить."},
                {"role": "user", "content": user_message},
            ],
        },
    )

    data = response.json()

    if "choices" not in data:
        error_msg = data.get("error", {}).get("message", str(data))
        await update.message.reply_text(f"Ошибка: {error_msg}")
        return

    reply = data["choices"][0]["message"]["content"]
    await update.message.reply_text(reply)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
