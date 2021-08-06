import discord
from discord import message
from discord.ext import commands
import traceback
import sqlite3
import db as dbase


bot = commands.Bot(command_prefix = "!")

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))


def check(func):
    async def wrapper(ctx):
        server_id = ctx.message.guild.id
        a_chat = dbase.get_chats(server_id)["admin"]
        m_chat = dbase.get_chats(server_id)["master"]
        if ctx.message.channel.id in [m_chat, a_chat] or (not a_chat):
            return await func(ctx)
        return 0
    wrapper.__name__ = func.__name__
    return wrapper




@bot.command()
@check
async def say(ctx):
    await ctx.message.delete()
    await ctx.send(ctx.message.content[5:])


@bot.command()
@check
async def init(ctx):
    guild = ctx.message.guild
    category = await guild.create_category("Game")
    admin = await guild.create_text_channel("Управление", category=category)
    master = await guild.create_text_channel("Главная", category=category)
    slave = await guild.create_text_channel("Уведомления", category=category)
    dbase.init(guild.id, admin.id, master.id, slave.id)
    


@bot.command()
@check
async def clear(ctx):
    chats = dbase.get_chats(ctx.message.guild.id)
    for i in chats:
        await bot.get_channel(chats[i]).delete()
    dbase.wipe(ctx.message.guild.id)


@bot.command()
@check
async def db(ctx):
    message = ctx.message
    text = message.content[4:]
    try:
        getattr(dbase, text)(message.guild.id,message.channel.id)
    except Exception as e:
        await ctx.send(traceback.format_exc())


bot.run('ODczMTUzMTkwMjczNjEzOTI1.YQ0RRg.KaGNf_pq7ukFF8FmXEHo0HxFbiQ')




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