import discord
from discord.ext import commands
import traceback
import sqlite3

m_chat = None
s_chat = None

#client = discord.Client()
bot = commands.Bot(command_prefix = "!")

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

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

def check(func):
    async def wrapper(ctx):
        if ctx.message.channel.id == m_chat or m_chat == None:
            return await func(ctx)
        return 0
    return wrapper

@bot.command()
async def init(ctx):
    global m_chat, s_chat
    id = ctx.message.channel.id
    if m_chat == None:
        m_chat = id
        await ctx.send("Теперь это master channel")
    elif s_chat == None and id != m_chat:
        s_chat = id
        await ctx.send("Теперь это slave channel")
    else: await ctx.send("Недоступно")



@bot.command(aliases=["say"])
@check
async def say(ctx):
    await ctx.message.delete()
    await ctx.send(ctx.message.content[5:])

@bot.command()
async def get(ctx):
    message = ctx.message
    text = message.content[5:]
    await ctx.send(getattr(message.channel.guild,text))


@bot.command()
async def db(ctx):
    message = ctx.message
    text = message.content[4:]
    try:
        con = sqlite3.connect('./game.sqlite')
        cur = con.cursor()
        cur.execute(text)
        con.commit()
        result = cur.fetchall()
        con.close()
        await ctx.send(result)
    except Exception as e:
        await ctx.send(traceback.format_exc())


bot.run('ODczMTUzMTkwMjczNjEzOTI1.YQ0RRg.5FGM8mFVPvlJ3YTSs1bnG_Pduvo')
