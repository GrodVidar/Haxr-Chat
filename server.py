import socket
import threading
from datetime import date, datetime
import sys
import os
import sqlite3
import requests
import json
from time import sleep
from kryp import dekryp


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
    db_cursor.execute(f"CREATE TABLE IF NOT EXISTS {today.strftime('%B_%d_%Y')}(date TEXT, user TEXT, message TEXT)")


def data_entry_messages(today, date_format, user, message):
    db_cursor.execute(f"INSERT INTO {today.strftime('%B_%d_%Y')}(date, user, message) VALUES (?, ?, ?)",
                      (date_format, user, message))
    db_connection.commit()


def create_table_clients():
    try:
        db_cursor.execute("CREATE TABLE IF NOT EXISTS clients (users TEXT)")
    except sqlite3.ProgrammingError as w:
        print(w)


def data_entry_clients(user):
    if user != 'quit()':
        db_cursor.execute("INSERT INTO clients(users) VALUES(?)", (user,))
        db_connection.commit()


def delete_client(client, name):
    print(f"user {name} left.")
    client.close()
    del clients[client]
    del CLIENTS[CLIENTS.index(name)]
    broadcast(bytes(f"({name}) has left the chat.", 'utf-8'), 'Announcer: ', False)
    print(f"deleting: {name} from DB")
    db_cursor.execute("DELETE FROM clients WHERE users=(?)", (name,))
    db_connection.commit()


def broadcast(message, prefix='Unknown: ', save=True):
    today = date.today()
    create_table_messages(today)
    date_format = datetime.now().strftime('[%Y-%m-%d|%H:%M:%S]')
    if save:
        data_entry_messages(today, date_format, prefix, message.decode('utf-8'))
    for s in clients:
        s.send(bytes(date_format + ' ' + prefix, 'utf-8')+message)


def send_temp():
    sent_this_minute = True
    with open("key.txt", 'r') as file:
        key = file.readline()
        while True:
            if len(CLIENTS) > 0:
                if int(datetime.now().strftime('%M')) % 5 == 0 and not sent_this_minute:
                    resp = requests.get(f"https://api.openweathermap.org/data/2.5/weather?id=2673730&APPID={key}&units=metric")
                    my_json = json.loads(resp.text)
                    broadcast(bytes(f"the weather in {my_json['name']} is {my_json['main']['temp']} °C", 'utf-8'), 'Weather-announcer: ', False)
                    sent_this_minute = True
                elif int(datetime.now().strftime('%M')) % 5 != 0 and sent_this_minute:
                    sent_this_minute = False


