import os
import subprocess
import sys
from time import perf_counter

import arrow
import git
import pyrogram
from pyrogram import Client, filters
from pyrogram.types import Message

from utils.db import db
from utils.filters import command
from utils.misc import bot_uptime, modules_help
from utils.scripts import (
    format_exc,
    get_args,
    get_cpu_usage,
    get_prefix,
    get_ram_usage,
    restart,
    shell_exec,
    with_args,
)


@Client.on_message(~filters.scheduled & command(["help", "h"]) & filters.me & ~filters.forwarded)
async def help_cmd(_, message: Message):
    args, _ = get_args(message)
    try:
        if not args:
            msg_edited = False

            for text in modules_help.help():
                if msg_edited:
                    await message.reply(text, disable_web_page_preview=True)
                else:
                    await message.edit(text, disable_web_page_preview=True)
                    msg_edited = True
        elif args[0] in modules_help.modules:
            await message.edit(modules_help.module_help(args[0]), disable_web_page_preview=True)
        else:
            await message.edit(modules_help.command_help(args[0]), disable_web_page_preview=True)
    except ValueError as e:
        await message.edit(e)


@Client.on_message(~filters.scheduled & command(["restart"]) & filters.me & ~filters.forwarded)
async def _restart(_: Client, message: Message):
    db.set(
        "core.updater",
        "restart_info",
        {
            "chat_id": message.chat.id,
            "message_id": message.id,
            "time": perf_counter(),
            "type": "restart",
        },
    )
    await message.edit("<code>Перезагружаюсь...</code>")
    restart()


@Client.on_message(~filters.scheduled & command(["update"]) & filters.me & ~filters.forwarded)
async def _update(_: Client, message: Message):
    await message.edit("<code>Обновляюсь...</code>")
    args, nargs = get_args(message)

    current_hash = git.Repo().head.commit.hexsha

    git.Repo().remote("origin").fetch()

    branch = git.Repo().active_branch.name
    upcoming = next(git.Repo().iter_commits(f"origin/{branch}", max_count=1)).hexsha

    if current_hash == upcoming:
        return await message.edit("<b>Юзер-бот уже обновлен до актуальной версии</b>")

    if "--hard" in args:
        await shell_exec("git reset --hard HEAD")

    try:
        git.Repo().remote("origin").pull()
    except git.exc.GitCommandError as e:
        return await message.edit_text(
            "<b>Ошибка обнволения! Попробуйте с аргументом --hard.</b>\n\n"
            f"<code>{e.stderr.strip()}</code>"
        )

    upcoming_version = len(list(git.Repo().iter_commits()))
    current_version = upcoming_version - (
        len(list(git.Repo().iter_commits(f"{current_hash}..{upcoming}")))
    )

    db.set(
        "core.updater",
        "restart_info",
        {
            "chat_id": message.chat.id,
            "message_id": message.id,
            "time": perf_counter(),
            "hash": current_hash,
            "version": f"{current_version}",
            "type": "update",
        },
    )

    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-U", "pip"])
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-U",
                "-r",
                "requirements.txt",
            ]
        )
    except Exception as e:
        await message.edit(format_exc(e))
        db.remove("core.updater", "restart_info")
    else:
        restart()


@Client.on_message(
    ~filters.scheduled & command(["kprefix", "prefix"]) & filters.me & ~filters.forwarded
)
async def set_prefix(_, message: Message):
    args, _ = get_args(message)
    prefix = get_prefix()

    if not args:
        return await message.edit_text(
            f"Текущий префикс: <code>{prefix}</code>\n"
            f"Для изменения префикса на другой используйте: <code>{prefix}{message.command[0]} [новый префикс]</code>"
        )

    _prefix = args[0]
    db.set("core.main", "prefix", _prefix)
    await message.edit(f"<b>Префикс изменён на:</b> <code>{_prefix}</code>")


@Client.on_message(
    ~filters.scheduled & command(["sendmod", "sm"]) & filters.me & ~filters.forwarded
)
@with_args("<b>Module name to send is not provided</b>")
async def sendmod(client: Client, message: Message):
    args, _ = get_args(message)
    try:
        module_name = args[0]
        if module_name in modules_help.modules:
            await message.delete()
            text = modules_help.module_help(module_name, False)
            if os.path.isfile(modules_help.modules[module_name].path):
                await client.send_document(
                    message.chat.id,
                    modules_help.modules[module_name].path,
                    caption=text,
                )
        else:
            await message.edit(f"<b>Модуль {module_name} не найден!</b>")
    except Exception as e:
        await message.reply(format_exc(e), quote=False)


