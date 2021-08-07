import sqlite3

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


def init(server_id, admin_id, master_id, slave_id): # Вносит id чатов взаимодействия
    insert(f"INSERT INTO servers (id, admin_chat_id, master_chat_id, slave_chat_id) \
            VALUES ({server_id}, {admin_id}, {master_id}, {slave_id})")

def get_chats(server_id): # Получает id чатов взаимодействия
    data = (*get(f"SELECT * FROM servers WHERE id = {server_id}"), [None]*4)[0]
    return {"admin": data[1], "master": data[2], "slave": data[3]}

def wipe(server_id): #Удаляет все данные о сервере
    insert(f"DELETE FROM players WHERE server_id = {server_id}")
    insert(f"DELETE FROM servers WHERE id = {server_id}")



def add_player(discord_id, server_id):
    insert(f"INSERT INTO players (discord_id, server_id) VALUES ({discord_id}, {server_id})")

def get_player_id(discord_id, server_id):
    return [*get(f"SELECT id FROM players WHERE discord_id = {discord_id} and \
                 server_id = {server_id}"), (None,)][0][0]

def remove_player(discord_id, server_id):
    insert(f"DELETE FROM players WHERE discord_id = {discord_id} and server_id = {server_id}")