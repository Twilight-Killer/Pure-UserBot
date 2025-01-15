import openai
from pyrogram import Client, enums, filters
from pyrogram.types import Message

from utils.db import db
from utils.filters import command
from utils.misc import modules_help
from utils.scripts import get_args_raw, with_args

@Client.on_message(command(["nudes"]) & ~filters.forwarded & ~filters.scheduled)
async def chatpgt_nudes(_: Client, message: Message):
    args = get_args_raw(message, use_reply=True)

    api_key = db.get("ChatGPT", "api_key")
    if not api_key:
        return await message.reply(
            "<emoji id=5260342697075416641>❌</emoji><b> Вы не установили API ключ от OpenAI</b>",
            quote=True,
        )

    data: dict = db.get(
        "ChatGPT",
        f"gpt_id{message.chat.id}",
        {
            "enabled": True,
            "gpt_messages": [],
        },
    )

    if not data.get("enabled"):
        return await message.reply(
            "<emoji id=5260342697075416641>❌</emoji><b> ChatGPT пока недоступен</b>",
            quote=True,
        )

    data["enabled"] = False
    db.set("ChatGPT", f"gpt_id{message.chat.id}", data)

    msg = await message.reply(
        "<emoji id=5443038326535759644>💬</emoji><b> Генерирую твой запрос...</b>",
        quote=True,
    )

    client = openai.AsyncOpenAI(api_key=api_key)

    # Создаем кастомный промт
    custom_prompt = f"Extract the title, description (without price and contact), price, and contact information from the following text. Format as a JSON object:\n{args}"

    try:
        # Отправляем кастомный запрос к ChatGPT
        completion = await client.chat.completions.create(
            messages=[{"role": "user", "content": custom_prompt}],
            model="gpt-4o"
        )
    except openai.RateLimitError:
        data["enabled"] = True
        db.set("ChatGPT", f"gpt_id{message.chat.id}", data)
        return await msg.edit_text(
            "<emoji id=5260342697075416641>❌</emoji><b> Модель перегружена другими запросами.</b>"
        )
    except Exception as e:
        data["enabled"] = True
        db.set("ChatGPT", f"gpt_id{message.chat.id}", data)
        return await msg.edit_text(
            f"<emoji id=5260342697075416641>❌</emoji><b> Выбросило ошибку: {e}</b>"
        )

    response = completion.choices[0].message.content
    await msg.edit_text(
        f"{response}",
        parse_mode=enums.ParseMode.MARKDOWN
    )
@Client.on_message(command(["gpt", "rgpt"]) & ~filters.forwarded & ~filters.scheduled)
async def chatpgt(_: Client, message: Message):
    if message.command[0] == "rgpt":
        args = get_args_raw(message, use_reply=True)
    else:
        args = get_args_raw(message)

    if not args:
        return await message.reply(
            "<emoji id=5260342697075416641>❌</emoji><b> Вы не ввели запрос</b>",
            quote=True,
        )

    api_key = db.get("ChatGPT", "api_key")
    if not api_key:
        return await message.reply(
            "<emoji id=5260342697075416641>❌</emoji><b> Вы не установили API ключ от OpenAI</b>",
            quote=True,
        )

    data: dict = db.get(
        "ChatGPT",
        f"gpt_id{message.chat.id}",
        {
            "enabled": True,
            "gpt_messages": [],
        },
    )

    if not data.get("enabled"):
        return await message.reply(
            "<emoji id=5260342697075416641>❌</emoji><b> ChatGPT пока недоступен</b>",
            quote=True,
        )

    data["enabled"] = False
    db.set("ChatGPT", f"gpt_id{message.chat.id}", data)

    msg = await message.reply(
        "<emoji id=5443038326535759644>💬</emoji><b> ChatGPT генерирует ответ...</b>",
        quote=True,
    )

    client = openai.AsyncOpenAI(api_key=api_key)

    try:
        completion = await client.chat.completions.create(
            messages=data["gpt_messages"] + [{"role": "user", "content": args}],
            model="gpt-4o"
        )
    except openai.RateLimitError:
        data["enabled"] = True
        db.set("ChatGPT", f"gpt_id{message.chat.id}", data)
        return await msg.edit_text(
            "<emoji id=5260342697075416641>❌</emoji><b> Модель перегружена другими запросами.</b>"
        )
    except Exception as e:
        data["enabled"] = True
        db.set("ChatGPT", f"gpt_id{message.chat.id}", data)
        return await msg.edit_text(
            f"<emoji id=5260342697075416641>❌</emoji><b> Выбросило ошибку: {e}</b>"
        )

    response = completion.choices[0].message.content

    data["gpt_messages"].append({"role": "user", "content": args})
    data["gpt_messages"].append({"role": completion.choices[0].message.role, "content": response})
    data["enabled"] = True
    db.set("ChatGPT", f"gpt_id{message.chat.id}", data)

    await msg.edit_text(response, parse_mode=enums.ParseMode.MARKDOWN)


@Client.on_message(command(["gptst"]) & filters.me & ~filters.forwarded & ~filters.scheduled)
@with_args("<emoji id=5260342697075416641>❌</emoji><b> Вы не ввели API ключ</b>")
async def chatpgt_set_key(_: Client, message: Message):
    args = get_args_raw(message)

    db.set("ChatGPT", "api_key", args)
    await message.edit_text(
        "<emoji id=5260726538302660868>✅</emoji><b>Вы установили API ключ</b>"
    )


@Client.on_message(command(["gptcl"]) & filters.me & ~filters.forwarded & ~filters.scheduled)
async def chatpgt_clear(_: Client, message: Message):
    db.remove("ChatGPT", f"gpt_id{message.chat.id}")

    await message.edit_text(
        "<emoji id=5258130763148172425>✅</emoji><b> Вы очистили контекст</b>"
    )


module = modules_help.add_module("chatgpt", __file__)
module.add_command("gpt", "Спросить у ChatGPT", "[query]")
module.add_command("rgpt", "Спросить у ChatGPT с отвеченного сообщения", "[reply]")
module.add_command("gptst", "Установить API ключ")
module.add_command("gptcl", "Очистить контекст")
