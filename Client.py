import socket
import time
import ast
import threading
from math import floor, ceil
from Classes import *
import tkinter
import tkinter.font as tkFont
from ttkbootstrap import Canvas, Text, Button, Entry, Label, Style, Frame
from ttkbootstrap.dialogs.colorchooser import ColorChooserDialog
from ttkbootstrap.dialogs import Messagebox as messagebox
import ttkbootstrap as ttk

worldwideMode = False

if worldwideMode:
    IP = socket.gethostbyname("say-request.gl.at.ply.gg")
    PORT = 48826
else:
    IP = "127.0.0.1"
    PORT = 50000



WIDTH = 800
HEIGHT = 800

username = "anonymous"
password = "yomomma"
userColor:str = "#0000FF"

connectionRefusedYet = False

def connection_refused_error_message(state:bool):
    global connectionRefusedYet

    # we only do stuff if the new state is not equal to the old
    if connectionRefusedYet != state:
        # if we haven't been refused yet, throw an error!
        if not connectionRefusedYet:
            messagebox.show_error(title="ConnectionRefusedError", message="The server could not be connected to! Check your internet connection.")
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
        # basically we have to keep recieving until the square bracket ends.
        # the entire server transmission is inside a bracket [] (It's JSON)
        # so when we can actually decode it (with ast), we know the transmission is complete.
        doneRecieving = False
        serverResponse = ''
        serverListResponse = []
        while not doneRecieving:
            serverResponse += connectionSocket.recv(2**32).decode()
            # if we can evaluate it with ast, we're done
            try:
                serverListResponse = ast.literal_eval(serverResponse)
                doneRecieving = True
                break
            except:
                # if we can't (List is unclosed), we keep receiving.
                doneRecieving = False

        
        connectionSocket.close()


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

'''
# start the refresh handler
refreshThread = threading.Thread(target=refresh_handler, daemon=True)
refreshThread.start()
'''


#send_message("ayo how you doin", "matthman2019", "yomomma")


def main():

    # now for the tkinter window (it must run in the main thread)

    # root is the window
    root = ttk.Window(title="OpenForum Client", themename="cosmo")
    root.geometry(f'{str(WIDTH)}x{str(HEIGHT)}')
    root.wm_resizable(True, True)
    root.title("Open Forum")



    def ask_exit():
        if messagebox.okcancel(title="Quit", message="Do you want to quit?", alert=True):
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", ask_exit)

    # canvas is where we draw the messages
    canvas = Canvas(root, width=WIDTH, height=HEIGHT*0.9) 
    canvas.grid(sticky=('n', 's', 'e', 'w'), row=0, column=0, columnspan=2)

    def message_send():
        nonlocal textBox
        global username, password
        messageText = textBox.get("1.0", "end-1c").strip('\n')
        textBox.delete("0.0", "end")
        send_message(messageText, username, password)

    # sendButton is our button to send
    sendButton = Button(root, text="Send", width=6)
    sendButton.config(command=message_send)
    sendButton.grid(row=1, column=1, sticky="nsew")

    # sets the spacing
    root.columnconfigure(1, weight=2)
    root.columnconfigure(0, weight=8)
    root.rowconfigure(0, weight=9)
    root.rowconfigure(1, weight=1)



    # this is to make textBox not take up the entire screen
    textBoxFrame = Frame(root, width=WIDTH*0.8, height=HEIGHT*0.1)
    textBoxFrame.grid(row=1, column=0, sticky="nsew")

    # textBox is where we put our text to send
    textBox = Text(textBoxFrame, height=2)
    textBox.pack(expand=True, fill="both")

    # this handles window-size changing
    def change_window_size(event):
        
        global WIDTH, HEIGHT
        nonlocal textBox, sendButton, root
        WIDTH = event.width
        HEIGHT = event.height * 1.25

        root.update_idletasks()




    canvas.bind("<Configure>", change_window_size)

    # menu stuff
    def open_menu():
        global username, userColor
        nonlocal root
        chosenUserColor = userColor
        while root is None:
            pass

        
        menuRoot = ttk.Toplevel(root)
        menuRoot.geometry("400x400")

        usernameLabel = Label(menuRoot, text="Username:")
        usernameLabel.grid(row=0, column=0)

        usernameEntry = Entry(menuRoot, width=15)
        usernameEntry.insert("end", username)
        usernameEntry.grid(row=0, column=1)

        userColorLabel = Label(menuRoot, text="This is your message color", foreground=userColor)
        userColorLabel.grid(row=1, column=0)

        def get_user_color():
            nonlocal userColorLabel, chosenUserColor, menuRoot
            chosenUserColorWindow = ColorChooserDialog(parent=menuRoot, title="Choose your message color", initialcolor=userColor)
            chosenUserColorWindow.show()
            chosenUserColor = chosenUserColorWindow.result[2]
            if chosenUserColor is None:
                chosenUserColor = userColor
            userColorLabel.config(foreground=chosenUserColor, text="This will be your message color")
        
        userColorButton = Button(menuRoot, text="Change Color", command=get_user_color)
        userColorButton.grid(row=1, column=1)

        cancelButton = Button(menuRoot, text="Cancel", command=lambda:menuRoot.withdraw())
        cancelButton.place(anchor='sw', x=5, y=395)

        def save_choices():
            global userColor, username
            nonlocal chosenUserColor, usernameEntry, menuRoot

            username = usernameEntry.get()
            userColor = chosenUserColor
            menuRoot.withdraw()

        saveButton = Button(menuRoot, text="Save and Exit", command=save_choices)
        saveButton.place(anchor="se", x=395, y=395)

        

    menuButton = Button(root, text="Settings", command=open_menu)
    menuButton.place(anchor='nw', x=0, y=0)

    # now for receiving messages!
    def process_message_list():
        global messageList, username, WIDTH, userColor
        nonlocal canvas, root, textBox

        canvas.delete("all")
        drawY = HEIGHT
        
        for message in messageList:
            assert isinstance(message, Message)
            # get the color
            messageColor = "black"
            if message.username == username:
                messageColor = userColor

            if message.username == "ERROR":
                messageColor = 'crimson'

            textToShow = f'{message.username}: {message.text}'
            
            messageText = canvas.create_text(0, drawY, text=textToShow,  fill=messageColor, anchor="sw", width=WIDTH)
            x1, y1, x2, y2 = canvas.bbox(messageText)
            drawY -= y2-y1

        root.after(1000, process_message_list)
            

    root.after(1000, process_message_list)
    root.mainloop()

main()