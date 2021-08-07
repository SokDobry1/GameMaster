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


@bot.listen('on_message')
async def type(message):
    chat = message.channel.id
    if chat == dbase.get_chats(message.guild.id)["slave"]:
        await message.channel.set_permissions(message.author, read_messages=True,
                                                      send_messages=False)
        await message.delete()



def user_check(func):
    async def wrapper(ctx):
        server_id = ctx.message.guild.id
        a_chat = dbase.get_chats(server_id)["admin"]
        m_chat = dbase.get_chats(server_id)["master"]
        if ctx.message.channel.id in [m_chat, a_chat]:
            return await func(ctx)
    wrapper.__name__ = func.__name__
    return wrapper


def admin_check(func):
    async def wrapper(ctx):
        server_id = ctx.message.guild.id
        a_chat = dbase.get_chats(server_id)["admin"]
        if ctx.message.channel.id == a_chat or (not a_chat):
            return await func(ctx)
    wrapper.__name__ = func.__name__
    return wrapper



@bot.command()
@user_check
async def say(ctx):
    await ctx.message.delete()
    await ctx.send(ctx.message.content[5:])


@bot.command()
@admin_check
async def init(ctx):
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
async def clear(ctx):
    chats = dbase.get_chats(ctx.message.guild.id)
    if chats["admin"]:
        category = None
        for i in chats:
            channel = bot.get_channel(chats[i])
            category = channel.category
            await channel.delete()
        await category.delete()
        dbase.wipe(ctx.message.guild.id)


@bot.command()
@admin_check
async def test(ctx):
    message = ctx.message
    roles = message.guild.self_role
    await ctx.send(str(type(roles)))



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