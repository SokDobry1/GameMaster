import sqlite3
from random import randint

def insert(request):
    con = sqlite3.connect('./game.sqlite')
    cur = con.cursor()
    cur.execute(request)
    con.commit()
    con.close()


def get(request):
    con = sqlite3.connect('./game.sqlite')
    cur = con.cursor()
    cur.execute(request)
    result = cur.fetchall()
    con.close()
    return result


def clear_gboard(): pass #Объявляю факт существования (функция ниже)




def init(server_id, admin_id, master_id, slave_id): # Вносит id чатов взаимодействия
    insert(f"INSERT INTO servers (id, admin_chat_id, master_chat_id, slave_chat_id) \
            VALUES ({server_id}, {admin_id}, {master_id}, {slave_id})")

def get_chats(server_id): # Получает id чатов взаимодействия
    data = (*get(f"SELECT * FROM servers WHERE id = {server_id}"), [None]*4)[0]
    return {"admin": data[1], "master": data[2], "slave": data[3]}

def wipe(server_id): #Удаляет все данные о сервере
    clear_gboard(server_id)
    insert(f"DELETE FROM players WHERE server_id = {server_id}")
    insert(f"DELETE FROM servers WHERE id = {server_id}")





def add_player(discord_id, server_id):
    insert(f"INSERT INTO players (discord_id, server_id) VALUES ({discord_id}, {server_id})")


def get_all_players(server_id):
    data = get(f"SELECT * FROM players WHERE server_id = {server_id}")
    return [{"id": i[0], "discord_id": i[1], "server_id": i[2]} for i in data]

def get_all_gboard_players(server_id):
    pass

def get_player_id(discord_id, server_id):
    return [*get(f"SELECT id FROM players WHERE discord_id = {discord_id} and \
                 server_id = {server_id}"), (None,)][0][0]

def remove_player(discord_id, server_id):
    id = get_player_id(discord_id, server_id)
    insert(f"DELETE FROM gboard_players WHERE id = {id}")
    insert(f"DELETE FROM players WHERE discord_id = {discord_id} and server_id = {server_id}")





def add_players_on_gboard(server_id):
    players = get(f"SELECT id FROM players WHERE server_id = {server_id}")
    size =  20 #get(f"SELECT size")
    pos_x = randint(0, size); pos_y = randint(0, size)
    for player in players:
        while len(get(f"SELECT id FROM gboard_players WhERE pos = '{pos_x}:{pos_y}'")):
            pos_x = randint(0, size); pos_y = randint(0, size)
        insert(f"INSERT INTO gboard_players (id, pos, hp, points) VALUES \
                ({player[0]}, '{pos_x}:{pos_y}', 3, 1)")


def clear_gboard(server_id):
    players = get(f"SELECT id FROM players WHERE server_id = {server_id}")
    for player in players: insert(f"DELETE FROM gboard_players WHERE id = {player[0]}")


def isGameStarted(server_id):
    p0 = [*get(f"SELECT id FROM players WHERE server_id = {server_id}"), (None,)][0][0]
    if p0 and len(get(f"SELECT * FROM gboard_players WhERE id = {p0}")):
        return True
    return False