# Open Forum Version 1.0

This is the original version of Open Forum! It requires 0 modules not in the standard python library, and should be able to run on any python installation with a version greater than 10.

## Protocol

Basic protocol can be found in Planning.txt. All messages are sent over TCP and are formatted like JSON. (They are built using Python's json module.)

## Server.py

The server can run on any internet-connected device! Change the variables IP and PORT to change the IP address and the port. Currently it is set to 127.0.0.1 and 50000 respectively.


## Client.py

The client can run on any internet-connected device! Like Server.py, make sure to change IP and PORT to whatever is necessary to connect to the server.
The variables username, password, and userColor can be set to give default user settings. Password does not do anything in Version 1.0, however.
