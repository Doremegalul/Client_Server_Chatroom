import socket
import json
import os
import threading
from datetime import datetime
# Directory where attachments will be saved
ATTACHMENTS_DIR = "attachments/"

if not os.path.exists(ATTACHMENTS_DIR):
    os.makedirs(ATTACHMENTS_DIR)

# List to track active client sockets
active_clients = [] 
# List to track active client addresses
active_addresses = [] 
# List to track chat history
messages = [] 

# # Handles communication with the client
def handle_client(client_socket, client_address):
    print(f"New connection from {client_address}")
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                try:
                    message_data = json.loads(message)
                    if message_data['ATTACHMENT_FLAG'] == 1:
                        # Handle file upload for attachment
                        handle_file_upload(client_socket, message_data)
                    elif message_data['REPORT_REQUEST_FLAG'] == 1:
                        # Handle report request for active client
                        handle_report_request(client_socket)
                    elif message_data['JOIN_REQUEST_FLAG'] == 1:
                        # Handle join request
                        handle_join_request(client_socket, client_address, message_data)
                    elif message_data['QUIT_REQUEST_FLAG'] == 1:
                        # Handle quit request
                        handle_quit_request(client_socket,message_data)
                        # Leave
                        break  
                    else:
                        # Handle general messages
                        handle_message(client_socket, message_data)
                except json.JSONDecodeError:
                    print("Received non-JSON message.")
            else:
                break
        except Exception as e:
            print(f"Error receiving message: {e}")
            break
    client_socket.close()

# Handle file uploads from the client
def handle_file_upload(client_socket, message_data):
    try:
        filename = message_data['FILENAME']
        username = message_data['USERNAME']
        # Decoding from latin1 as binary data
        file_content = message_data['PAYLOAD'].encode('latin1')  

        f = open(filename, "r")
        broadcast_message(f"[{datetime.now().strftime('%H:%M')}] {username}: {f.read()}")

        response_data = {
            'ATTACHMENT_FLAG': 1,
            'PAYLOAD': f"File {filename} uploaded successfully!"
        }
        client_socket.send(json.dumps(response_data).encode('utf-8'))
        print(f"File {filename} uploaded successfully.")
        
    except Exception as e:
        response_data = {
            'ATTACHMENT_FLAG': 0,
            'PAYLOAD': f"Error uploading file: {str(e)}"
        }
        client_socket.send(json.dumps(response_data).encode('utf-8'))
        print(f"Error uploading file: {str(e)}")

# Handle report of the active users
def handle_report_request(client_socket):
    # Get active users' usernames
    active_users = [username for _, username in active_clients]  
    user_list = ""
    for x in range(len(active_users)):
        user_list += f"{x+1}. {active_users[x]}: {active_addresses[x]}\n"
    response_data = {
        'REPORT_RESPONSE_FLAG': 1,
        'NUMBER': len(active_users),
        'PAYLOAD': f"Active users:\n{user_list}"
    }
    client_socket.send(json.dumps(response_data).encode('utf-8'))

# Handles a user's request to join the chatroom
def handle_join_request(client_socket, client_address, message_data):
    username = message_data['USERNAME']
    if len(active_clients) >= 3:
        response_data = {
            'JOIN_REJECT_FLAG': 1,
            'PAYLOAD': "The server rejects the join request. The chatroom has reached its maximum capacity."
        }
        client_socket.send(json.dumps(response_data).encode('utf-8'))
        return

    # Check for duplicate usernames
    for _, user in active_clients:
        if user == username:
            response_data = {
                'JOIN_REJECT_FLAG': 1,
                'PAYLOAD': "The server rejects the join request. Another user is using this username."
            }
            client_socket.send(json.dumps(response_data).encode('utf-8'))
            return

    # Add the new client to the active list
    active_clients.append((client_socket, username))
    active_addresses.append(client_address)
    temp = ""
    for msg in messages:
        temp += msg + "\n"
    response_data = {
        'JOIN_ACCEPT_FLAG': 1,
        'USERNAME': username,
        'PAYLOAD': f"Welcome {username} to the chatroom!\n Here is the chat  history:\n{temp}"
    }
    client_socket.send(json.dumps(response_data).encode('utf-8'))

    # Notify all other clients about the new user
    broadcast_message(f"{username} has joined the chatroom.")

# Handles a user's request to quit the chatroom
def handle_quit_request(client_socket,message_data):
    username = message_data['USERNAME']
    # Remove client from active clients list
    for i, (sock, _) in enumerate(active_clients):
        if sock == client_socket:
            del active_clients[i]
            break

    response_data = {
        'QUIT_ACCEPT_FLAG': 1,
        'PAYLOAD': "You have been disconnected."
    }
    # Broadcast to other users
    if username is not None:
        broadcast_message(f"{username} has left the chatroom.")
        client_socket.send(json.dumps(response_data).encode('utf-8'))

# Handles chat messages from clients
def handle_message(client_socket, message_data):
    message = message_data['PAYLOAD']
    print(f"Received message: {message}")
    messages.append(message)
    # Broadcast the message to all connected clients
    broadcast_message(message)

# Broadcasts the message to all active clients
def broadcast_message(message):
    for client_socket, _ in active_clients:
        try:
            response_data = {
                'PAYLOAD': message
            }
            client_socket.send(json.dumps(response_data).encode('utf-8'))
        except Exception as e:
            print(f"Error broadcasting message: {e}")

# Starts the server and listens for incoming client connections
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 18000))
    server_socket.listen(5)

    print("Server started. Waiting for connections...")
    while True:
        client_socket, client_address = server_socket.accept()
        # Handle the new client in a new thread
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()

if __name__ == '__main__':
    start_server()
