from pathlib import Path
import time
import threading
import socket
import json
from Classes import *
import queue
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledText
from ttkbootstrap.constants import *
import os

IP = "127.0.0.1"
PORT = 50000

W_HEIGHT = 400
W_WIDTH = 600

sayAllClientConnections = False

messageIDAssign = -2**40

currentServerLogList = []
currentServerLogString = ""
serverLogWidget = None

IPLastReceivedDict = {}
usersOnline = 0
THIRTYNANOSECONDS = 10**9 * 30


messageList = []
messageQueue = queue.Queue(maxsize=0)

messageThreadEvent = threading.Event()

def get_key_safe(dictionary:dict, key:any):
    try:
        return dictionary[key]
    except KeyError:
        return None

# this function is meant to be run in a thread. It writes messages in the queue to the csv file.
def write_messages_to_log():
    while True:
        # wait until we can write into the log
        messageThreadEvent.wait()

        # write into the log
        with open("Logs/messageLog.csv", 'a') as file:
            # for everything in the queue, write it to csv
            while messageQueue.qsize() > 0:
                messageToWrite = messageQueue.get()
                file.write('{},{},{},{},{}\n'.format(
                    messageToWrite.text.replace(',', ';'),
                    str(messageToWrite.time).replace(',', ';'),
                    messageToWrite.username.replace(',', ';'),
                    messageToWrite.password.replace(',', ';'),
                    str(messageToWrite.messageID).replace(',', ';')
                    ))

        messageThreadEvent.clear()


# yes, I could have used the logging module.
# no, I wanted to do it myself.
def log_message(message:str, priority:int=1):
    global serverLogWidget, currentServerLogList, currentServerLogString
    messageStarter = ''
    if priority <= 1:
        messageStarter = "DEBUG"
    elif priority == 2:
        messageStarter = "INFO"
    elif priority == 3:
        messageStarter = "WARNING"
    elif priority == 4:
        messageStarter = "ERROR"
    elif priority == 5:
        messageStarter = "CRITICAL"
    elif priority >= 6:
        messageStarter = "FATAL"

    messageStarter += ': '

    # now we do the logging
    message = messageStarter + message
    print(message)
    currentServerLogList.append(message)
    currentServerLogString += message + '\n'
    if serverLogWidget is not None:
        serverLogWidget.insert('end', message+'\n')

    with open("Logs/ServerLog.txt", 'a') as file:
        file.write(message + '\n')


def send_server_event(text:str):
    global messageIDAssign
    messageToSend = Message(text, time.time_ns(), "SERVER", '', messageIDAssign)
    messageIDAssign += 1

    # put it where it belongs
    messageQueue.put(messageToSend)
    messageThreadEvent.set()
    messageList.append(messageToSend)


# this handles a request sent by the client
def handle_request_decoded(decodedDict : dict, decodedString:SyntaxWarning, address):
    global messageList, messageQueue, messageIDAssign
    try:
        requestType = decodedDict["code"]
    except KeyError:
        log_message("Bad request from client! No code attribute. Ignoring message.", 3)
        return "NoCodeError"

    # the client has sent us a message.
    if requestType == "message":
        requestMessage = Message.from_json(decodedString)

        # set the messageID
        requestMessage.messageID = messageIDAssign
        messageIDAssign += 1

        # put it where it belongs
        messageQueue.put(requestMessage)
        messageThreadEvent.set()
        messageList.append(requestMessage)
        
        log_message(f"Message recieved and processed by {address}", 2)

        return None

    # the client has asked for all messages since a certain time or message
    elif requestType == "refreshRequest":
        requestObject = RefreshRequest.from_json(decodedString)

        maxMessages = requestObject.maxMessages
        requestedTime = requestObject.time
        requestedID = requestObject.messageID
        requestedComparison = requestObject.comparison
        returnList = []
        messagesSending = 0

        if requestedComparison == 'time':
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


        elif requestedComparison == "messageID":

            # get messages since a certain id or until maxMessages is reached
            for index in range(len(messageList)-1, -1, -1):
                currentMessage = messageList[index]
                assert isinstance(currentMessage, Message)
                # break if maxMessages
                if messagesSending == maxMessages:
                    break
                # add a message if it's id is more recent than the id given
                elif currentMessage.messageID > requestedID:
                    
                    # hide the password
                    currentMessage.password = ''

                    returnList.append(currentMessage)
                    messagesSending += 1
                # if maxMessages hasn't been reached but id is less recent than id given, we break
                else:
                    break


        # get the list in chronological order
        returnList.reverse()

        # make all Messages json
        for index in range(len(returnList)):
            returnList[index] = returnList[index].to_json()

        sendList = json.dumps(returnList)

        if len(returnList) > 0:
            log_message(f"Relayed {str(len(returnList))} Messages to {address}.", 2)
        return sendList
    
    else:
        log_message(f"Request type not identified! Request type is {requestType}.", 3)

    # add more protocol later!


