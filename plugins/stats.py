import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.filters import command
from utils.scripts import get_args
from bs4 import BeautifulSoup as BS
from datetime import datetime

async def fetch_page(url: str) -> BS:
    """Выполняет асинхронный GET-запрос и возвращает объект BeautifulSoup."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status() 
            html = await response.text()
            return BS(html, 'html.parser')

def days_to_season_end():
    """Возвращает количество дней до конца сезона с правильным склонением."""
    date1 = datetime.now()
    date2 = datetime(day=3, month=3, year=2023)
    countdown = (date2 - date1).days
    days_word = ['день', 'дня', 'дней']
    p = 0 if countdown % 10 == 1 and countdown % 100 != 11 else (
        1 if 2 <= countdown % 10 <= 4 and (countdown % 100 < 10 or countdown % 100 >= 20) else 2)
    return f"{countdown} {days_word[p]}"

@Client.on_message(~filters.scheduled & command(["stats"]) & filters.me & ~filters.forwarded)
async def handler(_, message: Message):
    if message.from_user.id == 183416928:
        await message.answer('poshel naxyi', reply_to=message.id)
        return

    args, _ = get_args(message)
    nick = args[0]
    url = f'https://iccup.com/dota/gamingprofile/{nick}'
    
    try:
        soup = await fetch_page(url)
        text = soup.find('div', id='main-stata-5x5')
        if not text:
            await message.answer('Такого аккаунта не существует.', reply_to=message.id)
            return
        
        stats = text.text.replace('\n', ' ').split()
        main = (
            f"🔮 РЕЙТИНГ аккаунта\n\n"
            f"🔰 Логин: {nick}\n"
            f"🔝 Положение в рейтинге: {stats[21]}\n"
            f"🏆 Ранк (pts): {stats[0]}\n"
            f"⚔️ K/D/A: {stats[3]} / {stats[5]} / {stats[7]} K {stats[9]}\n"
            f"❇ Win/Lose/Leave: {stats[27]} / {stats[29]} / {stats[31]}\n"
            f"🐊 Нейтралов убито: {stats[37]}\n"
            f"🐔 Курьеров убито: {stats[34]}\n"
            f"⏰ Налётанные часы: {stats[40]}\n"
            f"👑 Победы: {stats[42]}\n"
            f"💤 Кол-во ливов: {stats[45]}\n"
            f"📊 Лучший счёт: {stats[48]} - {stats[50]} - {stats[52]}\n"
            f"🔱 Макс. стрик побед: {stats[56]}\n"
            f"⚜ Текущий стрик: {stats[59]}\n"
            f"<emoji id=5276137821558548459>🖼️</emoji> Группа {ds}\n"
            f"⏳ Конец сезона через: {days_to_season_end()}\n"
        )
        await message.answer(main, reply_to=message.id)
    except Exception as e:
        await message.answer(f"Ошибка: {e}", reply_to=message.id)

@Client.on_message(~filters.scheduled & command(["last"]) & filters.me & ~filters.forwarded)
async def lastgame(_, message: Message):
    if message.from_user.id == 183416928:
        await message.answer('poshel naxyi', reply_to=message.id)
        return

    args, _ = get_args(message)
    try:
        nick = args[0]
        url = f'https://iccup.com/dota/gamingprofile/{nick}'
        soup = await fetch_page(url)
        games = soup.find('tbody', id='result-table').find_all('td', limit=5)
        alls = f'ПОСЛЕДНЯЯ ИГРА\n\n👨‍💻 Логин: {nick}\n🧜 Герой: {games[0].text.strip()}\n👟 Мод: {games[1].text.strip()}\n⏰ Время: {games[2].text.strip()}\n⚔️ K/D/A: {games[3].text.strip()}\n🔥 Очки: {games[4].text.strip()} PTS\n\n⏳ Конец сезона через: {days_to_season_end()}'
        await message.answer(alls, reply_to=message.id)
    except IndexError:
        await message.answer('Игрок ещё не играл', reply_to=message.id)

@Client.on_message(~filters.scheduled & command(["top"]) & filters.me & ~filters.forwarded)
async def top(_, message: Message):
    if message.from_user.id == 183416928:
        await message.answer('poshel naxyi', reply_to=message.id)
        return

    url = 'https://iccup.com/dota/ladder'
    soup = await fetch_page(url)
    find_pts_players = soup.find_all('div', class_="field2 width70p10", limit=5)
    find_stats_players = soup.find_all('div', class_="field2 width80c", limit=5)
    find_wrl_players = soup.find_all('div', class_="field2 width80r", limit=5)
    find_players = soup.find_all('div', class_='field2 width210 ladder-flag', limit=5)

    toplist = []
    for i in range(5):
        a = f'#{i+1} {find_players[i].text.strip()} {find_pts_players[i].text.strip()} {find_stats_players[i].text.strip()} {find_wrl_players[i].text.strip()}'
        toplist.append(a)
    
    out = f'№ | Игрок | Очки | Стата | Победа\n' + '\n'.join(toplist)
    await message.answer(out, reply_to=message.id)

@Client.on_message(~filters.scheduled & command(["ladder"]) & filters.me & ~filters.forwarded)
async def ladder(_, message: Message):
    if message.from_user.id == 183416928:
        await message.answer('poshel naxyi', reply_to=message.id)
        return

    url = 'https://iccup.com/dota/teams.html'
    soup = await fetch_page(url)
    find_pts_teams = soup.find_all('div', class_="field2 width70", limit=10)
    find_stats_teams = soup.find_all('div', class_="field2 width70c", limit=10)
    find_wrl_teams = soup.find_all('div', class_="field2 width90c", limit=5)
    find_teams = soup.find_all('div', class_='field2 width200', limit=5)

    toplist = []
    com = [find_stats_teams[n].text.strip() + '  ' + find_stats_teams[n+1].text.strip() for n in range(0, 10, 2)]
    com2 = [find_pts_teams[j].text.strip() for j in range(0, 10)]
    del com2[:-1:2]
    
    for i in range(5):
        a = f'#{i+1} {find_teams[i].text.strip()} {find_wrl_teams[i].text.strip()} {com2[i]} {com[i]}'
        toplist.append(a)

    out = f'№ | Команда | Игроки | Стата | Победа\n' + '\n'.join(toplist)
    await message.answer(out, reply_to=message.id)

@Client.on_message(~filters.scheduled & command(["profile"]) & filters.me & ~filters.forwarded)
async def profile(_, message: Message):
    args, _ = get_args(message)
    if message.from_user.id == 183416928:
        await message.answer('poshel naxyi', reply_to=message.id)
        return

    try:
        nick = args[0]
        url = f'https://iccup.com/profile/view/{nick}'
        soup = await fetch_page(url)
        text = soup.find('div', class_='allinfo width395')
        mesto = text.find('span', class_="user-flag").find('a').attrs['title']
        p1 = text.find('div', class_='infoblock-tbl')
        p3 = p1.find_all(class_='nth-2')
        key = [h.text for h in p3]
        profile = (
            f"🔮 ПРОФИЛЬ аккаунта\n\n"
            f"👨‍💻 Логин: {nick}\n"
            f"🗣 Настоящее имя: {key[0]}\n"
            f"🌍 Местоположение: {mesto} ({key[1]})\n"
            f"💬 Скайп: {key[2]}\n"
            f"🟣 Дискорд: {key[3]}\n"
            f"🔵 ВКонтакте: {key[4]}\n"
            f"👀 Возраст: {key[5]}\n"
            f"🖱 Мышка: {key[6]}\n"
            f"⌨️ Клавиатура: {key[7]}\n"
            f"🎧 Наушники: {key[8]}\n"
            f"🌫️ Коврик: {key[9]}\n\n"
            f"⏳ Конец сезона через: {days_to_season_end()}"
        )
        await message.answer(profile, reply_to=message.id)
    except AttributeError:
        await message.answer('Такого аккаунта не существует.', reply_to=message.id)

@Client.on_message(~filters.scheduled & command(["last5"]) & filters.me & ~filters.forwarded)
async def lastgames(_, message: Message):
    args, _ = get_args(message)
    if message.from_user.id == 183416928:
        await message.answer('poshel naxyi', reply_to=message.id)
        return

    try:
        nick = args[0]
        url = f'https://iccup.com/dota/gamingprofile/{nick}'
        soup = await fetch_page(url)
        games = soup.find('tbody', id='result-table').find_all('td', limit=5)

        last5 = []
        for game in games[:5]:
            last5.append(f'🧜 Герой: {game.text.strip()}\n')

        await message.answer('ПОСЛЕДНИЕ 5 ИГР\n\n' + '\n'.join(last5), reply_to=message.id)
    except IndexError:
        await message.answer('Игрок ещё не играл', reply_to=message.id)
