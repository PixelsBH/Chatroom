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
            print('Accepted a new connection from {} to {}'.format(sc.getpeername(), sc.getsockname()))
            
            server_socket = ServerSocket(sc, sockname, self)
            server_socket.start()
            
            self.clients.append(server_socket)
            print('Ready to receive messages from', sc.getpeername())
    
    def broadcast(self, message, source):
        for client in self.clients:
            if client.sockname != source:
                client.send('{}: {!r}'.format(source, message))
                
    def remove_client(self, client):
        print('Removing client', client.sockname)
        self.clients.remove(client)
        
        
class ServerSocket(threading.Thread):
    
    def __init__(self, sc, sockname, server):
        super().__init__()
        self.sc = sc
        self.sockname = sockname
        self.server = server
        
    def run(self):
        while True:
            message = self.sc.recv(1024).decode('ascii')
            if message:
                print('{} says {!r}'.format(self.sockname, message))
                self.server.broadcast(message, self.sockname)
            else:
                print('{} has closed the connection'.format(self.sockname))
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
            break
        
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Chatroom Server')
    parser.add_argument('host', help='Interface the server listens at')
    parser.add_argument('-p', metavar='PORT', type=int, default=1060, help='TCP port (default 1060)')
    
    args = parser.parse_args()
    
    server = Server(args.host, args.p)
    server.start()
    
    server_thread = threading.Thread(target=run_server, args=(server,))
    server_thread.start()
    