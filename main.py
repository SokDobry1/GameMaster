from typing import Text
import discord
from discord import message
from discord.ext import commands
import traceback
import sqlite3
import db as dbase
from settings import *


bot = commands.Bot(command_prefix = "!")

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

def admin_help_check(): pass

@bot.listen('on_message')
async def type(message):
    if message.author != message.guild.me:
        chat = message.channel.id
        allowed_chats = dbase.get_chats(message.guild.id)
        if chat == allowed_chats["slave"]:
            await message.channel.set_permissions(message.author, read_messages=True,
                                                        send_messages=False)
        if chat in allowed_chats.values():
            await admin_help_check(message)
            try: await message.delete()
            except: pass


def update_gamestat(): pass
def update_lobby(): pass
def win_checker(): pass
def get_user_help(): pass
admin_help = ""

#==================ТЕХНИЧЕСКИЕ ФУНКЦИИ=========================

#-----АДМИНКА------


async def admin_help_check(message):
    guild = message.guild
    a_chat = dbase.get_chats(guild.id)["admin"]
    if a_chat:
        a_chat = guild.get_channel(a_chat)
        messages = await a_chat.history().flatten()
        if not len(messages): await a_chat.send(admin_help)


#---УВЕДОМЛЕНИЯ----
async def send_notification(ctx, text, file=None): # Отправляет text в канал "Уведомления"
    guild = ctx.message.guild
    s_chat = dbase.get_chats(guild.id)["slave"]
    if s_chat:
        s_chat = guild.get_channel(s_chat)
        await s_chat.send(text, file=file)


async def clear_notifications(ctx): # Очищает канал "Уведомления"
    guild = ctx.message.guild
    s_chat = dbase.get_chats(guild.id)["slave"]
    if s_chat:
        s_chat = guild.get_channel(s_chat)
        messages = await s_chat.history().flatten()
        await s_chat.delete_messages(messages)


#-------ГЛАВНАЯ-------

async def send_master(ctx, text, file=None): # Отправляет text в канал "Главная"
    guild = ctx.message.guild
    m_chat = dbase.get_chats(guild.id)["master"]
    if m_chat:
        m_chat = guild.get_channel(m_chat)

        messages = await m_chat.history().flatten()
        if not len(messages):
            f = discord.File(open("separator.jpg", "rb"))
            await m_chat.send(get_user_help(), file=f)

        await m_chat.send(text, file=file)

async def clear_master(ctx, remove_all=False): # Очищает канал "Главная"
    guild = ctx.message.guild
    m_chat = dbase.get_chats(guild.id)["master"]
    if m_chat:
        m_chat = guild.get_channel(m_chat)
        messages = await m_chat.history().flatten()
        for i in messages:
            try:
                if len(i.attachments) == 0 or remove_all: await i.delete()
            except: pass


#==============================================



#========ОСНОВНЫЕ ОБОЛОЧКИ ДЛЯ КОМАНД========

def user_check(func): #Проверяет нужно ли отвечать на команду юзерского доступа
    async def wrapper(ctx, *args):
        server_id = ctx.message.guild.id
        m_chat = dbase.get_chats(server_id)["master"]
        if ctx.message.channel.id == m_chat:
            await func(ctx, *args)
    wrapper.__name__ = func.__name__
    return wrapper


def admin_check(func): #Проверяет нужно ли отвечать на команду админского доступа
    async def wrapper(ctx, *args):
        server_id = ctx.message.guild.id
        a_chat = dbase.get_chats(server_id)["admin"]
        if ctx.message.channel.id == a_chat or (not a_chat):
            await func(ctx, *args)
    wrapper.__name__ = func.__name__
    return wrapper


def game_alive_check(func): #Проверяет нужно ли отвечать на игровую команду для живых
    async def wrapper(ctx, *args):
        server_id = ctx.message.guild.id
        m_chat = dbase.get_chats(server_id)["master"]
        if ctx.message.channel.id == m_chat and dbase.isGameStarted(server_id):
            hp = dbase.get_gboard_player(ctx.message.author.id, server_id)["hp"]
            if hp:
                await func(ctx, *args)
                await win_checker(ctx)
                if dbase.isGameStarted(server_id):
                    await update_gamestat(ctx)

    wrapper.__name__ = func.__name__
    return wrapper


def game_ghost_check(func):
    async def wrapper(ctx, *args):
        server_id = ctx.message.guild.id
        m_chat = dbase.get_chats(server_id)["master"]
        if ctx.message.channel.id == m_chat and dbase.isGameStarted(server_id):
            hp = dbase.get_gboard_player(ctx.message.author.id, server_id)["hp"]
            if hp == 0:
                await func(ctx, *args)
                if dbase.isGameStarted(server_id):
                    await update_gamestat(ctx)

    wrapper.__name__ = func.__name__
    return wrapper

