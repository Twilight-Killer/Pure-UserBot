import asyncio
import html
import re
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from time import perf_counter
from traceback import print_exc

from pyrogram import Client, enums, filters
from pyrogram.types import Message

from utils.db import db
from utils.filters import command
from utils.misc import modules_help
from utils.scripts import paste_neko, shell_exec


async def aexec(code, *args, timeout=None):
    exec(
        "async def __todo(client, message, *args):\n"
        + " from pyrogram import raw, types, enums\n"
        + " from utils.db import db\n"
        + " app = client\n"
        + " m = message\n"
        + " r = m.reply_to_message\n"
        + " u = m.from_user\n"
        + " ru = getattr(r, 'from_user', None)\n"
        + " p = print\n"
        + " here = m.chat.id\n"
        + "".join(f"\n {_l}" for _l in code.split("\n"))
    )

    f = StringIO()
    with redirect_stdout(f):
        await asyncio.wait_for(locals()["__todo"](*args), timeout=timeout)

    return f.getvalue()


code_result = (
    "<b><emoji id={emoji_id}>🌐</emoji> ЯП:</b>\n"
    "<code>{language}</code>\n\n"
    "<b><emoji id=5431376038628171216>💻</emoji> Код:</b>\n"
    '<pre language="{pre_language}">{code}</pre>\n\n'
    "{result}"
)


@Client.on_message(~filters.scheduled & command(["py", "rpy"]) & filters.me & ~filters.forwarded)
async def python_exec(client: Client, message: Message):
    if len(message.command) == 1 and message.command[0] != "rpy":
        return await message.edit_text("<b>Code to execute isn't provided</b>")

    if message.command[0] == "rpy":
        if not message.reply_to_message:
            return await message.edit_text("<b>Вы не ввели код.</b>")

        # Check if message is a reply to message with already executed code
        for entity in message.reply_to_message.entities:
            if entity.type == enums.MessageEntityType.PRE and entity.language == "python":
                code = message.reply_to_message.text[entity.offset : entity.offset + entity.length]
                break
        else:
            code = message.reply_to_message.text
    else:
        code = message.text.split(maxsplit=1)[1]

    await message.edit_text("<b><emoji id=5821116867309210830>🔃</emoji> Выполняю...</b>")

    try:
        code = code.replace("\u00A0", "")

        start_time = perf_counter()
        result = await aexec(code, client, message, timeout=db.get("shell", "timeout", 3600))
        stop_time = perf_counter()

        result = result.replace(client.me.phone_number, "88804818110")

        if not result:
            result = "No result"
        elif len(result) > 3072:
            paste_result = html.escape(await paste_neko(result))

            if paste_result == "Pasting failed":
                with open("error.log", "w") as file:
                    file.write(result)

                result = None
            else:
                result = paste_result

        elif re.match(r"^(https?):\/\/[^\s\/$.?#].[^\s]*$", result):
            result = html.escape(result)
        else:
            result = f"<pre>{html.escape(result)}</pre>"

        if result:
            return await message.edit_text(
                code_result.format(
                    emoji_id=5260480440971570446,
                    language="Python",
                    pre_language="python",
                    code=html.escape(code),
                    result=f"<b><emoji id=5472164874886846699>✨</emoji> Результат</b>:\n"
                    f"{result}\n"
                    f"<b>Выполнено за {round(stop_time - start_time, 5)}с.</b>",
                ),
                disable_web_page_preview=True,
            )
        else:
            return await message.reply_document(
                document="error.log",
                caption=code_result.format(
                    emoji_id=5260480440971570446,
                    language="Python",
                    pre_language="python",
                    code=html.escape(code),
                    result=f"<b><emoji id=5472164874886846699>✨</emoji> Результат слишком длинный</b>\n"
                    f"<b>Выполнено за {round(stop_time - start_time, 5)}с.</b>",
                ),
            )
    except asyncio.TimeoutError:
        return await message.edit_text(
            code_result.format(
                emoji_id=5260480440971570446,
                language="Python",
                pre_language="python",
                code=html.escape(code),
                result="<b><emoji id=5465665476971471368>❌</emoji> Время ожидания истекло!</b>",
            ),
            disable_web_page_preview=True,
        )
    except Exception as e:
        err = StringIO()
        with redirect_stderr(err):
            print_exc()

        return await message.edit_text(
            code_result.format(
                emoji_id=5260480440971570446,
                language="Python",
                pre_language="python",
                code=html.escape(code),
                result=f"<b><emoji id=5465665476971471368>❌</emoji> {e.__class__.__name__}: {e}</b>\n"
                f"Трейсбэк: {html.escape(await paste_neko(err.getvalue()))}",
            ),
            disable_web_page_preview=True,
        )


@Client.on_message(~filters.scheduled & command(["go", "rgo"]) & filters.me & ~filters.forwarded)
async def go_exec(_: Client, message: Message):
    if len(message.command) == 1 and message.command[0] != "rgo":
        return await message.edit_text("<b>Вы не ввели код.</b>")

    if message.command[0] == "rgo":
        code = message.reply_to_message.text
    else:
        code = message.text.split(maxsplit=1)[1]

    await message.edit_text("<b><emoji id=5821116867309210830>🔃</emoji> Выполняется...</b>")

    with tempfile.TemporaryDirectory() as tempdir:
        with tempfile.NamedTemporaryFile("w+", suffix=".go", dir=tempdir) as file:
            file.write(code)
            file.seek(0)

            timeout = db.get("shell", "timeout", 3600)
            try:
                exec_start_time = perf_counter()
                rcode, stdout, stderr = await shell_exec(
                    command=f"go run {file.name}",
                    executable=db.get("shell", "executable"),
                    timeout=timeout,
                )
                exec_stop_time = perf_counter()
            except asyncio.exceptions.TimeoutError:
                return await message.edit_text(
                    code_result.format(
                        emoji_id=5258117049317603088,
                        language="Go",
                        pre_language="go",
                        code=html.escape(code),
                        result=f"<b><emoji id=5465665476971471368>❌</emoji>Ошибка!</b>\n<b>Время выполнения превысило {timeout}с.</b>",
                    ),
                    disable_web_page_preview=True,
                )
            else:
                if stderr:
                    return await message.edit_text(
                        code_result.format(
                            emoji_id=5258117049317603088,
                            language="Go",
                            pre_language="go",
                            code=html.escape(code),
                            result=f"<b><emoji id=5465665476971471368>❌</emoji> Выбросило ошибку {rcode}:</b>\n"
                            f"<code>{html.escape(stderr)}</code>",
                        ),
                        disable_web_page_preview=True,
                    )

                if len(stdout) > 3072:
                    result = html.escape(await paste_neko(stdout))
                else:
                    result = f"<pre>{html.escape(result)}</pre>"

                return await message.edit_text(
                    code_result.format(
                        emoji_id=5258117049317603088,
                        language="Go",
                        pre_language="go",
                        code=html.escape(code),
                        result=f"<b><emoji id=5472164874886846699>✨</emoji> Результат</b>:\n"
                        f"{result}\n\n"
                        f"<b>Выполнено за {round(exec_stop_time - exec_start_time, 5)}с.</b>",
                    ),
                    disable_web_page_preview=True,
                )


module = modules_help.add_module("code_runner", __file__)
module.add_command("py", "Execute Python code", "[code]")
module.add_command("rpy", "Execute Python code from reply")
module.add_command("go", "Execute Go code", "[code]")
module.add_command("rgo", "Execute Go code from reply")
