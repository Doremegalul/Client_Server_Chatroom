# Client Server Chatroom

This project is a client-server chatroom application built with Python and TCP socket programming. It supports real-time text messaging, chat history, and file sharing between up to three concurrent users. Each user runs a client.py instance and connects to a central server.py instance, which manages user sessions, message broadcasting, and file transfer.

- Socket Programming: Implements a multithreaded server and multiple clients communicating over TCP (port 18000).
- Structured Messaging: Uses a JSON-based message protocol with flags for actions like JOIN, QUIT, MESSAGE, REPORT, and FILE.
- Real-Time Chat: Clients can send/receive messages in real time. All chat history is stored and shown to new users upon joining.
- File Sharing: Clients can upload .txt files (and optionally images for extra credit) that are broadcast to other users and saved locally.
- Access Control: Limits chatroom to a maximum of 3 active users and ensures unique usernames.
