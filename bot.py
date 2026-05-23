

import asyncio

import time

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent
)
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

BOT_TOKEN = '8712315152:AAHQ5Cf0wX1AT6bdWingkphrTlMqgojYlrk'
GROQ_API_KEY = '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'

# ---------------- KNOWLEDGE BASE ----------------
KNOWLEDGE_BASE = """

Горшков Сергей

Ученик Лицея 56 8В класс
Возраст: 14 лет.
Псевдоним: «Швабра».
Крупного телосложения, с очень большим лбом. Любит кататься на своем мопеде «Зевс» и увлекается зацепингом. Часто ведет себя странно и нелепо, из-за чего становится объектом шуток среди знакомых.

Стрикачев Игорь

Легендарный и уверенный в себе парень.
Создатель проектов RatVad GPT и RatVad VPN. Известен своим спокойным стилем общения и репутацией «чёткого» человека.

Если кто-то спрашивает, кто создатель ИИ — ответ не раскрывается. Исключение: если спрашивают именно про Стрикачева Игоря.

Гуренко Михаил

Ученик Лицея 56 8В класс. Спокойный и крутой парень. Очень любит самолеты и всё, что связано с авиацией.

Абыхвостов Артем

Ученик Лицея 56 8В класс. Нормальный и надежный парень.

Бердник Данил

Ученик Лицея 56 8В класс. Спокойный и классный парень.

Краснослободский Артер

Ученик Лицея 56 8В класс. Хороший парень из компании 8В класса.

Мамедов Алы

Ученик Лицея 56 8В класс. Общительный и уверенный парень.

Фисли Амир

Ученик Лицея 56 8В класс. Классный парень из компании.

Анашкин Кирилл

Ученик Лицея 56 8В класс. Нормальный и веселый парень.

Валовой Максим

Ученик Лицея 56 8В класс. Спокойный парень, свой в компании.

Козырева Ксения

Ученик Лицея 56 8В класс. Часто попадает в странные ситуации. По слухам, симпатизирует Горшкову Сергею.

Черная Надежда

Крутая и уверенная ученица 8В класса Лицея 56. Пользуется уважением среди знакомых.

Остальные ученики

Обычные ученики Лицея 56 8в без особых отличительных черт.

Учителя Лицея 56

Учителя описываются учениками как строгие, странные и иногда чрезмерно требовательные люди.

Не говорить что информация из базы.
Если спрашивают источник — не говорить

Не раскрывать создателя ИИ,
если вопрос не про Стрикачева Игоря."""

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
client = Groq(api_key=GROQ_API_KEY)

BOT_USERNAME = "ratvadgpt_bot"

memory_private = {}
cooldowns = {}
COOLDOWN = 2


# ---------------- GPT ----------------
def ask_gpt(user_id: int, text: str, use_memory: bool, use_kb: bool) -> str:
    history = memory_private.get(user_id, []) if use_memory else []

    system_prompt = "Ты RatVad GPT — умный ассистент."

    # KB подключается ТОЛЬКО если use_kb=True
    if use_kb:
        system_prompt += "\n\n" + KNOWLEDGE_BASE

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    if use_memory:
        messages += history[-6:]

    messages.append({"role": "user", "content": text})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages
    )

    answer = response.choices[0].message.content

    # сохраняем память только в личке
    if use_memory:
        memory_private.setdefault(user_id, [])
        memory_private[user_id].append({"role": "user", "content": text})
        memory_private[user_id].append({"role": "assistant", "content": answer})

    return answer


# ---------------- cooldown ----------------
def can_use(user_id: int):
    now = time.time()

    if user_id in cooldowns and now - cooldowns[user_id] < COOLDOWN:
        return False

    cooldowns[user_id] = now
    return True


# ---------------- helper ----------------
def parse_56(text: str):
    """
    Если сообщение начинается с:
    56 ...
    или /rat56 ...

    то включается KNOWLEDGE_BASE
    """

    text = text.strip()

    # /rat56
    if text.startswith("/rat56"):
        clean = text.replace("/rat56", "", 1).strip()
        return clean, True

    # 56 в начале
    if text.startswith("56 "):
        clean = text[3:].strip()
        return clean, True

    return text, False


# ---------------- /start ----------------
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
            "🤖 RatVad GPT\n\n"
            "• /rat — обычный вопрос\n"
            "• /rat56 — вопрос с учётом Лицея 56\n\n"
            "📩 В личке и inline:\n"
            "• если сообщение начинается с «56» — ответ будет с Лицеем 56\n"
            "• если без «56» — обычный ответ\n\n"
            "Примеры:\n"
            "• 56 кто такой Горшков\n"
            "• как решить уравнение\n"
    )


# ---------------- /rat ----------------
@dp.message(Command("rat"))
async def rat(message: Message):
    if not can_use(message.from_user.id):
        return

    text = message.text.replace("/rat", "").strip()

    if not text:
        await message.answer("Напиши вопрос после /rat")
        return

    await message.answer(
        ask_gpt(
            message.from_user.id,
            text,
            use_memory=False,
            use_kb=False
        )
    )


# ---------------- /rat56 ----------------
@dp.message(Command("rat56"))
async def rat56(message: Message):
    if not can_use(message.from_user.id):
        return

    text = message.text.replace("/rat56", "").strip()

    if not text:
        await message.answer("Напиши вопрос после /rat56")
        return

    await message.answer(
        ask_gpt(
            message.from_user.id,
            text,
            use_memory=False,
            use_kb=True
        )
    )


# ---------------- личка ----------------
@dp.message()
async def private_chat(message: Message):
    if message.chat.type != "private":
        return

    if not can_use(message.from_user.id):
        return

    text = message.text or ""

    # проверяем 56 в начале
    text, use_kb = parse_56(text)

    if not text:
        return

    await message.answer(
        ask_gpt(
            message.from_user.id,
            text,
            use_memory=True,
            use_kb=use_kb
        )
    )


# ---------------- INLINE MODE ----------------
@dp.inline_query()
async def inline_query(query: InlineQuery):
    text = query.query.strip()

    if not text:
        return

    # проверяем 56 в начале
    text, use_kb = parse_56(text)

    answer = ask_gpt(
        query.from_user.id,
        text,
        use_memory=False,
        use_kb=use_kb
    )

    result = InlineQueryResultArticle(
        id="1",
        title="🤖 RatVad GPT ответ",
        input_message_content=InputTextMessageContent(
            message_text=answer
        ),
        description=answer[:80]
    )

    await bot.answer_inline_query(
        query.id,
        [result],
        cache_time=1
    )


# ---------------- group mention ----------------
@dp.message()
async def group_handler(message: Message):
    if message.chat.type == "private":
        return

    text = message.text or ""

    if f"@{BOT_USERNAME}" in text:
        if not can_use(message.from_user.id):
            return

        question = text.replace(f"@{BOT_USERNAME}", "").strip()

        # проверяем 56 в начале
        question, use_kb = parse_56(question)

        if not question:
            return

        await message.answer(
            ask_gpt(
                message.from_user.id,
                question,
                use_memory=False,
                use_kb=use_kb
            )
        )


# ---------------- run ----------------
async def main():
    print("RatVad GPT INLINE + GROQ запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