@Client.on_message(~filters.scheduled & command(["status"]) & filters.me & ~filters.forwarded)
async def _status(_, message: Message):
    common_args, _ = get_args(message)

    await message.edit("<code>Getting info...</code>")

    prefix = get_prefix()
    repo_link = "https://github.com/PureAholy/Pure-UserBot"
    dev_link = "https://t.me/PureAholy"
    cpu_usage = get_cpu_usage()
    ram_usage = get_ram_usage()
    current_time = arrow.get()
    uptime = current_time.shift(seconds=perf_counter() - bot_uptime)
    kernel_version = subprocess.run(["uname", "-a"], capture_output=True).stdout.decode().strip()
    system_uptime = subprocess.run(["uptime", "-p"], capture_output=True).stdout.decode().strip()

    current_hash = git.Repo().head.commit.hexsha
    git.Repo().remote("origin").fetch()
    branch = git.Repo().active_branch.name
    upcoming = next(git.Repo().iter_commits(f"origin/{branch}", max_count=1)).hexsha
    upcoming_version = len(list(git.Repo().iter_commits()))
    current_version = upcoming_version - (
        len(list(git.Repo().iter_commits(f"{current_hash}..{upcoming}")))
    )

    result = (
        f"<emoji id=5276137821558548459>🖼️</emoji> <a href='{repo_link}'>Pure</a> / "
    )
    result += f"<a href='{repo_link}/commit/{current_hash}'>#{current_hash[:7]} ({current_version})</a>\n\n"
    result += f"<b>Pyrogram:</b> <code>{pyrogram.__version__}</code>\n"
    result += f"<b>Python:</b> <code>{sys.version}</code>\n"
    result += f"<b>Разработчик:</b> <a href='{dev_link}'>PureAholy</a>\n\n"

    if "-a" not in common_args:
        return await message.edit(result, disable_web_page_preview=True)

    result += "<b>Статус:</b>\n"
    result += (
        f"├─<b>Работает:</b> <code>{uptime.humanize(current_time, only_distance=True)}</code>\n"
    )
    result += f"├─<b>Ветка:</b> <code>{branch}</code>\n"
    result += f"├─<b>Текущая версия:</b> <a href='{repo_link}/commit/{current_hash}'>"
    result += f"#{current_hash[:7]} ({current_version})</a>\n"
    result += f"├─<b>Последняя версия:</b> <a href='{repo_link}/commit/{upcoming}'>"
    result += f"#{upcoming[:7]} ({upcoming_version})</a>\n"
    result += f"├─<b>Текущий префикс:</b> <code>{prefix}</code>\n"
    result += f"├─<b>Подключенных модулей:</b> <code>{modules_help.modules_count}</code>\n"
    result += f"└─<b>Включенных команд:</b> <code>{modules_help.commands_count}</code>\n\n"

    result += "<b>Статус:</b>\n"
    result += f"├─<b>ОС:</b> <code>{sys.platform}</code>\n"
    result += f"├─<b>Ядро:</b> <code>{kernel_version}</code>\n"
    result += f"├─<b>Работает:</b> <code>{system_uptime}</code>\n"
    result += f"├─<b>Использовано ЦП:</b> <code>{cpu_usage}%</code>\n"
    result += f"└─<b>Использовано ОЗУ:</b> <code>{ram_usage}МБ</code>"

    await message.edit(result, disable_web_page_preview=True)


module = modules_help.add_module("base", __file__)
module.add_command("help", "Получение информациии по модулям.", "[module/command name]", ["h"])
module.add_command("prefix", "Установка другого префикса", None, ["kprefix"])
module.add_command("restart", "Перезагрузка юзер-бота")
module.add_command("update", "Обновление юзер-бота с репозитория")
module.add_command("sendmod", "Отправка модуля с юзер-бота", "[module_name]", ["sm"])
module.add_command("status", "Получить статус работы юзер-бота", "[-a]")
