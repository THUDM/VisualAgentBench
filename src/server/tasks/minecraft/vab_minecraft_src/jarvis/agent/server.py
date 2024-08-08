import socket

class Server():
    def __init__(self, port):
        self.first_turn = True
        self.port = port
        self.socket = None

    def step(self, prompt, image, reward, task_goal, done=None):
        message = ""
        if self.first_turn:
            message += f"Your task is to get a {task_goal} in your inventory.\n"
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind(("", self.port))
            self.socket.listen(1)
            print("Listen on port: ", self.port)
            self.first_turn = False
        
        if done:
            message += f"<RREWARD>{reward}</RREWARD><DDONE>{done}</DDONE>"
        else:
            message += prompt
            message += f"<IIMAGE>{image}</IIMAGE>"
            message += f"<RREWARD>{reward}</RREWARD>"
        
        conn, addr = self.socket.accept()
        with conn:
            print('Connected by', addr)
            conn.sendall(str(message).encode())
            data = conn.recv(8192)
            if not data:
                return False, ""
            data = data.decode("utf-8")
        
        return True, data