def send_old_messages(client, day):
    date = day.split()[1]
    db_cursor.execute(f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{date}'")
    if db_cursor.fetchone()[0] == 1:
        db_cursor.execute(f"SELECT * from {day.split()[1]}")
        for row in db_cursor.fetchall():
            if 'Announcer' not in row[1] and 'Weather-announcer' not in row[1]:
                try:
                    client.send(bytes(f"{row[0]} {row[1]}{row[2]}", 'utf-8'))
                    sleep(.07)
                except ConnectionResetError:
                    return
    else:
        client.send(bytes(f"{day.split()[1]} not found syntax: -d [fullmonthname_date_fullyear]", 'utf-8'))


def send_daily_messages_to_client(client):
    today = date.today()
    table = today.strftime('%B_%d_%Y')
    db_cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name=(?)", (table,))
    if db_cursor.fetchone()[0] == 1:
        db_cursor.execute(f"SELECT * from {table}")
        for row in db_cursor.fetchall():
            if 'Announcer' not in row[1] and 'Weather-announcer' not in row[1]:
                try:
                    client.send(bytes(f"{row[0]} {row[1]}{row[2]}", 'utf-8'))
                    sleep(.07)
                except ConnectionResetError:
                    return


def send_users_to_client(client):
    db_cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='clients'")
    if db_cursor.fetchone()[0] == 1:
        db_cursor.execute("SELECT users FROM clients")
        for row in db_cursor.fetchall():
            print(f"sending {row[0]} to client")
            client.send(bytes(f"!{row[0]}", 'utf-8'))
            sleep(.05)


def whisper(sender_sock, sender, my_message):
    print("whisper called")
    if my_message.split()[1] in CLIENTS:
        print("whisper client found")
        receiver = my_message.split()[1]
        message = my_message.split(' ', 2)[2]
        for client in clients:
            if clients[client] == receiver:
                sender_sock.send(bytes(f"you whisper: {message} to {my_message.split()[1]}", 'utf-8'))
                client.send(bytes(f"{sender} whispers: {message}", 'utf-8'))
                return
    else:
        sender_sock.send(bytes(f"{my_message.split()[1]} not recognized, /w syntax: /w [recipient_name] [message]", 'utf-8'))


def handler(client, name):
    try:
        CLIENTS.append(name)
        create_table_clients()
        data_entry_clients(name)
        send_users_to_client(client)
        send_daily_messages_to_client(client)
        client.send(bytes("welcome %s, to quit type quit()" % name, 'utf-8'))
        broadcast(bytes(f"[{name}] has joined the chat!", 'utf-8'), 'Announcer: ', False)
        clients[client] = name
        while True:
            try:
                message = client.recv(BUFFSIZE)
            except ConnectionResetError:
                delete_client(client, name)
                break
            if message.decode('utf-8')[0] == '/':
                if message.decode('utf-8')[:2] == '/w':
                    whisper(client, name, message.decode('utf-8'))
                else:
                    client.send(bytes("/ command not recognized, working commands: /w(whisper)", 'utf-8'))
            elif message.decode('utf-8')[0] == '-':
                if message.decode('utf-8')[:2] == '-d':
                    str_message = message.decode('utf-8')
                    send_old_messages(client, str_message)
                else:
                    client.send(bytes("- command not recognized, working commands: -d(get old messages)", 'utf-8'))
            elif message.decode('utf-8')[0] == '!':
                if message.decode('utf-8')[:5] == '!anon':
                    filtered = message.decode('utf-8')[5:]
                    broadcast(bytes(filtered, 'utf-8'), name+': ', False)
                else:
                    client.send(bytes("! command not recognized, working commands: !anon(doesn't save message in db)", 'utf-8'))
            elif message != bytes("quit()", 'utf-8'):
                broadcast(message, name+': ')
            else:
                delete_client(client, name)
                break
    except ConnectionResetError:
        print("client disconnected")
        return
    except BrokenPipeError as e:
        print(e)
        return


def check_if_name_taken(username):
    db_cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='users'")
    if db_cursor.fetchone()[0] == 1:
        db_cursor.execute("SELECT username FROM users")
        if username in db_cursor.fetchall()[0]:
            return True
        else:
            return False
    else:
        return False


def create_user(client):
    name_given = False
    pass_given = False
    client.send(bytes("Please enter a username between 2 and 10 characters long", 'utf-8'))
    username = dekryp(client.recv(BUFFSIZE).decode('utf-8'))
    while not name_given:
        if 10 < len(username) or len(username) < 2 or check_if_name_taken(username):
            client.send(bytes("Username too short or already taken, please enter another", 'utf-8'))
            username = dekryp(client.recv(BUFFSIZE).decode('utf-8'))
        else:
            name_given = True
    client.send(bytes("Please enter a password longer than 3 chars", 'utf-8'))
    password = dekryp(client.recv(BUFFSIZE).decode('utf-8'))
    while not pass_given:
        if len(password) < 3:
            client.send(bytes("PASSWORD TOO WEAK, MORTAL!!! ENTER A STRONGER!", 'utf-8'))
            password = dekryp(client.recv(BUFFSIZE).decode('utf-8'))
        else:
            pass_given = True
    return username, password


def check_pass(user, password):
    db_cursor.execute("SELECT username, password FROM users")
    for row in db_cursor.fetchall():
        if row[0] == user:
            if row[1] == password:
                return True
            else:
                return False
        else:
            return False


def accept_connections():
    while True:
        logged_in = False
        client, client_address = SERVER.accept()
        print(f"[{datetime.now()}] %s:%s connected" % client_address)
        try:
            while not logged_in:
                client.send(bytes("Enter Username or -r to Register", 'utf-8'))
                username = dekryp(client.recv(BUFFSIZE).decode('utf-8'))
                print(username)
                if ',q' in username:
                    username, password = create_user(client)
                    db_cursor.execute("INSERT INTO users(username, password) VALUES(?, ?)", (username, password))
                    db_connection.commit()
                    logged_in = True
                else:
                    if check_if_name_taken(username):
                        client.send(bytes("Enter Password", 'utf-8'))
                        given_pass = dekryp(client.recv(BUFFSIZE).decode('utf-8'))
                        if check_pass(username, given_pass):
                            logged_in = True
                        else:
                            client.send(bytes("incorrect credentials!", 'utf-8'))
                    else:
                        client.send(bytes("Username not found", 'utf-8'))
            addresses[client] = client_address
            threading.Thread(target=handler, args=(client, username,)).start()
        except BrokenPipeError:
            client.close()


if __name__ == "__main__":
    CLIENTS = []
    clients = {}
    addresses = {}

    db_connection = sqlite3.connect('chat.db', check_same_thread=False)
    db_cursor = db_connection.cursor()

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
    db_cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='clients'")
    if db_cursor.fetchone()[0] == 1:
        db_cursor.execute("DROP TABLE clients")
    db_cursor.execute("CREATE TABLE IF NOT EXISTS users(username TEXT, password TEXT)")
    print("Awaiting connections...")
    ACCEPT_THREAD = threading.Thread(target=accept_connections)
    threading.Thread(target=send_temp).start()
    ACCEPT_THREAD.start()
    ACCEPT_THREAD.join()
    db_cursor.close()
    db_connection.close()
    SERVER.close()
