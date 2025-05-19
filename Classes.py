import json

class Message:

    def __init__(self, text:str, time:float, username:str, password:str=None):
        self.text = text
        self.time = time
        self.username = username
        self.password = password

    def __str__(self):
        return f'Message from "{self.username}" which says "{self.text}"'

    def to_json(self):
        return json.dumps({"code":"message", "username":self.username, "password":self.password, "time":self.time, "text":self.text})
    
    @classmethod
    def from_json(cls, JSON):
        messageDict = json.loads(JSON)
        return Message(
            text=messageDict["text"], 
            time=messageDict["time"], 
            username=messageDict["username"], 
            password=messageDict["password"]
        )
    

class RefreshRequest:

    def __init__(self, time:float, maxMessages:int=-1):
        self.time = time
        self.maxMessages = maxMessages

    def to_json(self):
        return json.dumps({"code":"refreshRequest", "time":self.time, "maxMessages":self.maxMessages})
    
    @classmethod
    def from_json(cls, JSON):
        requestDict = json.loads(JSON)
        return RefreshRequest(
            time=requestDict["time"],
            maxMessages=requestDict["maxMessages"]
        )
    

if __name__ == "__main__":
    print(Message.from_json(Message("HELLO WORLD!", 10, "matthman2019", "YoMomma").to_json()))
    print("This holds classes common to server and client!")