#==============================================


#===============ИНИЦИАЛИЗАЦИЯ БОТА=============


@bot.command()
@admin_check
async def init(ctx, *args): # Создаёт записи в бд и чаты на сервере
    guild = ctx.message.guild

    if not dbase.get_chats(guild.id)["admin"]:
        category = await guild.create_category("Game")
        admin = await guild.create_text_channel("Управление", category=category)
        master = await guild.create_text_channel("Главная", category=category)
        slave = await guild.create_text_channel("Уведомления", category=category)
        dbase.init(guild.id, admin.id, master.id, slave.id)
        await update_lobby(ctx)
        await ctx.send("Бот развёрнут успешно")
    else: await ctx.send("Бот уже развёрнут")
    


@bot.command()
@admin_check
async def clear(ctx, *args): # Удаляет все смежные записи в бд и чаты на сервере
    chats = dbase.get_chats(ctx.message.guild.id)
    if chats["admin"]:
        category = None
        for i in chats:
            channel = bot.get_channel(chats[i])
            category = channel.category
            await channel.delete()
        await category.delete()
        dbase.wipe(ctx.message.guild.id)


#=============================================


#====================ИГРА=====================

#--------ВЫВОД ИНФОРМАЦИИ-----

async def update_lobby(ctx): # Отображает логированных игроков до начала матча
    await clear_master(ctx)
    server = ctx.message.guild
    i = 1
    if not dbase.isGameStarted(server.id):
        text = "Список ожидающих игроков:\n"
        for player in dbase.get_all_players(server.id):
            text += f"{i}. {(await server.fetch_member(player['discord_id'])).name}\n"
            i += 1
        await send_master(ctx, text)




async def update_gamestat(ctx):
    await clear_master(ctx)
    server = ctx.message.guild
    await send_master(ctx, "Таблица с данными")




#----ВЗАИМОДЕЙСТВИЕ С ИГРОВЫМ ПОЛЕМ-----

@bot.command()
@admin_check
async def start(ctx, *args): # Начинает игру с логированными игроками
    dbase.add_players_on_gboard(ctx.message.guild.id)
    await clear_notifications(ctx)
    await send_notification(ctx, "Игра началась!")
    await clear_master(ctx, True)
    await update_gamestat(ctx)



@bot.command()
@admin_check
async def finish(ctx, *args): #Завершает игру досрочно
    dbase.clear_gboard(ctx.message.guild.id)
    await clear_notifications(ctx)
    await send_notification(ctx, "Игра была досрочно завершена")
    await clear_master(ctx, True)
    await update_lobby(ctx)




#--------ВЗАИМОДЕЙСТВИЕ ИГРОКОВ С ЛОББИ---------


@bot.command()
@user_check
async def login(ctx, *args): # Заносит игрока в базу логированных (можно сказать хаб ожидания)
    message = ctx.message
    server_id = message.guild.id
    discord_id = message.author.id
    if dbase.get_player_id(discord_id, server_id) == None:
        dbase.add_player(message.author.name, discord_id,server_id)
        await send_notification(ctx, f"Добро пожаловать в зал ожидания, {message.author.mention}\nУстраивайся поудобнее")
        await update_lobby(ctx)


@bot.command()
@user_check
async def leave(ctx, *args): # Удаляет игрока из хаба/матча
    message = ctx.message
    server_id = message.guild.id
    discord_id = message.author.id
    if dbase.get_player_id(discord_id, server_id) != None:
        dbase.remove_player(discord_id,server_id)
        await send_notification(ctx, f"{message.author.mention} покинул игру.\nДо встречи!")
        await update_lobby(ctx)





#----------ИГРОВЫЕ КОМАНДЫ---------


@bot.command()
@game_alive_check
async def attack(ctx, mention, damage):
    message = ctx.message
    player = message.author.mention
    mention = message.mentions[0]; damage = abs(int(damage))
    server_id = ctx.message.guild.id

    data_sender = dbase.get_gboard_player(message.author.id, server_id)
    data_reciver = dbase.get_gboard_player(mention.id, server_id)

    if not data_reciver["id"]:
        await send_notification(ctx, f"Пользователь не учавствет в игре, {player}")
        return

    x_sender, y_sender = [int(i) for i in data_sender["pos"].split(":")]
    x_reciver, y_reciver = [int(i) for i in data_reciver["pos"].split(":")]

    if data_reciver["hp"] < damage: damage = data_reciver["hp"]
    pos_delta = max(abs(x_sender - x_reciver), abs(y_sender - y_reciver))
    text = ""

    if pos_delta > 3: text = f"Слишком далеко, {player}"
    elif data_sender["points"] < damage: text = f"У тебя недостаточно ОД для атаки, {player}"
    else:
        data_reciver["hp"] -= damage
        data_sender["points"] -= damage
        data_sender["damage"] += damage

        if data_reciver["hp"] <= 0:
            data_reciver["pos"] = ""

        dbase.update_gboard_player(data_sender)
        dbase.update_gboard_player(data_reciver)
        text = f"{player} нанес {mention.mention} {damage} ед. урона"

    await send_notification(ctx, text)

    if data_reciver["hp"] <= 0:
        await send_notification(ctx, f"{mention.mention} погиб")





