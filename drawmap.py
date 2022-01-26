from PIL import ImageDraw, Image, ImageFont
from random import randint
from io import BytesIO
from db import get_player_by_id

from discord.ext.commands.converter import TextChannelConverter

def centered_table(w, h, txt, color):
    txtbox = Image.new('RGB', (w, h), color)
    drawtxt = ImageDraw.Draw(txtbox)
    drawtxt.rectangle((0,0,w-1,h-1), outline=1)
    font = ImageFont.truetype('./arial.ttf', 18)
    wt, ht = drawtxt.textsize(txt, font=font)
    drawtxt.text(((w-wt)//2,(h-ht)//2), txt, font=font, fill="black")
    return txtbox

def load_map(players_data, env_data):
    sz = env_data['size'] + 1
    map = [[-1 for i in range(sz - 1)] for i in range(sz - 1)]
    for x in players_data:
        if x['pos'] != '':
            pos = x['pos'].split(':')
            map[int(pos[1]) - 1][int(pos[0]) - 1] = x['id']
    rectSize = 40
    w = sz * rectSize + 1
    h = sz * rectSize + 1
    img = Image.new('RGB', (w, h), 'white')
    draw = ImageDraw.Draw(img)
    fpx, fpy = 0, rectSize
    font = ImageFont.truetype('./arial.ttf', 20)
    lit = 1
    draw.rectangle([0, 0, rectSize, rectSize], outline=1)
    for i in range(sz):
        draw.rectangle([fpx, fpy, fpx+rectSize, fpy+rectSize], outline=1)
        draw.text((fpx + rectSize // 4, fpy + rectSize // 4), str(lit), font=font, fill='black')
        fpy += rectSize
        lit += 1
    lit = 'A'
    fpx, fpy = rectSize, 0
    for i in range(sz):
        draw.rectangle([fpx, fpy, fpx+rectSize, fpy+rectSize], outline=1)
        draw.text((fpx + rectSize // 4, fpy + rectSize // 4), lit, font=font, fill='black')
        fpx += rectSize
        lit = chr(ord(lit) + 1)
    fpx, fpy = rectSize, rectSize
    colors = {}
    font = ImageFont.truetype('./arial.ttf', 16)
    for i in range(sz - 1):
        for j in range(sz - 1):
            if (map[i][j] == -1):
                draw.rectangle([fpx, fpy, fpx+rectSize, fpy+rectSize], outline=1)
            else:
                r, g, b = (int(str(map[i][j])[::-1]) * 1244 + 144) * 3 % 255, ((map[i][j] * 5352 + 42311) * 14221) % 255, ((map[i][j] * 1244 + 144) * 3) % 255
                draw.rectangle([fpx, fpy, fpx+rectSize, fpy+rectSize], fill=(r, g, b), outline=1)
                pl = get_player_by_id(str(map[i][j]))
                draw.text((fpx + 2, fpy + 6), pl['name'][0:3], font=font, stroke_width=1, stroke_fill='black')
                colors[map[i][j]] = (r, g, b)
            fpx += rectSize
        fpx = rectSize
        fpy += rectSize
    widthes = [30*14, 30*4-30, 30*2-4, 30*5+6, 30*5-2]
    table = Image.new('RGB', (1000, 32 * (len(players_data) + 1) - 2), 'white')
    fpx, fpy = 0, 0
    table.paste(centered_table(widthes[0], 32, 'Игрок', (255, 255, 255)), (fpx, fpy))
    fpx += 30 * 14 - 1
    table.paste(centered_table(widthes[1], 32, 'Здоровье', (255, 255, 255)), (fpx, fpy))
    fpx += 30*4-30 - 1
    table.paste(centered_table(widthes[2], 32, 'ОД', (255, 255, 255)), (fpx, fpy))
    fpx += 30 * 2 - 4 - 1
    table.paste(centered_table(widthes[3], 32, 'Получил помощи', (255, 255, 255)), (fpx, fpy))
    fpx += 30 * 5 + 6 - 1
    table.paste(centered_table(widthes[4], 32, 'Оказал помощи', (255, 255, 255)), (fpx, fpy))
    fpx += 30 * 5 - 2 - 1
    table.paste(centered_table(1000 - fpx, 32, 'Нанес урона', (255, 255, 255)), (fpx, fpy))
    widthes.append(1000 - fpx)
    fpy += 32
    fpx = 0
    for p in players_data:
        i = 0
        for x in p:
            if x not in ["id", "pos"] and p['pos'] != '':
                table.paste(centered_table(widthes[i], 32, str(p[x]), colors[p['id']]), (fpx, fpy))
                fpx += widthes[i] - 1
                i += 1
        fpx, i = 0, 0
        fpy += 32 - 1
    ret = Image.new('RGB', (img.width + table.width, max(img.height, table.height)), 'white')
    ret.paste(img, (0, 0))
    ret.paste(table, (img.width, 0))

    buffer = BytesIO()
    ret.save(buffer,format="PNG")
    buffer.seek(0)

    return buffer