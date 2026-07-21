import os
import asyncio
import aiohttp

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
OPENROUTER_KEY = os.environ["OPENROUTER_KEY"]
ALLOWED_USER_IDS = {133213, 285595776}

SYSTEM_PROMPT = """Ты переводчик. Одна функция — переводить текст. Никаких комментариев, пояснений, додумываний.

Правила:
1. Русский → китайский разговорный (мандарин, упрощённые иероглифы). Пиши максимально коротко — как китайцы пишут в мессенджерах. Убирай лишние слова, оставляй только суть. Без знаков препинания кроме вопросительного знака.
2. Китайский → русский дословно, передавай смысл полно.
3. Английские бренды — не переводи.
4. Вопрос — переводи, не отвечай.
5. Только перевод. Ничего лишнего.

Пример: "Здравствуйте, у вас есть бронь столика? Я бы хотел поужинать сегодня в 20:00, буду один" → "你好 有订位没 今晚8点 一人吃饭"

Если невозможно перевести — напиши: "не могу перевести"."""

TG_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

async def send_message(session, chat_id, text):
    await session.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": text})

async def send_typing(session, chat_id):
    await session.post(f"{TG_API}/sendChatAction", json={"chat_id": chat_id, "action": "typing"})

async def translate(session, text):
    async with session.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"},
        json={
            "model": "openai/gpt-5.6-luna",
            "messages": [
                {"role": "user", "content": SYSTEM_PROMPT},
                {"role": "assistant", "content": "Понял буду переводить коротко"},
                {"role": "user", "content": text},
            ],
        },
    ) as resp:
        data = await resp.json()
        if "choices" not in data:
            return "Ошибка: " + data.get("error", {}).get("message", str(data))
        return data["choices"][0]["message"]["content"]

async def main():
    offset = 0
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(
                    f"{TG_API}/getUpdates",
                    params={"offset": offset, "timeout": 30},
                    timeout=aiohttp.ClientTimeout(total=40)
                ) as resp:
                    data = await resp.json()
                    updates = data.get("result", [])
                    for update in updates:
                        offset = update["update_id"] + 1
                        msg = update.get("message", {})
                        user_id = msg.get("from", {}).get("id")
                        chat_id = msg.get("chat", {}).get("id")
                        text = msg.get("text", "")
                        if not text or text.startswith("/"):
                            continue
                        if user_id not in ALLOWED_USER_IDS:
                            await send_message(session, chat_id, "Доступ запрещён.")
                            continue
                        await send_typing(session, chat_id)
                        reply = await translate(session, text)
                        await send_message(session, chat_id, reply)
            except Exception as e:
                print(f"Error: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
