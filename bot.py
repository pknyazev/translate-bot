import os
import asyncio
import aiohttp

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
            "model": "google/gemini-2.5-flash",
            "messages": [
                {"role": "user", "content": SYSTEM_PROMPT},
                {"role": "assistant", "content": "Понял, буду переводить."},
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
                    for update in data.get("result", []):
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
    asyncio.run(main())                {"role": "assistant", "content": "Понял, буду переводить."},
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
                async with session.get(f"{TG_API}/getUpdates", params={"offset": offset, "timeout": 30}) as resp:
                    data = await resp.json()
                    for update in data.get("result", []):
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
