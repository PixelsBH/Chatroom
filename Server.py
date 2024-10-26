import socket

HOST = '127.0.0.1'
PORT = 12345

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

print("Server is listening...")

client_socket, client_address = server.accept()
print(f"Connected to {client_address}")

client_socket.send("Hello from the server!".encode('utf-8'))
message = client_socket.recv(1024).decode('utf-8')
print("Received from client:", message)

client_socket.close()
server.close()
