import json

class Message:

    def __init__(self, text:str, time:float, username:str, password:str=None, messageID:int=0):
        self.text = text
        self.time = time
        self.username = username
        self.password = password
        self.messageID = messageID

    def __str__(self):
        return f'Message from "{self.username}" which says "{self.text}"'

    def to_json(self):
        return json.dumps({
            "code":"message",
            "username":self.username,
            "password":self.password,
            "time":self.time,
            "text":self.text,
            "messageID":self.messageID
            
            })
    
    @classmethod
    def from_json(cls, JSON):
        messageDict = json.loads(JSON)
        return Message(
            text=messageDict["text"], 
            time=messageDict["time"], 
            username=messageDict["username"], 
            password=messageDict["password"],
            messageID=messageDict["messageID"]
        )
    

class RefreshRequest:

    def __init__(self, comparison:str, time:float, messageID:int, maxMessages:int=-1):
        self.time = time
        self.comparison = comparison
        self.maxMessages = maxMessages
        self.messageID = messageID

    def to_json(self):
        return json.dumps({
            "code":"refreshRequest", 
            "time":self.time, 
            "maxMessages":self.maxMessages, 
            "comparison":self.comparison,
            "messageID":self.messageID
            })
    
    @classmethod
    def from_json(cls, JSON):
        requestDict = json.loads(JSON)
        return RefreshRequest(
            comparison=requestDict["comparison"],
            time=requestDict["time"],
            maxMessages=requestDict["maxMessages"],
            messageID=requestDict["messageID"]
        )
    

if __name__ == "__main__":
    print(Message.from_json(Message("HELLO WORLD!", 10, "matthman2019", "YoMomma").to_json()))
    print("This holds classes common to server and client!")