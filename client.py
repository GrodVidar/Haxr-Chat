from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
from tkinter import *
from time import sleep
import sys
import os
import re
import requests
import json
from tkinter import font # om vi vill lägga till fonts, venne hur viktigt det är lmao


def restart(host, port, my_font, font_size):
    print("argv was", sys.argv)
    print("sys.executable was", sys.executable)
    print("restart now")
    if my_font.isspace() or my_font == '':
        my_font = 'a'
    os.execv(sys.executable, ['python', 'client.py', host, str(port), str(my_font), str(font_size)])


def update_online():
    clients_list.delete(0, END)
    clients_list.insert(END, "Online:")
    for client in CLIENTS:
        clients_list.insert(END, client)


def get_dad_joke():
    resp = requests.get("https://us-central1-dadsofunny.cloudfunctions.net/DadJokes/random/jokes")
    my_json = json.loads(resp.text)
    return my_json['setup'], my_json['punchline']


def receive():
    while True:
        try:
            message = client_socket.recv(BUFFSIZE).decode('utf-8')
            if message[0] == '!':
                print(f"appending {message[1:]}")
                CLIENTS.append(message[1:])
                update_online()
            elif 'Announcer' in message:
                if bool(re.search(r'\[(\w+)\]', message)):
                    client = re.search(r'\[(\w+)\]', message)
                    CLIENTS.append(client.group(1))
                    update_online()
                elif bool(re.search(r'\((\w+)\)', message)):
                    client = re.search(r'\((\w+)\)', message)
                    print(f"delete {client.group(1)}")
                    if str(client.group(1)) in CLIENTS:
                        clients_list.delete(CLIENTS.index(client.group(1))+1)
                        CLIENTS.remove(client.group(1))
                        update_online()
            elif 'quit()' in message:
                update_online()
            if message[0] != '!':
                message_list.insert(END, message)
                message_list.see(END)
        except OSError:
            break


def send(event=None):
    message = my_message.get()
    message2 = ''
    if my_message.get() == "!dad":
        (message, message2) = get_dad_joke()
    my_message.set("")  # Clears input field.
    try:
        client_socket.send(bytes(message, "utf-8"))
        if message2 != '':
            client_socket.send(bytes(message2, "utf-8"))
    except ConnectionResetError:
        message_list.insert(END, "Lost connection to Server, restarting...")
        sleep(3)
        restart(HOST, PORT, FONT, FONT_SIZE)
    if message == "quit()":
        client_socket.close()
        window.quit()


def on_closing(event=None):
    my_message.set("quit()")
    send()


def ask_for_host():
    host = input('Enter host: ')
    if not host:
        return '127.0.0.1'
    return host


def ask_for_port():
    port = input('Enter port: ')
    if not port:
        return 1234
    else:
        try:
            return int(port)
        except ValueError:
            return 1234


def ask_for_font():
    my_font = input('Enter desired font("CS") or leave blank for default: ')
    if not my_font or my_font != 'CS':
        print("no font/no known font entered setting default")
        return ''
    else:
        return 'Comic Sans MS'


def ask_for_font_size():
    font_size = input("Enter desired font-size:(5-25) ")
    try:
        if 5 <= int(font_size) <= 25:
            return int(font_size)
        else:
            print("Entered value out of range, setting default")
            return 15
    except ValueError:
        print("setting default font-size")
        return 15


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        try:
            HOST = sys.argv[1]
        except ValueError:
            HOST = input('Enter host: ')
            if not HOST:
                HOST = '127.0.0.1'
    else:
        HOST = ask_for_host()

    if len(sys.argv) >= 3:
        try:
            PORT = int(sys.argv[2])
        except ValueError:
            PORT = input('Enter port: ')
            if not PORT:
                PORT = 1234
            else:
                try:
                    PORT = int(PORT)
                except ValueError:
                    PORT = 1234
    else:
        PORT = ask_for_port()

    if len(sys.argv) >= 4:
        if sys.argv[3] != 'CS':
            FONT = ''
        else:
            FONT = 'Comic Sans MS'
    else:
        FONT = ask_for_font()

    if len(sys.argv) >= 5:
        try:
            if 5 <= int(sys.argv[4]) <= 25:
                FONT_SIZE = int(sys.argv[4])
            else:
                print("Font-value out of range, setting default")
                FONT_SIZE = 15
        except ValueError:
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
    else:
        FONT_SIZE = ask_for_font_size()

    CLIENTS = []
    window = Tk()
    window.title("Haxr-Chat")
    window.configure(background="black")
    top_frame = Frame(window, bg="black")
    top_frame.pack()
    bottom_frame = Frame(window, bg="black")
    bottom_frame.pack(side=BOTTOM)
    my_message = StringVar()

    clients_list = Listbox(top_frame, height=15, width=10, bg="black", fg="green", selectbackground="green", selectforeground="black", font=(FONT, FONT_SIZE))
    message_list = Listbox(top_frame, height=25, width=90, bg="black", fg="green", selectbackground="green", selectforeground="black", font=(FONT, FONT_SIZE))
    clients_list.pack(side=LEFT)
    message_list.pack(side=RIGHT)
    clients_list.pack()
    message_list.pack()

    entry_field = Entry(bottom_frame, textvariable=my_message, bg="black", fg="green", selectbackground="green", selectforeground="black")
    entry_field.bind("<Return>", send)
    entry_field.focus()
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
    receive_thread.daemon = True
    receive_thread.start()
    mainloop()