@bot.command()
@game_alive_check
async def transfer(ctx, mention, count):
    message = ctx.message
    player = message.author.mention
    mention = message.mentions[0]; count = int(count)
    server_id = ctx.message.guild.id

    data_sender = dbase.get_gboard_player(message.author.id, server_id)
    data_reciver = dbase.get_gboard_player(mention.id, server_id)

    if not data_reciver["id"]:
        await send_notification(ctx, f"Пользователь не учавствет в игре, {player}")
        return

    x_sender, y_sender = [int(i) for i in data_sender["pos"].split(":")]
    x_reciver, y_reciver = [int(i) for i in data_reciver["pos"].split(":")]
    pos_delta = max(abs(x_sender - x_reciver), abs(y_sender - y_reciver))
    text = ""

    if pos_delta > 3: text = f"Слишком далеко, {player}"
    elif data_sender["points"] < count: text = f"У тебя недостаточно ОД для отправки, {player}"
    else:
        data_reciver["points"] += count
        data_reciver["recive_points"] += count
        data_sender["points"] -= count
        data_sender["send_points"] += count
        dbase.update_gboard_player(data_sender)
        dbase.update_gboard_player(data_reciver)
        text = f"{player} передал {mention.mention} {count} ОД"

    await send_notification(ctx, text)



@bot.command()
@game_alive_check
async def move(ctx, *args):
    server_id = ctx.message.guild.id
    pos = ctx.message.content[6:].upper()
    try:
        x = pos[0]; y = int(pos[1:])
        x = ord(x) - 64
        if not dbase.can_step(server_id, f"{x}:{y}"): int("ERR")
        
        data = dbase.get_gboard_player(ctx.message.author.id, server_id)
        old_x, old_y = [int(i) for i in data["pos"].split(":")]
        points_need = max(abs(old_x - x), abs(old_y - y))
        if points_need > data["points"]: int("ERR")

        data["points"] -= points_need; data["pos"] = f"{x}:{y}"
        dbase.update_gboard_player(data)

        await send_notification(ctx, f"{ctx.message.author.mention} ходит с {chr(old_x+64)}{old_y} на {chr(x+64)}{y}")

    except: 
        await send_notification(ctx, f"Неправильный ввод координат, {ctx.message.author.mention}")
        return



#----------ПРИЗРАКИ--------------


@bot.command()
@game_ghost_check
async def donate(ctx, *args):
    message = ctx.message
    server_id = ctx.message.guild.id
    player = message.author
    mention = message.mentions[0]
    text = ""
    reciver_hp = dbase.get_gboard_player(mention.id, server_id)["hp"]

    if not dbase.isGhostCanMakeRequest(player.id, server_id):
        text = f"{player.mention}, на сегодня ты больше не можешь делать запросов"
    elif reciver_hp == 0:
        text = f"{player.mention}, призрак не может влиять на призраков"
    elif reciver_hp == None:
        text = f"Пользователь не учавствет в игре, {player.mention}"
    else:
        text = f"Призрак {player.mention} сделал свой ход"
        dbase.make_ghost_request(player.id, server_id, "donate", mention.name)
    
    await send_notification(ctx, text)

    temp = dbase.get_equal_ghosts_requests(server_id, "donate", mention.name)
    if len(temp) == len(dbase.get_all_gboard_ghosts(server_id)) or len(temp) > 2:
        data = dbase.get_gboard_player(mention.id, server_id)
        data["points"] += 1
        dbase.update_gboard_player(data)
        await send_notification(ctx, f"Игрок {mention.mention} получил 1 ОД от призраков")


@bot.command()
@game_ghost_check
async def snatch(ctx, *args):
    message = ctx.message
    server_id = ctx.message.guild.id
    player = message.author
    mention = message.mentions[0]
    text = ""
    reciver_hp = dbase.get_gboard_player(mention.id, server_id)["hp"]

    if not dbase.isGhostCanMakeRequest(player.id, server_id):
        text = f"{player.mention}, на сегодня ты больше не можешь делать запросов"
    elif reciver_hp == 0:
        text = f"{player.mention}, призрак не может влиять на призраков"
    elif reciver_hp == None:
        text = f"Пользователь не учавствет в игре, {player.mention}"
    else:
        text = f"Призрак {player.mention} сделал свой ход"
        dbase.make_ghost_request(player.id, server_id, "snatch", mention.name)
    
    await send_notification(ctx, text)

    temp = dbase.get_equal_ghosts_requests(server_id, "snatch", mention.name)
    if len(temp) == len(dbase.get_all_gboard_ghosts(server_id)) or len(temp) > 2:
        data = dbase.get_gboard_player(mention.id, server_id)
        data["points"] -= 1
        dbase.update_gboard_player(data)
        await send_notification(ctx, f"Призраки забрали 1 ОД у {mention.mention}")




