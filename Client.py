import socket
import threading
import argparse
import os
import sys
import tkinter as tk
from tkinter import simpledialog

class Send(threading.Thread):
    
    def __init__(self, sock, name):
        super().__init__()
        self.sock = sock
        self.name = name
        self.running = True
        
    def run(self):
        # Send the name once, right after connecting
        self.sock.sendall(self.name.encode('ascii'))
        while self.running:
            sys.stdout.flush()
            message = sys.stdin.readline()[:-1]
            if message.lower() == 'exit':
                self.running = False
                self.sock.close()
                os._exit(0)
                break
            self.sock.sendall(message.encode('ascii'))

class Receive(threading.Thread):
    
    def __init__(self, sock, messages):
        super().__init__()
        self.sock = sock
        self.messages = messages
        self.running = True
        
    def run(self):
        while self.running:
            try:
                message = self.sock.recv(1024).decode('ascii')
                if message:
                    # Update the messages in the Listbox
                    self.messages.insert(tk.END, message)
                    print(message)
                else:
                    print('Server has closed the connection')
                    self.sock.close()
                    os._exit(0)
                    break
            except OSError:
                break

class Client:
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.name = None
        self.messages = None
        
    def start(self):
        print(f'Trying to connect to {self.host}:{self.port}...')
        self.sock.connect((self.host, self.port))
        print(f'Successfully connected to {self.host}:{self.port}')
        
        # Start Send and Receive threads after getting name from GUI
        send = Send(self.sock, self.name)
        receive = Receive(self.sock, self.messages)
        
        send.start()
        receive.start()
        
        return receive

    def send(self, text):
        message = text.get()
        text.delete(0, tk.END)
        
        if message.lower() == 'exit':
            self.sock.sendall('exit'.encode('ascii'))
            self.sock.close()
            os._exit(0)
            return

        if self.messages:
            self.messages.insert(tk.END, f'{self.name}: {message}')
        self.sock.sendall(message.encode('ascii'))

def main(host, port):
    client = Client(host, port)

    # Prompt for the username in a custom dialog box
    root = tk.Tk()
    root.withdraw()  # Hide the root window initially
    client.name = simpledialog.askstring("Username", "Please enter your username:")
    
    if not client.name:
        print("Username is required.")
        return
    
    # Initialize the main chat window after username is set
    root.deiconify()  # Show the main window
    root.title('Chatroom')
    root.geometry('800x500')  # Set window size to 800x500
    root.configure(bg='black')  # Set background to black

    # Create message display area
    fromMessage = tk.Frame(master=root, bg='black')
    scrollBar = tk.Scrollbar(master=fromMessage, bg='black', troughcolor='black')
    messages = tk.Listbox(
        master=fromMessage, 
        yscrollcommand=scrollBar.set, 
        bg='black', 
        fg='white', 
        selectbackground='gray', 
        highlightbackground='black', 
        highlightcolor='black'
    )
    
    scrollBar.pack(side=tk.RIGHT, fill=tk.Y, expand=False)
    messages.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Pass messages Listbox to the client and receive threads
    client.messages = messages
    receive = client.start()
    receive.messages = messages
    
    fromMessage.pack(fill=tk.BOTH, expand=True)
    
    # Message input area with username display
    fromEntry = tk.Frame(master=root, bg='black')
    username_label = tk.Label(master=fromEntry, text=f'{client.name}:', fg='white', bg='black')
    username_label.pack(side=tk.LEFT, padx=5)
    
    textInput = tk.Entry(master=fromEntry, bg='black', fg='white', insertbackground='white', width=60)
    textInput.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(5, 0), ipady=8)  # Set ipady to make it taller

    # Remove placeholder text on focus
    def on_focus_in(event):
        if textInput.get() == 'Enter your message here...':
            textInput.delete(0, tk.END)
            textInput.config(fg='white')

    textInput.insert(0, 'Enter your message here...')
    textInput.bind("<FocusIn>", on_focus_in)
    textInput.bind("<Return>", lambda x: client.send(textInput))
    
    sendButton = tk.Button(master=root, text='Send', command=lambda: client.send(textInput), bg='gray', fg='black')
    fromEntry.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
    sendButton.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
    
    root.rowconfigure(0, minsize=500, weight=1)
    root.rowconfigure(1, minsize=50, weight=0)
    root.columnconfigure(0, minsize=500, weight=1)
    root.columnconfigure(1, minsize=50, weight=0)
    root.mainloop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Chatroom Client')
    parser.add_argument('host', help='Interface the server listens at')
    parser.add_argument('-p', metavar='PORT', type=int, default=1060, help='TCP port (default 1060)')
    
    args = parser.parse_args()
    main(args.host, args.p)
