import socket
import json
import threading
import sys
import os
from datetime import datetime

# Displays the menu for user input
def display_menu():
    print("\nPlease select one of the following options:")
    print("1. Get a report of the chatroom from the server.")
    print("2. Request to join the chatroom.")
    print("3. Quit the program.")
    
    option = input("Enter option (1/2/3): ")
    return option

# Sends the selected option as a message to the server
def send_message(option, username=None, message=None, filename=None):
    message_data = {}

    # Report request
    if option == '1':
        message_data = {
            'REPORT_REQUEST_FLAG': 1,       # Request a report
            'REPORT_RESPONSE_FLAG': 0,      # Not a response yet
            'JOIN_REQUEST_FLAG': 0,         # No join request
            'QUIT_REQUEST_FLAG': 0,         # Not quitting
            'ATTACHMENT_FLAG': 0,           # No attachment
            'NUMBER': 0,                    # No number yet
            'USERNAME': '',                 # No username
            'FILENAME': '',                 # No file
            'PAYLOAD_LENGTH': 0,            # No message body
            'PAYLOAD': ''                   # Empty payload
        }
    
    # Join request
    elif option == '2':
        username = input("Enter your username: ")
        message_data = {
            'REPORT_REQUEST_FLAG': 0,       # No report request
            'REPORT_RESPONSE_FLAG': 0,      # No report response
            'JOIN_REQUEST_FLAG': 1,         # Join request
            'JOIN_REJECT_FLAG': 0,          # Not a reject
            'JOIN_ACCEPT_FLAG': 0,          # Not accepted yet
            'NEW_USER_FLAG': 0,             # Not a new user yet
            'QUIT_REQUEST_FLAG': 0,         # Not quitting
            'ATTACHMENT_FLAG': 0,           # No attachment
            'NUMBER': 0,                    # No number yet
            'USERNAME': username,           # Include the username
            'FILENAME': '',                 # No file
            'PAYLOAD_LENGTH': len(username),# Include the username length
            'PAYLOAD': ''                   # Empty payload
        }
    
    # Quit request
    elif option == '3':
        message_data = {
            'REPORT_REQUEST_FLAG': 0,       # No report request
            'REPORT_RESPONSE_FLAG': 0,      # No report response
            'JOIN_REQUEST_FLAG': 0,         # No join request
            'QUIT_REQUEST_FLAG': 1,         # Quit request
            'QUIT_ACCEPT_FLAG': 0,          # Not accepted yet
            'ATTACHMENT_FLAG': 0,           # No attachment
            'NUMBER': 0,                    # No number
            'USERNAME': username,           # Username
            'FILENAME': '',                 # No file
            'PAYLOAD_LENGTH': 0,            # No message
            'PAYLOAD': ''                   # Empty payload
        }
    
    # Chat message
    elif option == '4':
        message_data = {
            'REPORT_REQUEST_FLAG': 0,       # Not a report request
            'REPORT_RESPONSE_FLAG': 0,      # Not a report response
            'JOIN_REQUEST_FLAG': 0,         # Not a join request
            'QUIT_REQUEST_FLAG': 0,         # Not quitting
            'ATTACHMENT_FLAG': 0,           # No attachment
            'NUMBER': 0,                    # No number
            'USERNAME': username,           # Username included
            'FILENAME': '',                 # No file
            'PAYLOAD_LENGTH': len(message), # Length of the message
            'PAYLOAD': f"[{datetime.now().strftime('%H:%M')}] {username}: {message}"  # The actual message
        }

    # Send file attachment
    elif option == '5':
        
        filename = input("Enter the path to the file: ")
        try:
            with open(filename, 'rb') as f:
                file_content = f.read()
            message_data = {
                'REPORT_REQUEST_FLAG': 0,       # Not a report request
                'REPORT_RESPONSE_FLAG': 0,      # Not a report response
                'JOIN_REQUEST_FLAG': 0,         # Not a join request
                'QUIT_REQUEST_FLAG': 0,         # Not quitting
                'ATTACHMENT_FLAG': 1,           # Attachment flag set
                'NUMBER': 0,                    # No number
                'USERNAME': username,           # Username included
                'FILENAME': filename,           # The filename
                'PAYLOAD_LENGTH': len(file_content), # Length of file content
                'PAYLOAD': file_content.decode('latin1')  # File content as payload 
            }
        except FileNotFoundError:
            print("File not found, please try again.")
            return None

    return json.dumps(message_data)

# Allows the user to chat in the chatroom after joining
def chatroom(client_socket, username):
    print("\nIn the chatroom. You can:")
    print("1. Send a text message.")
    print("2. Type a for file attachment.")
    print("3. Type 'q' to leave the chatroom.")
    while True:
        option = input("")

        # Send a file attachment
        if option == 'a':
            message = send_message('5', username)
            if message:
                client_socket.send(message.encode('utf-8'))
        
        # Quit the program
        elif option.lower() == 'q':
            print("Exiting chat...")
            quit_message = send_message('3', username)  
            client_socket.send(quit_message.encode('utf-8'))
            break

        # Send a chat message
        else:
            message = send_message('4', username, option)
            if message:
                client_socket.send(message.encode('utf-8'))
        
# Listens for incoming messages from the server
def listen_for_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                try:
                    # Try to decode the message into JSON (control messages)
                    response_data = json.loads(message)
                    if 'PAYLOAD' in response_data:
                        print(f"\n{response_data['PAYLOAD']}")
                except json.JSONDecodeError:
                    # If it's not JSON, it's a chat message, so just print it
                    print(f"\n{message}")  # It's a regular chat message
            else:
                print("Server disconnected or sent an empty message.")
                break
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

# Starts the client and communicates with the server
def start_client():
    keep_Looping = True
    while keep_Looping:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 18000))

        username = None
        while True:
            option = display_menu()

            if option == '1':
                # Get the report from the server
                message = send_message(option)
                client_socket.send(message.encode('utf-8'))

                # Receive the response from the server
                response = client_socket.recv(1024).decode('utf-8')
                response_msg = json.loads(response)
                print(response_msg['PAYLOAD'])

            elif option == '2':
                # Join the chatroom
                message = send_message(option)
                client_socket.send(message.encode('utf-8'))

                # Receive the response from the server
                response = client_socket.recv(1024).decode('utf-8')
                response_data = json.loads(response)

                if response_data.get('JOIN_ACCEPT_FLAG') == 1:
                    print(f"Server response: {response_data['PAYLOAD']}")
                    username = response_data.get('USERNAME')
                    print(f"Welcome to the chatroom, {username}!")
                    # Now proceed to chat in the chatroom

                    # Start listening for incoming messages from the server
                    threading.Thread(target=listen_for_messages, args=(client_socket,), daemon=True).start()

                    # Continue chatting
                    chatroom(client_socket, username)
                    # After the user quits, break from the loop
                    break
                else:
                    print(f"Server response: {response_data['PAYLOAD']}")

            elif option == '3':
                # Quit the program
                message = send_message(option, username)
                client_socket.send(message.encode('utf-8'))
                # Receive the response from the server
                print(message)
                response = client_socket.recv(1024).decode('utf-8')
                print(f"Server response: {response}")
                keep_Looping = False
                break

            else:
                print("Invalid option, please try again.")

    # Close the client socket and exit
    client_socket.close()
    print("Connection closed. Exiting...")
    sys.exit(0)

if __name__ == '__main__':
    start_client()
