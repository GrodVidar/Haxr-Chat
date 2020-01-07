import socket
import threading
from datetime import date, datetime
import sys
import os
import sqlite3
from time import sleep


def restart(port, my_clients):
    print("argv was", sys.argv)
    print("sys.executable was", sys.executable)
    print("restart now")
    os.execv(sys.executable, ['python', 'server.py', str(port), str(my_clients)])


def ask_for_port():
    port = input("enter port: ")
    try:
        port = int(port)
        return port
    except ValueError:
        print("invalid Port, setting to 1234")
        return 1234


def ask_for_max_clients():
    max_clients = input("Enter maximum amount of clients:(1-20) ")
    try:
        if 1 <= int(max_clients) <= 20:
            return int(max_clients)
        else:
            print("Value out of range, setting default: 5")
            return 5
    except ValueError:
        print("Value not valid, setting default: 5")
        return 5


def create_table_messages(today):
    messages_cursor.execute(f"CREATE TABLE IF NOT EXISTS {today.strftime('%B_%d_%Y')}(date TEXT, user TEXT, message TEXT)")


def data_entry_messages(today, date_format, user, message):
    messages_cursor.execute(f"INSERT INTO {today.strftime('%B_%d_%Y')}(date, user, message) VALUES (?, ?, ?)",
                            (date_format, user, message))
    messages_connection.commit()


def create_table_clients():
    clients_cursor.execute("CREATE TABLE IF NOT EXISTS clients (users TEXT)")


def data_entry_clients(user):
    if user != 'quit()':
        clients_cursor.execute("INSERT INTO clients(users) VALUES(?)", (user,))
        clients_connection.commit()


def delete_client(client, name):
    print(f"user {name} left.")
    client.close()
    del clients[client]
    broadcast(bytes(f"({name}) has left the chat.", 'utf-8'), 'Announcer: ')
    print(f"deleting: {name} from DB")
    clients_cursor.execute("DELETE FROM clients WHERE users=(?)", (name,))
    clients_connection.commit()


def broadcast(message, prefix='Unknown: '):
    today = date.today()
    create_table_messages(today)
    date_format = datetime.now().strftime('[%Y-%m-%d|%H:%M:%S]')
    data_entry_messages(today, date_format, prefix, message.decode('utf-8'))
    for s in clients:
        s.send(bytes(date_format + ' ' + prefix, 'utf-8')+message)


def send_daily_to_client(client):
    today = date.today()
    table = today.strftime('%B_%d_%Y')
    messages_cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name=(?)", (table,))
    if messages_cursor.fetchone()[0] == 1:
        messages_cursor.execute(f"SELECT * from {table}")
        for row in messages_cursor.fetchall():
            if 'Announcer' not in row[1]:
                try:
                    client.send(bytes(f"{row[0]} {row[1]}{row[2]}", 'utf-8'))
                    sleep(.05)
                except ConnectionResetError:
                    return


def send_users_to_client(client):
    clients_cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='clients'")
    if clients_cursor.fetchone()[0] == 1:
        clients_cursor.execute("SELECT users FROM clients")
        for row in clients_cursor.fetchall():
            print(f"sending {row[0]} to client")
            client.send(bytes(f"!{row[0]}", 'utf-8'))
            sleep(.05)


def whisper(my_message, receiver_client):
    pass


def handler(client):
    try:
        name = client.recv(BUFFSIZE).decode('utf-8')
        if len(name) == 1:
            client.send(bytes("name too short, setting name to Unknown", 'utf-8'))
            name = 'Unknown'
        CLIENTS.append(name)
        create_table_clients()
        data_entry_clients(name)
        send_users_to_client(client)
        send_daily_to_client(client)
        client.send(bytes("welcome %s, to quit type quit()" % name, 'utf-8'))
        broadcast(bytes(f"[{name}] has joined the chat!", 'utf-8'), 'Announcer: ')
        clients[client] = name
        while True:
            try:
                message = client.recv(BUFFSIZE)
                utf_message = bytes(message, 'utf-8')
            except ConnectionResetError:
                delete_client(client, name)
                break
            if message != bytes("quit()", 'utf-8'):
                broadcast(message, name+': ')
            elif utf_message[0] == '/' and (utf_message[1] == 'w' or utf_message[1] == 'W'):
                for names in clients:
                    print(names)
                if len(utf_message.split()) >= 3:
                    receiver_client = utf_message.split()[1]
                    if receiver_client in CLIENTS:
                        my_message = utf_message.split(' ', 2)[2]
                        whisper(receiver_client, my_message)

            else:
                delete_client(client, name)
                break
    except ConnectionResetError:
        print("client disconnected without giving a username. :(")
        return


def accept_connections():
    while True:
        client, client_address = SERVER.accept()
        print("%s:%s connected." % client_address)
        client.send(bytes("Enter Username: ", 'utf-8'))
        addresses[client] = client_address
        threading.Thread(target=handler, args=(client,)).start()


if __name__ == "__main__":
    CLIENTS = []
    clients = {}
    addresses = {}

    messages_connection = sqlite3.connect('chat.db', check_same_thread=False)
    messages_cursor = messages_connection.cursor()
    clients_connection = sqlite3.connect('online_users.db', check_same_thread=False)
    clients_cursor = clients_connection.cursor()

    HOST = ''
    if len(sys.argv) >= 2:
        try:
            PORT = int(sys.argv[1])
        except ValueError:
            PORT = input("enter port: ")
            try:
                PORT = int(PORT)
            except ValueError:
                print("invalid Port, setting to 1234")
                PORT = 1234
    else:
        PORT = ask_for_port()
    if len(sys.argv) >= 3:
        try:
            MAX_CLIENTS = int(sys.argv[2])
        except ValueError:
            MAX_CLIENTS = input("Enter maximum amount of clients:(1-20) ")
            try:
                if 1 <= int(MAX_CLIENTS) <= 20:
                    MAX_CLIENTS = int(MAX_CLIENTS)
                else:
                    print("Value out of range, setting default: 5")
                    MAX_CLIENTS = 5
            except ValueError:
                print("Value not valid, setting default: 5")
                MAX_CLIENTS = 5
    else:
        MAX_CLIENTS = ask_for_max_clients()

    BUFFSIZE = 1024
    SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SERVER.bind((HOST, PORT))

    SERVER.listen(MAX_CLIENTS)
    clients_cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='clients'")
    if clients_cursor.fetchone()[0] == 1:
        clients_cursor.execute("DROP TABLE clients")
    print("Awaiting connections...")
    ACCEPT_THREAD = threading.Thread(target=accept_connections)
    ACCEPT_THREAD.start()
    ACCEPT_THREAD.join()
    messages_cursor.close()
    messages_connection.close()
    SERVER.close()
