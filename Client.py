import socket
import time
import ast
import threading
from math import floor, ceil
from Classes import *
import tkinter
import tkinter.font as tkFont
from tkinter import messagebox, Canvas, Text, Button

IP = "192.168.0.215"
PORT = 50000

WIDTH = 800
HEIGHT = 800

username = "Mommy Michael"
password = "yomomma"

connectionRefusedYet = False

def connection_refused_error_message(state:bool):
    global connectionRefusedYet

    # we only do stuff if the new state is not equal to the old
    if connectionRefusedYet != state:
        # if we haven't been refused yet, throw an error!
        if not connectionRefusedYet:
            messagebox.showerror("ConnectionRefusedError", "The server could not be connected to! Check your internet connection.")
            connectionRefusedYet = True

        else:
            connectionRefusedYet = True


messageList = []

# this is the last time we refreshed.
lastRefreshTime = time.time_ns() - 10000000
lastMessageID = -2**60

def unpack_list(listToAppend:list, listToStrip:list):
    for i in listToStrip:
        listToAppend.append(i)


def send_message(text, username='', password=''):
    global messageList
    try:
        connectionSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connectionSocket.connect((IP, PORT))
        connectionSocket.send(Message(text, time.time_ns(), username, password, 0).to_json().encode())
        connectionSocket.close()
        connection_refused_error_message(False)
    except ConnectionRefusedError:
        connection_refused_error_message(True)
        messageList.append(Message("Error: Connection refused! Check your internet connection. Message did not send.", time.time_ns(), "ERROR", ''))
    

def recv_messages(comparisonType:str, maxMessages=-1):
    global lastRefreshTime, connectionRefusedYet, lastMessageID
    try:
        connectionSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connectionSocket.connect((IP, PORT))
        connectionSocket.send(RefreshRequest(comparisonType, lastRefreshTime, lastMessageID, maxMessages).to_json().encode())
        # update our last refreshed time
        lastRefreshTime = time.time_ns()

        # recieve server's response
        serverResponse = connectionSocket.recv(8192).decode()
        connectionSocket.close()

        # first, we make it a list with ast. (I could have used json here but oh well.)
        serverListResponse = ast.literal_eval(serverResponse)

        # now, we decode every string in the list into a Message.
        trueResponse = []
        for messageJSON in serverListResponse:
            newMessage = Message.from_json(messageJSON)
            trueResponse.append(newMessage)
            if newMessage.messageID > lastMessageID:
                lastMessageID = newMessage.messageID

        


        # and we return it!
        connection_refused_error_message(False)
        return trueResponse
    except ConnectionRefusedError:
        connection_refused_error_message(True)
        return []


# this function handles receiving messages from the server every second or so.
def refresh_handler():
    global messageList, lastRefreshTime

    def sort_message_list():
        global messageList
        messageList.sort(key=lambda x: x.messageID, reverse=True)

    # get previous messages 100 seconds prior (and a max of 20 messages) on startup
    lastRefreshTime = time.time_ns() - 10**9
    serverReturn = recv_messages('time', 20)
    unpack_list(messageList, serverReturn)
    sort_message_list()

    while True:
        time.sleep(1)
        serverReturn = recv_messages('messageID', 20)
        unpack_list(messageList, serverReturn)
        sort_message_list()


# start the refresh handler
refreshThread = threading.Thread(target=refresh_handler, daemon=True)
refreshThread.start()



#send_message("ayo how you doin", "matthman2019", "yomomma")


def main():

    # now for the tkinter window (it must run in the main thread)

    # root is the window
    root = tkinter.Tk()
    root.geometry(f'{str(WIDTH)}x{str(HEIGHT)}')
    root.wm_resizable(True, True)

    # this is our main font
    textSize = 12
    mainFont = tkFont.Font(family="Consolas", size=textSize, weight="normal")
    characterLength = mainFont.measure("m")

    # finds the width of textBox and sendButton
    textBoxWidth = floor(700 / characterLength)
    sendButtonWidth = ceil(100 / characterLength)

    def ask_exit():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", ask_exit)

    # canvas is where we draw the messages
    canvas = Canvas(root, width=WIDTH, height=HEIGHT, bg="white") 
    canvas.pack(fill="both", expand=True)

    # textBox is where we put our text to send
    textBox = Text(root, height=2, width=textBoxWidth, font=mainFont)
    textBox.place(anchor="sw", x=0, y=HEIGHT)

    def message_send():
        nonlocal textBox
        global username, password
        messageText = textBox.get("1.0", "end-1c").strip('\n')
        textBox.delete("0.0", "end")
        send_message(messageText, username, password)

    # sendButton is our button to send
    sendButton = Button(root, text="Send", width=sendButtonWidth, height=2, font=mainFont)
    sendButton.config(command=message_send, padx=0, pady=0)
    sendButton.place(anchor="sw", x=textBoxWidth*characterLength, y=HEIGHT)

    # this handles window-size changing
    def change_window_size(event):
        global WIDTH, HEIGHT
        nonlocal textBoxWidth, sendButtonWidth, textBox, sendButton
        WIDTH = event.width
        HEIGHT = event.height
        
        textBoxWidth = floor(WIDTH * 0.875 / characterLength)
        sendButtonWidth = ceil(WIDTH * 0.125 / characterLength)

        textBox.config(width=textBoxWidth)
        textBox.place_forget()
        textBox.place(anchor="sw", x=0, y=HEIGHT)

        sendButton.config(width=sendButtonWidth)
        sendButton.place_forget()
        sendButton.place(anchor="sw", x=textBoxWidth*characterLength, y=HEIGHT)


    canvas.bind("<Configure>", change_window_size)

    # now for receiving messages!
    def process_message_list():
        global messageList, username, WIDTH
        nonlocal canvas, root, textSize, mainFont, textBox

        canvas.delete("all")
        drawY = HEIGHT - (textBox.winfo_height())
        
        for message in messageList:
            assert isinstance(message, Message)
            # get the color
            messageColor = "black"
            if message.username == username:
                messageColor = "blue"

            if message.username == "ERROR":
                messageColor = 'crimson'

            textToShow = f'{message.username}: {message.text}'
            
            messageText = canvas.create_text(0, drawY, text=textToShow,  fill=messageColor, anchor="sw", font=mainFont, width=WIDTH)
            x1, y1, x2, y2 = canvas.bbox(messageText)
            drawY -= y2-y1

        root.after(1000, process_message_list)
            

    root.after(1000, process_message_list)
    root.mainloop()

main()