from time import sleep
from multiprocessing import Process
import lirc
import re

class Player:
    def __init__(self, nth: int):
        self.nth = nth
        self.speed = 0
        self.lanechange = False

    def setspeed(self, s: int):
        self.speed = s

    def setlanechange(self, lc: bool):
        self.lanechange = lc

    def key(self):
        return "P%dS%dL%d" % (self.nth, self.speed, 1 if self.lanechange else 0)

class Race(Process):
    def __init__(self, q, players=[], remote="", socket="/var/run/lirc/lircd"):
        Process.__init__(self)
        self.q = q
        self.remote = remote
        self.socket = socket
        self.active = False
        self.players = self.__make_players(players)

    def run(self):
        with lirc.CommandConnection(socket_path=self.socket) as conn:
            while True:
                if self.active:
                    msg = conn.readline()

                    for _, p in self.players.items():
                        sleep(0.009)
                        lirc.SendCommand(conn, self.remote, [p.key()]).run()

                while not self.q.empty():
                    self.handle_message(self.q.get(False))

    def handle_message(self, msg):
        action = msg["message"]

        if re.match(r"start|stop", action):
            self.active = (action == "start")
        elif re.match(r"action|lanechange", action):
            data = msg["data"]
            value = data["value"]
            p = self.players.get(data["player"])

            if p:
                f = p.setspeed if action == "speed" else p.setlanechange
                f(value)
            else:
                pass # Error.
        else:
            pass # Error.

    def __make_players(self, players):
        p = players.copy()
        p.sort()

        return {n: Player(n) for n in players}
