import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
OPENROUTER_KEY = os.environ["OPENROUTER_KEY"]
ALLOWED_USER_ID = 133213

conversation_history = []

SYSTEM_PROMPT = "Ты переводчик между русским и китайским языками. Если пользователь пишет на русском — переводи на китайский. Если пишет на китайском — переводи на русский. Используй разговорную речь, живые и естественные выражения, не канцелярский стиль. Отвечай только переводом, без лишних пояснений."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("Доступ запрещён.")
        return

    user_message = update.message.text
    await update.message.chat.send_action("typing")

    conversation_history.append({"role": "user", "content": user_message})

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "anthropic/claude-3.5-haiku",
            "system": SYSTEM_PROMPT,
            "messages": conversation_history,
        },
    )

    reply = response.json()["choices"][0]["message"]["content"]
    conversation_history.append({"role": "assistant", "content": reply})

    await update.message.reply_text(reply)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
