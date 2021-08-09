from PIL import ImageDraw, Image, ImageFont
from random import randint
from io import BytesIO

from discord.ext.commands.converter import TextChannelConverter

def centered_table(w, h, txt):
    txtbox = Image.new('RGB', (w, h), 'white')
    drawtxt = ImageDraw.Draw(txtbox)
    drawtxt.rectangle((0,0,w-1,h-1), outline=1)
    font = ImageFont.truetype('arial.ttf', 18)
    wt, ht = drawtxt.textsize(txt, font=font)
    drawtxt.text(((w-wt)//2,(h-ht)//2), txt, font=font, fill="black")
    return txtbox

def load_map(players_data, env_data):
    sz = env_data['size'] + 1
    map = [[-1 for i in range(sz - 1)] for i in range(18)]
    for x in players_data:
        pos = x['pos'].split(':')
        map[int(pos[0]) - 1][int(pos[1]) - 1] = 1
    rectSize = 40
    w = sz * rectSize + 1
    h = sz * rectSize + 1
    img = Image.new('RGB', (w, h), 'white')
    draw = ImageDraw.Draw(img)
    fpx, fpy = 0, rectSize
    font = ImageFont.truetype('arial.ttf', 20)
    lit = 'A'
    draw.rectangle([0, 0, rectSize, rectSize], outline=1)
    for i in range(sz):
        draw.rectangle([fpx, fpy, fpx+rectSize, fpy+rectSize], outline=1)
        draw.text((fpx + rectSize // 4, fpy + rectSize // 4), lit, font=font, fill='black')
        fpy += rectSize
        lit = chr(ord(lit) + 1)
    lit = 1
    fpx, fpy = rectSize, 0
    for i in range(sz):
        draw.rectangle([fpx, fpy, fpx+rectSize, fpy+rectSize], outline=1)
        draw.text((fpx + rectSize // 4, fpy + rectSize // 4), str(lit), font=font, fill='black')
        fpx += rectSize
        lit += 1
    fpx, fpy = rectSize, rectSize
    for i in range(sz - 1):
        for j in range(sz - 1):
            if (map[i][j] == -1):
                draw.rectangle([fpx, fpy, fpx+rectSize, fpy+rectSize], outline=1)
            else:
                r, g, b = randint(0, 255), randint(0, 255), randint(0, 255)
                draw.rectangle([fpx, fpy, fpx+rectSize, fpy+rectSize], fill=(r, g, b), outline=1)
                draw.text((fpx + rectSize // 4, fpy + rectSize // 4), 'P', font=font)
            fpx += rectSize
        fpx = rectSize
        fpy += rectSize
    widthes = [30*14, 30*4-30, 30*2-4, 30*5+6, 30*5-2]
    table = Image.new('RGB', (1000, (sz-1) * 40 + 1), 'white')
    tableHeight = 18 * 40 + 1 // 3
    fpx, fpy = 0, 0
    table.paste(centered_table(widthes[0], 32, 'Игрок'), (fpx, fpy))
    fpx += 30 * 14 - 1
    table.paste(centered_table(widthes[1], 32, 'Здоровье'), (fpx, fpy))
    fpx += 30*4-30 - 1
    table.paste(centered_table(widthes[2], 32, 'ОД'), (fpx, fpy))
    fpx += 30 * 2 - 4 - 1
    table.paste(centered_table(widthes[3], 32, 'Получил помощи'), (fpx, fpy))
    fpx += 30 * 5 + 6 - 1
    table.paste(centered_table(widthes[4], 32, 'Оказал помощи'), (fpx, fpy))
    fpx += 30 * 5 - 2 - 1
    table.paste(centered_table(1000 - fpx, 32, 'Нанес урона'), (fpx, fpy))
    widthes.append(1000 - fpx)
    fpy += 32
    fpx = 0
    for p in players_data:
        i = 0
        for x in p:
            if x not in ["id", "pos"]:
                table.paste(centered_table(widthes[i], 32, str(p[x])), (fpx, fpy))
                fpx += widthes[i]
                i += 1
        fpx, i = 0, 0
        fpy += 32
    ret = Image.new('RGB', (img.width + table.width, max(img.height, table.height)), (0,0,0))
    ret.paste(img, (0, 0))
    ret.paste(table, (img.width, 0))

    buffer = BytesIO()
    ret.save(buffer,format="PNG")
    buffer.seek(0)

    return buffer