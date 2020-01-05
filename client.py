from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
from tkinter import *
import re
import sqlite3
from tkinter import font


def update_online():
    clients_list.delete(0, END)
    clients_list.insert(END, "Online:")
    for client in CLIENTS:
        clients_list.insert(END, client)


def get_online_users():
    clients_connection = sqlite3.connect('online_users.db', check_same_thread=False)
    clients_cursor = clients_connection.cursor()
    clients_cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='clients'")
    if clients_cursor.fetchone()[0] == 1:
        clients_cursor.execute("SELECT users FROM clients")
        for row in clients_cursor.fetchall():
            if row[0] not in CLIENTS:
                print(f"adding {row[0]} to list")
                CLIENTS.append(row[0])
    clients_cursor.close()
    clients_connection.close()


def receive():
    while True:
        try:
            message = client_socket.recv(BUFFSIZE).decode('utf-8')
            if 'Announcer' in message:
                if bool(re.search(r'\[(\w+)\]', message)):
                    get_online_users()
                    update_online()
                elif bool(re.search(r'\((\w+)\)', message)):
                    client = re.search(r'\((\w+)\)', message)
                    print(f"delete {client.group(1)}")
                    if str(client.group(1)) in CLIENTS:
                        print("deleting")
                        clients_list.delete(CLIENTS.index(client.group(1))+1)
                        CLIENTS.remove(client.group(1))
                        update_online()
            elif 'quit()' in message:
                get_online_users()
                update_online()
            message_list.insert(END, message)
            message_list.see(END)
        except OSError:
            break


def send(event=None):
    message = my_message.get()
    my_message.set("")  # Clears input field.
    client_socket.send(bytes(message, "utf8"))
    if message == "quit()":
        # clients_cursor.close()
        # clients_connection.close()
        client_socket.close()
        window.quit()


def on_closing(event=None):
    my_message.set("quit()")
    send()


HOST = input('Enter host: ')
if not HOST:
    HOST = '127.0.0.1'
PORT = input('Enter port: ')
if not PORT:
    PORT = 1234
else:
    PORT = int(PORT)
FONT = input('Enter desired font("CS") or leave blank for default: ')
if not FONT or FONT != 'CS':
    print("no font/no known font entered setting default")
    FONT = ''
elif FONT == 'CS':
    FONT = 'Comic Sans MS'
FONT_SIZE = input("Enter desired font-size:(5-25) ")
try:
    if 5 <= int(FONT_SIZE) <= 25:
        FONT_SIZE = int(FONT_SIZE)
    else:
        print("Entered value out of range, setting default")
        FONT_SIZE = 15
except ValueError:
    print("setting default font-size")
    FONT_SIZE = 15


CLIENTS = []
window = Tk()
window.title("Haxr-Chat")
window.configure(background="black")
top_frame = Frame(window, bg="black")
top_frame.pack()
bottom_frame = Frame(window, bg="black")
bottom_frame.pack(side=BOTTOM)
my_message = StringVar()
get_online_users()

clients_list = Listbox(top_frame, height=15, width=10, bg="black", fg="green", selectbackground="green", selectforeground="black", font=(FONT, FONT_SIZE))
message_list = Listbox(top_frame, height=25, width=90, bg="black", fg="green", selectbackground="green", selectforeground="black", font=(FONT, FONT_SIZE))
clients_list.pack(side=LEFT)
message_list.pack(side=RIGHT)
clients_list.pack()
message_list.pack()

entry_field = Entry(bottom_frame, textvariable=my_message, bg="black", fg="green", selectbackground="green", selectforeground="black")
entry_field.bind("<Return>", send)
entry_field.pack()
send_button = Button(bottom_frame, text="Send", command=send)
send_button.pack()

clients_list.insert(END, "Online:")
if len(CLIENTS) > 0:
    update_online()


window.protocol("WM_DELETE_WINDOW", on_closing)

BUFFSIZE = 1024


client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect((HOST, PORT))

receive_thread = Thread(target=receive)
receive_thread.start()
mainloop()