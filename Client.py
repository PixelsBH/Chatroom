import socket
import threading
import argparse
import os
import sys
import tkinter as tk
from tkinter import simpledialog
import random

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
                    msg, color = message.split('#')
                    # Update the messages in the Listbox
                    self.messages.insert(tk.END, msg)
                    self.messages.itemconfig(tk.END, {'fg': f'#{color}'})  # Apply user's color to their messages
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
        
        # # Define a list of colors for user assignment
        # self.available_colors = ["#e57373", "#64b5f6", "#81c784", "#ffb74d", "#9575cd", "#f06292", "#4db6ac", "#ffd54f"]
        # self.user_color = None  # Will be assigned upon login

    def start(self):
        print(f'Trying to connect to {self.host}:{self.port}...')
        self.sock.connect((self.host, self.port))
        print(f'Successfully connected to {self.host}:{self.port}')
        
        # Assign a random color to the user
        # self.user_color = random.choice(self.available_colors)
        
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

        # if message:
        #     # Insert message in the user's color
        #     self.messages.insert(tk.END, f'{self.name}: {message}')
        #     self.messages.itemconfig(tk.END, {'fg': self.user_color})  # Apply user's color to their messages
        self.sock.sendall(message.encode('ascii'))

def show_login_dialog(client):
    while not client.name:  # Loop until a username is provided
        # Create a new window for the login dialog
        login_window = tk.Toplevel()
        login_window.title("Login")
        login_window.geometry("400x250")
        login_window.configure(bg='#20232a')
        login_window.resizable(False, False)

        # Center the window on the screen
        screen_width = login_window.winfo_screenwidth()
        screen_height = login_window.winfo_screenheight()
        x = (screen_width // 2) - (400 // 2)
        y = (screen_height // 2) - (250 // 2)
        login_window.geometry(f"+{x}+{y}")

        # Title Label
        title_label = tk.Label(
            login_window, 
            text="Welcome to Chatroom", 
            font=("Arial", 16, "bold"), 
            bg='#20232a', 
            fg='#61dafb'
        )
        title_label.pack(pady=(20, 10))

        # Username label
        username_label = tk.Label(
            login_window, 
            text="Enter Username:", 
            font=("Arial", 12), 
            bg='#20232a', 
            fg='#61dafb'
        )
        username_label.pack(pady=(10, 5))

        # Username Entry
        username_entry = tk.Entry(
            login_window, 
            font=("Arial", 12), 
            bg='#282c34', 
            fg='#61dafb', 
            insertbackground='#61dafb', 
            relief="flat",
            width=25,
            highlightthickness=2, 
            highlightbackground="#61dafb",
            justify="center"
        )
        username_entry.pack(pady=(0, 20))

        # Error label for empty username warning
        error_label = tk.Label(
            login_window, 
            text="", 
            font=("Arial", 10), 
            bg='#20232a'
        )
        error_label.pack()

        # Enter button function
        def enter_username():
            username = username_entry.get().strip()
            if username:
                client.name = username
                login_window.destroy()
            else:
                error_label.config(text="Username is required.", fg="red")

        # Enter Button
        enter_button = tk.Button(
            login_window, 
            text="Enter Chatroom", 
            command=enter_username, 
            bg='#61dafb', 
            fg='#20232a', 
            font=("Arial", 12, "bold"),
            activebackground='#29a6d9', 
            activeforeground='#ffffff',
            relief="flat", 
            padx=10, 
            pady=5
        )
        enter_button.pack(pady=(5, 10))

        # Focus on entry box and bind Enter key to submit
        username_entry.focus()
        login_window.bind('<Return>', lambda event: enter_username())
        login_window.grab_set()  # Ensures the dialog is modal

        # Wait until the login dialog is closed
        login_window.wait_window()



def main(host, port):
    client = Client(host, port)

    # Prompt for the username in a custom dialog box
    root = tk.Tk()
    root.withdraw()  # Hide the root window initially
    show_login_dialog(client)
    
    if not client.name:
        print("Username is required.")
        return
    
    # Initialize the main chat window after username is set
    root.deiconify()
    root.title('Chatroom')
    root.geometry('800x500')
    root.configure(bg='#20232a')

    fromMessage = tk.Frame(master=root, bg='#20232a', padx=10, pady=10)
    scrollBar = tk.Scrollbar(master=fromMessage, bg='#444B54', troughcolor='#20232a', highlightbackground='#444B54')
    global messages
    messages = tk.Listbox(
        master=fromMessage, 
        yscrollcommand=scrollBar.set, 
        bg='#282c34', 
        fg='#61dafb',  
        selectbackground='#444B54', 
        highlightbackground='#444B54', 
        font=("Arial", 12),
        relief=tk.FLAT,  
        borderwidth=0
    )
    
    scrollBar.pack(side=tk.RIGHT, fill=tk.Y)
    messages.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    client.messages = messages
    receive = client.start()
    receive.messages = messages
    fromMessage.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    fromEntry = tk.Frame(master=root, bg='#20232a', padx=10, pady=10)
    username_label = tk.Label(master=fromEntry, text=f'{client.name}:', fg='#61dafb', bg='#20232a', font=("Arial", 10, "bold"))
    username_label.pack(side=tk.LEFT, padx=5)
    
    textInput = tk.Entry(
        master=fromEntry,
        bg='#444B54',
        fg='#61dafb', 
        insertbackground='#61dafb',
        width=50,
        font=("Arial", 12),
        relief=tk.FLAT,  
        highlightthickness=2,
        highlightbackground='#61dafb'
    )
    textInput.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(5, 10), ipady=8)

    def on_focus_in(event):
        if textInput.get() == 'Enter your message here...':
            textInput.delete(0, tk.END)
            textInput.config(fg='#61dafb')

    textInput.insert(0, 'Enter your message here...')
    textInput.bind("<FocusIn>", on_focus_in)
    textInput.bind("<Return>", lambda x: client.send(textInput))
    
    sendButton = tk.Button(
        master=fromEntry,
        text='Send',
        command=lambda: client.send(textInput),
        bg='#61dafb',
        fg='#20232a',
        activebackground='#29a6d9',
        activeforeground='#ffffff',
        relief=tk.FLAT,
        font=("Arial", 10, "bold"),
        borderwidth=0,
        padx=10,
        pady=5
    )
    
    fromEntry.pack(fill=tk.X, expand=True)
    sendButton.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT, padx=10)
    
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
