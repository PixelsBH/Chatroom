import socket
import threading
import argparse
import os

class Server(threading.Thread):
    
    def __init__(self, host, port):
        super().__init__()
        self.clients = []
        self.host = host
        self.port = port
        
    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        
        sock.listen(1)
        print('Listening at', sock.getsockname())
        
        while True:
            sc, sockname = sock.accept()
            print(f'Accepted a new connection from {sc.getpeername()}')
            
            server_socket = ServerSocket(sc, self)
            server_socket.start()
            
            self.clients.append(server_socket)
            print(f'Ready to receive messages from {sc.getpeername()}')
    
    def broadcast(self, message, source_name):
        for client in self.clients:
            if client.name != source_name:
                client.send(f'{source_name} says: {message}')
                
    def remove_client(self, client):
        print(f'Removing client {client.name}')
        self.clients.remove(client)

class ServerSocket(threading.Thread):
    
    def __init__(self, sc, server):
        super().__init__()
        self.sc = sc
        self.server = server
        self.name = None
        
    def run(self):
        # First message received from client is the client's name
        self.name = self.sc.recv(1024).decode('ascii')
        print(f'{self.name} has joined the chat.')
        
        while True:
            message = self.sc.recv(1024).decode('ascii')
            if message:
                print(f'{self.name} says: {message}')
                self.server.broadcast(message, self.name)
            else:
                print(f'{self.name} has left the chat.')
                self.sc.close()
                self.server.remove_client(self)
                return
            
    def send(self, message):
        self.sc.sendall(message.encode('ascii'))

def run_server(server):
    while True:
        ipt = input('')
        if ipt == 'exit':
            print('Closing all connections...')
            for client in server.clients:
                client.sc.close()
            print('Shutting down the server...')
            os._exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Chatroom Server')
    parser.add_argument('host', help='Interface the server listens at')
    parser.add_argument('-p', metavar='PORT', type=int, default=1060, help='TCP port (default 1060)')
    
    args = parser.parse_args()
    
    server = Server(args.host, args.p)
    server.start()
    
    server_thread = threading.Thread(target=run_server, args=(server,))
    server_thread.start()
