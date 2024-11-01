import socket
import threading
import argparse
import os
import sys
import tkinter as tk

class Send(threading.Thread):
    
    def __init__(self, sock, name):
        super().__init__()
        self.sock = sock
        self.name = name
        self.running = True
        
    def run(self):
        while self.running:
            sys.stdout.flush()
            message = sys.stdin.readline()[:-1]
            if message.lower() == 'exit':
                self.running = False
                self.sock.close()
                os._exit(0)
                break
            self.sock.sendall(message.encode('ascii'))
            
            

class Recieve(threading.Thread):
        
    def __init__(self, sock, name):
        super().__init__()
        self.sock = sock
        self.name = name
        self.messages = None
        self.running = True
        
    def run(self):
        while self.running:
            message = self.sock.recv(1024).decode('ascii')
            if message:
                if self.messages:
                    self.messages.insert(tk.END, message)
                    print('\r{}\n{}: '.format(message, self.name), end = '')
            else:
                print('Server has closed the connection')
                self.sock.close()
                os._exit(0)
                break
            
            
class Client:
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.name = None
        self.messages = None
        self.gui = None
        
    def start(self):
        print('Trying to connect to {}:{}...'.format(self.host, self.port))
        self.sock.connect((self.host, self.port))
        print('Successfully connected to {}:{}'.format(self.host, self.port))
        
        self.name = input('Your name: ')
        self.sock.sendall(self.name.encode('ascii'))
        
        send = Send(self.sock, self.name)
        recieve = Recieve(self.sock, self.name)
        
        send.start()
        recieve.start()
        
        
        return recieve
        
        # send.join()
        # recieve.join()
        
        # self.sock.close()
        
    def send(self, text):
        message = text.get()
        text.delete(0, tk.END)
        
        if text == 'exit':
            self.sock.sendall('exit'.encode('ascii'))
            self.sock.close()
            os._exit(0)
            return
            
        if self.messages:
            self.messages.insert(tk.END, '{}: {}'.format(self.name, message))
        self.sock.sendall(message.encode('ascii'))
        
        

def main(host, port):
    client = Client(host, port)
    recieve = client.start()
    
    root = tk.Tk()
    root.title('Chatroom')
    
    fromMessage = tk.Frame(master=root)
    scrollBar = tk.Scrollbar(master=fromMessage)
    messages = tk.Listbox(master=fromMessage, yscrollcommand=scrollBar.set)
    
    scrollBar.pack(side=tk.RIGHT, fill=tk.Y, expand=False)
    messages.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # client.messages = messages
    # recieve.messages = messages
    # client.gui = root
    
    # fromMessage.grid(row=0, column=0, columnspan=2, sticky='nsew')
    fromMessage.pack(fill=tk.BOTH, expand=True)
    fromEntry = tk.Frame(master=root)
    textInput = tk.Entry(master=fromEntry)
    textInput.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
    textInput.bind("<Return>", lambda x: client.send(textInput))
    textInput.insert(0, 'Enter your message here...')
    
    sendButton = tk.Button(master=root, text='Send', command=lambda: client.send(textInput))
    
    
    # fromEntry.grid(row=1, column=0, padx=10,sticky='ew')
    # sendButton.grid(row=1, column=0, pady=10,sticky='ew')
    fromEntry.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
    sendButton.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
    
    root.rowconfigure(0, minsize=500, weight=1)
    root.rowconfigure(1, minsize=50, weight=0)
    root.columnconfigure(0, minsize=500, weight=1)
    root.columnconfigure(1, minsize=50, weight=0)
    root.mainloop()
    
    # recieve.join()
    
    
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Chatroom Server')
    parser.add_argument('host', help='Interface the server listens at')
    parser.add_argument('-p', metavar='PORT', type=int, default=1060, help='TCP port (default 1060)')
    
    args = parser.parse_args()
    main(args.host, args.p)
        
        