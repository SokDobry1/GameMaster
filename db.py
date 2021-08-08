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





def add_player(name, discord_id, server_id): # Добавляет пользователя в зал ожидания
    insert(f"INSERT INTO players (name, discord_id, server_id) VALUES ({name!r}, {discord_id}, {server_id})")


def get_all_players(server_id): # Все пользователи в зале ожидания
    data = get(f"SELECT * FROM players WHERE server_id = {server_id}")
    return [{"id": i[0], "name": i[1], "discord_id": i[2], "server_id": i[3]} for i in data]


def global_get_gboard_players():
    players = get(f"SELECT * FROM gboard_players")
    return [{"id": data[0], "name": data[1], "pos": data[2], "hp": data[3], "points": data[4], 
            "recive_points": data[5], "send_points": data[6], "damage": data[7]} 
            for data in players]


def get_player_id(discord_id, server_id):
    return [*get(f"SELECT id FROM players WHERE discord_id = {discord_id} and \
                 server_id = {server_id}"), (None,)][0][0]


def get_player_by_id(id):
    data = [*get(f"SELECT * FROM players WHERE id = {id}"), [None]*4][0]
    return {"id": data[0], "name": data[1], "discord_id": data[2], "server_id": data[3]}


def remove_player(discord_id, server_id):
    id = get_player_id(discord_id, server_id)
    insert(f"DELETE FROM gboard_ghosts_requests WHERE player_id = {id}")
    insert(f"DELETE FROM gboard_players WHERE id = {id}")
    insert(f"DELETE FROM players WHERE discord_id = {discord_id} and server_id = {server_id}")





def add_players_on_gboard(server_id):
    players = get(f"SELECT id, name FROM players WHERE server_id = {server_id}")
    board_size = 18 #get(f"SELECT size")
    pos_x = randint(1, board_size); pos_y = randint(1, board_size)
    for player in players:
        while len(get(f"SELECT id FROM gboard_players WhERE pos = '{pos_x}:{pos_y}'")):
            pos_x = randint(1, board_size); pos_y = randint(1, board_size)
        insert(f"INSERT INTO gboard_players (id, name, pos, hp, points) VALUES \
                ({player[0]}, {player[1]!r}, '{pos_x}:{pos_y}', 3, 1)")

def clear_all_ghosts_requests(): pass

def clear_gboard(server_id):
    clear_all_ghosts_requests(server_id)
    players = get(f"SELECT id FROM players WHERE server_id = {server_id}")
    for player in players: insert(f"DELETE FROM gboard_players WHERE id = {player[0]}")


def isGameStarted(server_id):
    p0 = [*get(f"SELECT id FROM players WHERE server_id = {server_id}"), (None,)][0][0]
    if p0 and len(get(f"SELECT * FROM gboard_players WhERE id = {p0}")):
        return True
    return False






def get_gboard_player(discord_id, server_id):
    id = get_player_id(discord_id, server_id)
    if id == None: data = [None]*8
    else: data = get(f"SELECT * FROM gboard_players WHERE id = {id}")[0]
    return {"id": data[0], "name": data[1], "pos": data[2], "hp": data[3], "points": data[4], 
            "recive_points": data[5], "send_points": data[6], "damage": data[7]}


def get_all_gboard_players(server_id): # Данные о всех играющих пользователях на данном сервере
    gboard_players = []
    players = get(f"SELECT id FROM players WHERE server_id = {server_id}")
    for player in players:
        temp = get(f"SELECT * FROM gboard_players WHERE id = {player[0]}")[0]
        if len(temp): gboard_players += [temp]

    return [{"id": data[0], "name": data[1], "pos": data[2], "hp": data[3], "points": data[4], 
            "recive_points": data[5], "send_points": data[6], "damage": data[7]} 
            for data in gboard_players]


def update_gboard_player(data):
    insert(f"UPDATE gboard_players SET pos = {data['pos']!r}, hp =  {data['hp']}, points =  {data['points']}, \
             recive_points =  {data['recive_points']}, send_points =  {data['send_points']}, damage =  {data['damage']} \
             WHERE id = {data['id']}")


def can_step(server_id, pos):
    board_size = 18
    x, y = [int(i) for i in pos.split(":")]
    if x > board_size or y > board_size: return False

    on_pos = get(f"SELECT id FROM gboard_players WHERE pos = {pos!r}")
    on_board = get(f"SELECT id FROM players WHERE server_id = {server_id}")
    if all([i not in on_pos for i in on_board]): return True
    return False



def global_clear_ghosts_requests():
    insert("DELETE FROM gboard_ghosts_requests")

def clear_all_ghosts_requests(server_id):
    insert(f"DELETE FROM gboard_ghosts_requests WHERE server_id = {server_id}")

def get_all_gboard_ghosts(server_id):
    return [i[0] for i in get(f"SELECT id FROM gboard_players WHERE hp = 0")]


def make_ghost_request(discord_id, server_id, _type, data):
    id = get_player_id(discord_id, server_id)
    insert(f"INSERT INTO gboard_ghosts_requests (player_id, server_id, type, data)\
            VALUES ({id}, {server_id}, {_type!r}, {data!r})")


def get_equal_ghosts_requests(server_id, _type, data):
    return [i[0] for i in get(f"SELECT player_id FROM gboard_ghosts_requests WHERE \
                                server_id = {server_id} and type = {_type!r} and data = {data!r}")]


def isGhostCanMakeRequest(discord_id, server_id):
    id = get_player_id(discord_id, server_id)
    if id:
        if not len(get(f"SELECT player_id FROM gboard_ghosts_requests WHERE player_id = {id}")):
            return True
    return False