# this runs in a thread and manages a socket from the client.
def manage_client(clientSocket, address):
    global IPLastReceivedDict, messageIDAssign, THIRTYNANOSECONDS
    clientIP = address[0]
    try:
        clientRequestJSON = clientSocket.recv(20000).decode()
    except:
        log_message("Client sent a bad request! Could not be decoded in UTF-8.", 2)
        return

    # make sure that the client request is JSON-like and has a code attribute
    try:
        clientRequest = json.loads(clientRequestJSON)
    except:
        log_message("Client sent a bad request! Could not be JSON decoded! Ignoring message.", 2)
        print(clientRequestJSON)
        return
    
    # sends a welcome message.
    # the messageID is a little funky. This could lead to problems!
    def send_welcome_message():
        nonlocal clientSocket, clientIP
        global IPLastReceivedDict
        log_message(f"Welcome message sent to {clientIP}", 2)
        now = time.time_ns()
        # this is a little long! It takes a welcome message, sandwiches it between brackets (to be a list), then encodes and sends it.
        clientSocket.send(json.dumps([Message(f"Welcome! There are {str(usersOnline)} users online right now (Not including yourself.)", now, "SERVER", "", messageIDAssign).to_json()]).encode())
        IPLastReceivedDict[clientIP] = now

    # we see when they last sent us a message and we respond 
    # if we haven't seen them before OR we haven't seen them in the last 30 seconds, send a welcome message.
    # if we send a welcome message, we return. If we send something like this "[][]" ast will error.
    clientLastSeen = get_key_safe(IPLastReceivedDict, clientIP)
    if clientLastSeen is None:
        send_welcome_message()
        return
    elif clientLastSeen + THIRTYNANOSECONDS < time.time_ns():
        send_welcome_message()
        return
    else:
        pass
        

    stuffToSend = handle_request_decoded(clientRequest, clientRequestJSON, address)

    if stuffToSend is not None:
        clientSocket.send(str(stuffToSend).encode())
    
    clientSocket.close()
    return




# these following functions mainly are used in threads.

# this function is meant to be run in a thread! It checks which users are online and updates usersOnline.
def manage_users_online():
    global usersOnline, IPLastReceivedDict, THIRTYNANOSECONDS
    while True:
        usersOnline = 0
        startTime = time.time_ns()
        for clientIP, timeLastSeen in IPLastReceivedDict.items():
            if timeLastSeen + THIRTYNANOSECONDS < startTime:
                usersOnline += 1

        time.sleep(1)



# manages all sockets. Meant to be run in a thread.
def manage_sockets():

    # server socket setup
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((IP, PORT))
    serverSocket.listen()

    while True:
        clientSocket, address = serverSocket.accept()
        clientThread = threading.Thread(target=manage_client, args=(clientSocket, address))
        clientThread.start()

        if sayAllClientConnections:
            log_message('\n', 1)
            log_message(f"Recieved by {address}", 2)



# manages tkinter. Not meant to be run in a thread!
def manage_tkinter():
    global messageList, W_WIDTH, W_HEIGHT, serverLogWidget
    root = ttk.Window(themename="cosmo")
    root.geometry("{}x{}".format(str(W_WIDTH), str(W_HEIGHT)))
    root.title("OpenForum Server")

    serverLogText = ScrolledText(root, autohide=True, width=10, height=16)
    serverLogText.insert("end", "")
    serverLogWidget = serverLogText
    serverLogText.grid(row=0, column=0, rowspan=5, sticky="nsew")

    serverMessageLabel = ttk.Label(root, text="Send a Server-Wide Message")
    serverMessageLabel.grid(row=0, column=1, sticky="nsew")

    serverMessageTextFrame = ttk.Frame(root)
    serverMessageTextFrame.grid(row=1, column=1, columnspan=2, sticky="nsew")

    serverMessageEntry = ttk.Text(serverMessageTextFrame, width=1, height=1)
    serverMessageEntry.pack(fill='both', expand=True)

    def send_server_message_button():
        nonlocal root, serverMessageEntry
        textToSend = serverMessageEntry.get("1.0", "end-1c").strip('\n').replace(',', ';')
        serverMessageEntry.delete("0.0", "end")
        send_server_event(textToSend)
        log_message(f'Message send: "{textToSend}"', 2)

    serverMessageButton = ttk.Button(root, text="Send", command=send_server_message_button)
    serverMessageButton.grid(row=0, column=2, sticky="ew")
    
    root.columnconfigure(0, weight=3)
    root.columnconfigure(1, weight=1)
    root.columnconfigure(2, weight=1)
    

    root.mainloop()
    



# make sure we have a folder to log to
try:
    fileText = os.makedirs(Path(__file__).parent / "Logs")
    log_message("Logs folder created!", 2)
except FileExistsError:
    log_message("Logs folder found, using as a target for server logs.", 2)
        
socketThread = threading.Thread(target=manage_sockets)
socketThread.start()

log_message("Server is up and running!", 2)

usersOnlineThread = threading.Thread(target=manage_users_online)
usersOnlineThread.start()

log_message("Manage Users thread is running!")

# log.csv writer setup
logThread = threading.Thread(target=write_messages_to_log)
logThread.start()

log_message("Messages are being logged!", 2)



log_message("Starting Tk!", 2)
manage_tkinter()
