import socket
import threading
from datetime import date, datetime
import sys
import sqlite3


clients = {}
addresses = {}

messages_connection = sqlite3.connect('chat.db', check_same_thread=False)
messages_cursor = messages_connection.cursor()
clients_connection = sqlite3.connect('online_users.db', check_same_thread=False)
clients_cursor = clients_connection.cursor()


HOST = ''
PORT = input("enter port: ")
try:
    PORT = int(PORT)
except ValueError:
    print("invalid Port, setting to 1234")
    PORT = 1234

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

BUFFSIZE = 1024
SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER.bind((HOST, PORT))


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


def delete_client(name):
    print(f"deleting: {name} from DB")
    clients_cursor.execute("DELETE FROM clients WHERE users=(?)", (name,))
    clients_connection.commit()


def broadcast(message, prefix='Unknown: '):
    today = date.today()
    create_table_messages(today)
    # date_format = today.strftime("[%d %b-%y]")
    date_format = datetime.now().strftime('[%Y-%m-%d|%H:%M:%S]')
    data_entry_messages(today, date_format, prefix, message.decode('utf-8'))
    for s in clients:
        s.send(bytes(date_format + ' ' + prefix, 'utf-8')+message)


def handler(client):
    name = client.recv(BUFFSIZE).decode('utf-8')
    if len(name) == 1:
        client.send(bytes("name too short, setting name to Unknown", 'utf-8'))
        name = 'Unknown'
    create_table_clients()
    data_entry_clients(name)
    # TODO: for loopa igenom databasens table för att visa tidigare meddelanden för clienten ☺ så typ for message in db: client.send(bytes(f"{time} {name}: {message}"))
    client.send(bytes("welcome %s, to quit type quit()" % name, 'utf-8'))
    broadcast(bytes(f"[{name}] has joined the chat!", 'utf-8'), 'Announcer: ')
    clients[client] = name
    while True:
        message = client.recv(BUFFSIZE)
        if message != bytes("quit()", 'utf-8'):
            broadcast(message, name+': ')
        else:
            print("quitting.")
            client.close()
            del clients[client]
            broadcast(bytes(f"({name}) has left the chat.", 'utf-8'), 'Announcer: ')
            delete_client(name)
            break


def accept_connections():
    while True:
        client, client_address = SERVER.accept()
        print("%s:%s connected." % client_address)
        client.send(bytes("Enter Username: ", 'utf-8'))
        addresses[client] = client_address
        threading.Thread(target=handler, args=(client,)).start()


if __name__ == "__main__":

    SERVER.listen(MAX_CLIENTS)
    print("Awaiting connections...")
    ACCEPT_THREAD = threading.Thread(target=accept_connections)
    ACCEPT_THREAD.start()
    ACCEPT_THREAD.join()
    messages_cursor.close()
    messages_connection.close()
    SERVER.close()
