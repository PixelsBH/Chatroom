import asyncio
import websockets
import json
from database import DatabaseHandler
import platform

# Store connected clients with their user IDs
connected_clients = {}
db = DatabaseHandler()

# Add this function to broadcast user list updates
async def broadcast_user_list():
    all_users = db.get_all_users()
    user_list_message = json.dumps({
        'type': 'user_list',
        'users': [{'id': uid, 'username': uname} for uid, uname in all_users]
    })
    
    for client in connected_clients:
        try:
            await client.send(user_list_message)
        except websockets.exceptions.ConnectionClosed:
            continue

async def handle_client(websocket):
    user_id = None
    username = None
    try:
        # Handle authentication first
        auth_data = await websocket.recv()
        auth_info = json.loads(auth_data)
        
        if auth_info['action'] == 'register':
            success = db.register_user(auth_info['username'], auth_info['password'])
            if success:
                await websocket.send(json.dumps({
                    'type': 'auth_response',
                    'success': True,
                    'message': 'Registration successful'
                }))
            else:
                await websocket.send(json.dumps({
                    'type': 'auth_response',
                    'success': False,
                    'message': 'Username already exists'
                }))
                return
                
        elif auth_info['action'] == 'login':
            user_id = db.verify_user(auth_info['username'], auth_info['password'])
            if user_id:
                username = auth_info['username']
                connected_clients[websocket] = {
                    'user_id': user_id,
                    'username': username
                }
                
                # Send auth response
                await websocket.send(json.dumps({
                    'type': 'auth_response',
                    'success': True,
                    'message': 'Login successful'
                }))
                
                # Broadcast updated user list to all clients
                await broadcast_user_list()
                
                # Send list of all users
                all_users = db.get_all_users()
                await websocket.send(json.dumps({
                    'type': 'user_list',
                    'users': [{'id': uid, 'username': uname} for uid, uname in all_users]
                }))
                
                # Send recent global messages
                recent_messages = db.get_recent_messages()
                for msg in recent_messages:
                    await websocket.send(json.dumps({
                        'type': 'message',
                        'chat_type': 'global',
                        'username': msg[0],
                        'content': msg[1],
                        'timestamp': str(msg[2])
                    }))
                
                # Send recent DM history
                recent_dms = db.get_user_dm_history(user_id)
                for dm in recent_dms:
                    await websocket.send(json.dumps({
                        'type': 'message',
                        'chat_type': 'dm',
                        'username': dm[0],
                        'content': dm[1],
                        'timestamp': str(dm[2]),
                        'sender_id': dm[3],
                        'receiver_id': dm[4]
                    }))
            else:
                await websocket.send(json.dumps({
                    'type': 'auth_response',
                    'success': False,
                    'message': 'Invalid credentials'
                }))
                return

        # Handle messages
        async for message in websocket:
            if user_id:
                msg_data = json.loads(message)
                username = connected_clients[websocket]['username']
                
                if msg_data.get('receiver_id'):
                    # Handle DM
                    receiver_id = int(msg_data['receiver_id'])
                    db.save_message(user_id, msg_data['content'], receiver_id)
                    
                    message_data = {
                        'type': 'message',
                        'chat_type': 'dm',
                        'username': username,
                        'content': msg_data['content'],
                        'sender_id': user_id,
                        'receiver_id': receiver_id
                    }
                    
                    # Send to receiver if online
                    for client_socket, client_info in connected_clients.items():
                        if client_info['user_id'] == receiver_id:
                            await client_socket.send(json.dumps(message_data))
                            break
                    
                    # Send back to sender
                    await websocket.send(json.dumps(message_data))
                    
                else:
                    # Handle global message
                    db.save_message(user_id, msg_data['content'])
                    broadcast_message = json.dumps({
                        'type': 'message',
                        'chat_type': 'global',
                        'username': username,
                        'content': msg_data['content']
                    })
                    
                    # Broadcast to all except sender
                    for client_socket in connected_clients:
                        if client_socket != websocket:
                            try:
                                await client_socket.send(broadcast_message)
                            except websockets.exceptions.ConnectionClosed:
                                continue

    except websockets.exceptions.ConnectionClosed:
        if username:
            print(f"Client disconnected: {username}")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if websocket in connected_clients:
            del connected_clients[websocket]
            # Broadcast updated user list after disconnect
            await broadcast_user_list()

async def main():
    async with websockets.serve(handle_client, "localhost", 8765):
        print("WebSocket server starting on ws://localhost:8765")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    try:
        if platform.system() == 'Windows':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server shutting down...")
    except Exception as e:
        print(f"Server error: {str(e)}")
