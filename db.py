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

def init(server_id, admin_id, master_id, slave_id):
    insert(f"INSERT INTO servers (id, admin_chat_id, master_chat_id, slave_chat_id) \
            VALUES ({server_id}, {admin_id}, {master_id}, {slave_id})")

def get_chats(server_id):
    data = (*get(f"SELECT * FROM servers WHERE id = {server_id}"), [None]*4)[0]
    return {"admin": data[1], "master": data[2], "slave": data[3]}

def wipe(server_id):
    insert(f"DELETE FROM servers WHERE id = {server_id}")