async def win_checker(ctx):
    server = ctx.message.guild
    alive_users = []

    for player in dbase.get_all_gboard_players(server.id):
        if player["hp"]:
            alive_users += [player]

    if len(alive_users) == 1:
        stat = alive_users[0]
        hero = dbase.get_player_by_id(alive_users[0]["id"])
        hero_mention = (await server.fetch_member(hero['discord_id'])).mention
        dbase.clear_gboard(server.id)

        pic = discord.File(open("win.jpg", "rb"))
        await send_notification(ctx, f"{hero_mention} побеждает в этой игре, он\n\
Нанёс урона: {stat['damage']}\nПожертвовал ОД: {stat['send_points']}\n\
Получил ОД: {stat['recive_points']}\nПрими мои поздравления, победитель!", pic)
        await update_lobby(ctx)

    elif len(alive_users) == 0:
        pic = discord.File(open("0surv.gif", "rb"))
        await send_notification(ctx, "", pic)
        


#================ТЕХНИЧЕСКАЯ ЗОНА (ДАЛЬШЕ НИЧЕГО)=====================


from threading import Thread
import time

def sentinel():
    for data in dbase.global_get_gboard_players():
        data["points"] += 1
        dbase.update_gboard_player(data)
        dbase.global_clear_ghosts_requests()


def pinger():
    flag = True
    while True:
        clock = time.localtime(time.time())
        if clock.tm_hour == 8 and clock.tm_min == 0:
            if flag:
                flag = False
                sentinel()
        else: flag = True
        time.sleep(5)

Thread(target=pinger, daemon=True).start()



def get_user_help():
    x = len(dbase.get("SELECT * FROM servers"))
    return f"""Спасибо, что выбрали меня.
Сейчас я развёрнут на {x} серверах.

Автор игры: BurnedTuner#0367
Авторs бота: VeDmEd_u_Ko#3837, Voladsky#6401

Правила игры:
Каждый игрок получает одно очко действия (ОД) в день.

ОД можно тратить на одно из этих действий:

1. Передвижение на 1 клетку в любую сторону (как король в шахматах)
2. Отдать свои ОД игроку в радиусе 3 клеток
3. Выстрелить в игрока в радиусе 3 клеток
У каждого игрока есть 3 жизни
После смерти игроки становятся "призраками"

Возможные действия призраков:

1. Если три призрака решили вместе помочь одному из игроков, он получает +1 ОД
2. Если три призрака решили вместе помешать одному из игроков, он теряет 1 ОД
3. Если призраков меньше трех, то их решение должно быть единогласным

Очищение истории действий призраков и зачисление ОД происходит в 8 утра по МСК

Победителем считается последний выживший игрок

Помощь по командам:

До старта игры:
!login - Зайти в комнату ожидания (войти в уже начатую игру нельзя)
!leave - Выйти из комнаты ожидания/игры

Живым игрокам:
!move [клетка] - Перемещает игрока на указанную клетку по кратчайшей траектории (формат клетки: <x><y>, например: А15)
!attack @[имя] [урон] - Атакует упомянутого игрока
!transfer @[имя] [сумма] - Передаёт упомянутому игроку указанную сумму ОД

Призракам:
!donate @[имя] - Создаёт запрос на пожертвование 1 ОД игроку
!snatch @[имя] - Создаёт запрос на кражу 1 ОД у игрока

Приятной игры!
"""

admin_help = """Этот чат предназначен только для команд управления игрой. Вся информация доступна в канале "главная".

Совет администраторам: Желательно сделать этот чат скрытым для обычных игроков во избежание непредвиденных ситуаций

Команды:
!start - Начинает игру составом из комнаты ожидания
!finish - Досрочно завершает игру
!kik @[имя] - Удаляет упомянутого пользователя из игры

!init - Разворачивает необходимые для бота чаты
!clear - Удаляет всё созданное ботом на сервере

Удачи!"""




'''
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    #if message.content.startswith('f'):
    text = message.content
    try:
        #await message.channel.send(getattr(message, text))
        await message.channel.send("")
    except Exception as e: 
        await message.channel.send(traceback.format_exc())
'''


bot.run(token)