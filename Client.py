import socket

HOST = '127.0.0.1'
PORT = 12345
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

message = client.recv(1024).decode('utf-8')
print("Received from server:", message)

client.send("Hello from the client!".encode('utf-8'))

client.close()
