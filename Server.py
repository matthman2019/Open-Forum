from pathlib import Path
import time
import threading
import socket
import json
from Classes import *
import queue

IP = "192.168.0.215"
PORT = 50000


messageList = []
messageQueue = queue.Queue(maxsize=0)

messageThreadEvent = threading.Event()

# this function is meant to be run in a thread. It writes messages in the queue to the csv file.
def write_messages_to_log():
    while True:
        # wait until we can write into the log
        messageThreadEvent.wait()

        # write into the log
        with open("log.csv", 'a') as file:
            # for everything in the queue, write it to csv
            while messageQueue.qsize() > 0:
                messageToWrite = messageQueue.get()
                file.write(f'{messageToWrite.text},{messageToWrite.time},{messageToWrite.username},{messageToWrite.password}\n')

        messageThreadEvent.clear()


# this handles a request sent by the client
def handle_request_decoded(decodedDict : dict, decodedString:SyntaxWarning, address):
    global messageList, messageQueue
    try:
        requestType = decodedDict["code"]
    except KeyError:
        print("Bad request from client! No code attribute. Ignoring message.")
        return "NoCodeError"

    # the client has sent us a message.
    if requestType == "message":
        requestMessage = Message.from_json(decodedString)
        messageQueue.put(requestMessage)
        messageThreadEvent.set()
        messageList.append(requestMessage)
        
        print(f"Message recieved and processed by {address}")

        return None

    # the client has asked for all messages since a certain time.
    elif requestType == "refreshRequest":
        requestObject = RefreshRequest.from_json(decodedString)

        maxMessages = requestObject.maxMessages
        requestedTime = requestObject.time
        returnList = []
        messagesSending = 0

        # get messages since a certain time or until maxMessages is reached
        for index in range(len(messageList)-1, -1, -1):
            currentMessage = messageList[index]

            # break if maxMessages
            if messagesSending == maxMessages:
                break
            # add a message if it's time is more recent than the time given
            elif currentMessage.time > requestedTime:
                
                # hide the password
                currentMessage.password = ''

                returnList.append(currentMessage)
                messagesSending += 1
            # if maxMessages hasn't been reached but time is less recent than time given, we break
            else:
                break
        
        # get the list in chronological order
        returnList.reverse()

        # make all Messages json
        for index in range(len(returnList)):
            returnList[index] = returnList[index].to_json()

        returnList = json.dumps(returnList)

        print(f"{address} send RefreshRequest, responded successfully")
        return returnList
    


    # add more protocol later!


# this runs in a thread and manages a socket from the client.
def manage_client(clientSocket, address):
    clientRequestJSON = clientSocket.recv(20000).decode()

    # make sure that the client request is JSON-like and has a code attribute
    try:
        clientRequest = json.loads(clientRequestJSON)
    except:
        print("Client sent a bad request! Could not be JSON decoded! Ignoring message.")
        return

    stuffToSend = handle_request_decoded(clientRequest, clientRequestJSON, address)

    if stuffToSend is not None:
        clientSocket.send(str(stuffToSend).encode())

    print('\n')
    
    clientSocket.close()
    return

        
# server socket setup
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serverSocket.bind((IP, PORT))
serverSocket.listen()

print("Server is up and running!")

# log.csv writer setup
logThread = threading.Thread(target=write_messages_to_log)
logThread.start()

print("Messages are being logged!")


while True:
    clientSocket, address = serverSocket.accept()
    clientThread = threading.Thread(target=manage_client, args=(clientSocket, address))
    clientThread.start()

    print(f"Recieved by {address}")

