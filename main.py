import discord
from discord.ext import commands
import traceback
import sqlite3
import db as dbase
from settings import *


bot = commands.Bot(command_prefix = "!")

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))


@bot.listen('on_message')
async def type(message):
    if message.author != message.guild.me:
        chat = message.channel.id
        allowed_chats = dbase.get_chats(message.guild.id)
        if chat == allowed_chats["slave"]:
            await message.channel.set_permissions(message.author, read_messages=True,
                                                        send_messages=False)
        if chat in allowed_chats.values():
            try: await message.delete()
            except: pass


def update_gamestat(): pass



async def send_notification(ctx, text): # Отправляет text в канал "Уведомления"
    guild = ctx.message.guild
    s_chat = dbase.get_chats(guild.id)["slave"]
    if s_chat:
        s_chat = guild.get_channel(s_chat)
        await s_chat.send(text)

async def clear_notifications(ctx):
    guild = ctx.message.guild
    s_chat = dbase.get_chats(guild.id)["slave"]
    if s_chat:
        s_chat = guild.get_channel(s_chat)
        messages = await s_chat.history().flatten()
        await s_chat.delete_messages(messages)




async def send_master(ctx, text): # Отправляет text в канал "Главная"
    guild = ctx.message.guild
    m_chat = dbase.get_chats(guild.id)["master"]
    if m_chat:
        m_chat = guild.get_channel(m_chat)
        await m_chat.send(text)

async def clear_master(ctx): # Удаляет сообщения в канале "Главная"
    guild = ctx.message.guild
    m_chat = dbase.get_chats(guild.id)["master"]
    if m_chat:
        m_chat = guild.get_channel(m_chat)
        messages = await m_chat.history().flatten()
        await m_chat.delete_messages(messages)





#========ОСНОВНЫЕ ОБОЛОЧКИ ДЛЯ КОМАНД========

def user_check(func): #Проверяет нужно ли отвечать на команду юзерского доступа
    async def wrapper(ctx, *args):
        server_id = ctx.message.guild.id
        a_chat = dbase.get_chats(server_id)["admin"]
        m_chat = dbase.get_chats(server_id)["master"]
        if ctx.message.channel.id in [m_chat, a_chat]:
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


def game_check(func): #Проверяет нужно ли отвечать на игровую команду
    async def wrapper(ctx, *args):
        server_id = ctx.message.guild.id
        m_chat = dbase.get_chats(server_id)["master"]
        if ctx.message.channel.id == m_chat and dbase.isGameStarted(server_id):
            await func(ctx, *args)
            #await send_master(ctx, "*Обновил таблицу*")
    wrapper.__name__ = func.__name__
    return wrapper

#==============================================




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


#==========ИГРА=====================


async def update_players_list(ctx): # Отображает логированных игроков до начала матча
    await clear_master(ctx)
    server = ctx.message.guild
    i = 1
    if not dbase.isGameStarted(server.id):
        text = "Список игроков:\n"
        for player in dbase.get_all_players(server.id):
            text += f"{i}. {(await server.fetch_member(player['discord_id'])).name}\n"
            i += 1
        await send_master(ctx, text)




async def update_gamestat(ctx):
    pass






@bot.command()
@admin_check
async def start(ctx, *args): # Начинает игру с логированными игроками
    dbase.add_players_on_gboard(ctx.message.guild.id)
    await clear_notifications(ctx)
    await send_notification(ctx, "Игра началась!")



@bot.command()
@admin_check
async def finish(ctx, *args): #Завершает игру досрочно
    dbase.clear_gboard(ctx.message.guild.id)
    await clear_notifications(ctx)
    await send_notification(ctx, "Игра была досрочно завершена")






@bot.command()
@user_check
async def login(ctx, *args): # Заносит игрока в базу логированных (можно сказать хаб ожидания)
    message = ctx.message
    server_id = message.guild.id
    discord_id = message.author.id
    if dbase.get_player_id(discord_id, server_id) == None:
        dbase.add_player(discord_id,server_id)
        await send_notification(ctx, f"Добро пожаловать в игру, {message.author.mention}")
        await update_players_list(ctx)


@bot.command()
@user_check
async def leave(ctx, *args): # Удаляет игрока из хаба/матча
    message = ctx.message
    server_id = message.guild.id
    discord_id = message.author.id
    if dbase.get_player_id(discord_id, server_id) != None:
        dbase.remove_player(discord_id,server_id)
        await send_notification(ctx, f"{message.author.mention} покинул игру.\nДо встречи!")
        await update_players_list(ctx)





@bot.command()
@game_check
async def transfer(ctx, mention, count):
    message = ctx.message
    player = message.author.mention
    mention = message.mentions[0]; count = int(count)
    server_id = ctx.message.guild.id

    data_sender = dbase.get_gboard_player(message.author.id, server_id)
    data_reciver = dbase.get_gboard_player(mention.id, server_id)

    x_sender, y_sender = [int(i) for i in data_sender["pos"].split(":")]
    x_reciver, y_reciver = [int(i) for i in data_reciver["pos"].split(":")]
    pos_delta = max(abs(x_sender - x_reciver), abs(y_sender - y_reciver))
    text = ""

    if not data_reciver["id"]: text = f"Пользователь не учавствет в игре, {player}"
    elif pos_delta > 3: text = f"Слишком далеко, {player}"
    elif data_sender["points"] < count: text = f"У тебя недостаточно ОД для отправки, {player}"
    else:
        data_reciver["points"] += count
        data_sender["points"] -= count
        dbase.update_gboard_player(data_sender)
        dbase.update_gboard_player(data_reciver)
        text = f"{player} передал {mention.mention} {count} ОД"

    await send_notification(ctx, text)






@bot.command()
@game_check
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






from threading import Thread
import time

def sentinel():
    for data in dbase.get_all_gboard_players():
        data["points"] += 1
        dbase.update_gboard_player(data)


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


bot.run(token)




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