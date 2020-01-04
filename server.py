import socket
import threading
import sys

clients = {}
addresses = {}

HOST = ''
PORT = 1234
BUFFSIZE = 1024
SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER.bind((HOST, PORT))


def broadcast(message, prefix=''):
    for s in clients:
        s.send(bytes(prefix, 'utf-8')+message)


def handler(client):
    name = client.recv(BUFFSIZE).decode('utf-8')
    client.send(bytes("welcome %s, to quit type quit()" % name, 'utf-8'))
    broadcast(bytes(f"{name} has joined the chat!", 'utf-8'))
    clients[client] = name
    while True:
        message = client.recv(BUFFSIZE)
        if message != bytes("{quit}", 'utf-8'):
            broadcast(message, name+': ')
        else:
            print("quitting.")
            client.close()
            del clients[client]
            broadcast(bytes(f"{name} has left the chat.", 'utf-8'))
            break


def accept_connections():
    while True:
        client, client_address = SERVER.accept()
        print("%s:%s connected." % client_address)
        client.send(bytes("Enter Username: ", 'utf-8'))
        addresses[client] = client_address
        threading.Thread(target=handler, args=(client,)).start()


if __name__ == "__main__":
    SERVER.listen(5)
    print("Awaiting connections...")
    ACCEPT_THREAD = threading.Thread(target=accept_connections)
    ACCEPT_THREAD.start()
    ACCEPT_THREAD.join()
    SERVER.close()
