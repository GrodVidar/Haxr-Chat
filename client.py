from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
from tkinter import *
from tkinter import font



def receive():
    while True:
        try:
            message = client_socket.recv(BUFFSIZE).decode('utf-8')
            message_list.insert(END, message)
            message_list.see(END)
        except OSError:
            break


def send(event=None):
    message = my_message.get()
    my_message.set("")  # Clears input field.
    client_socket.send(bytes(message, "utf8"))
    if message == "quit()":
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


window = Tk()
window.title("Haxr-Chat")
window.configure(background="black")
messages_frame = Frame(window, bg="black", bd=7)
my_message = StringVar()
#scrollbar = Scrollbar(messages_frame)

message_list = Listbox(messages_frame, height=25, width=90, bg="black", fg="green", selectbackground="green", selectforeground="black", font=(FONT, FONT_SIZE))
#scrollbar.pack(side=RIGHT, fill=Y)
message_list.pack(side=LEFT, fill=BOTH)
message_list.pack()
messages_frame.pack()

entry_field = Entry(window, textvariable=my_message, bg="black", fg="green", selectbackground="green", selectforeground="black")
entry_field.bind("<Return>", send)
entry_field.pack()
send_button = Button(window, text="Send", command=send)
send_button.pack()


window.protocol("WM_DELETE_WINDOW", on_closing)

BUFFSIZE = 1024


client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect((HOST, PORT))

receive_thread = Thread(target=receive)
receive_thread.start()
mainloop()