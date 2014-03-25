from BrickPi import *   #import BrickPi.py file to use BrickPi operations
import threading
import socket
import select
import Queue
from threading import Thread
import sys

BrickPiSetup()  # setup the serial port for communication
BrickPi.MotorEnable[PORT_A] = 1 #Enable the Motor A
BrickPi.MotorEnable[PORT_D] = 1 #Enable the Motor D
BrickPiSetupSensors()   #Send the properties of sensors to BrickPi

running = True

#This thread is used for keeping the motor running while the main thread waits for user input
class BrickPiThread (threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
    def run(self):
        while running:
            BrickPiUpdateValues()       # Ask BrickPi to update values for sensors/motors
            time.sleep(.2)              # sleep for 200 ms

brickPiThread = BrickPiThread(1, "BrickPiThread", 1)                #Setup and start the thread
brickPiThread.setDaemon(True)
brickPiThread.start()

class ProcessCommandThread(Thread):
    def __init__(self):
        super(ProcessCommandThread, self).__init__()
        self.running = True
        self.q = Queue.Queue()

    def add(self, data):
        self.q.put(data)

    def stop(self):
        self.running = False

    def run(self):
        q = self.q
        while self.running:
            try:
                # block for 1 second only:
                value = q.get(block=True, timeout=1)
                process(value)
            except Queue.Empty:
                sys.stdout.write('.')
                sys.stdout.flush()
        if not q.empty():
            print "Elements left in the queue:"
            while not q.empty():
                print q.get()


commandThread = ProcessCommandThread()
commandThread.start()


def process(value):
    print "Processing [{v}]".format(v=value)

    # Left side
    if value == 'L-FORWARD-Start':
        print "L-FORWARD-Start"
        BrickPi.MotorSpeed[PORT_A] = 200
    elif value == 'L-FORWARD-Stop':
        print "L-FORWARD-Stop"
        BrickPi.MotorSpeed[PORT_A] = 0
    elif value == 'L-BACK-Start':
        print "L-BACK-Start"
        BrickPi.MotorSpeed[PORT_A] = -200
    elif value == 'L-BACK-Stop':
        print "L-BACK-Stop"
        BrickPi.MotorSpeed[PORT_A] = 0
    # Right side
    if value == 'R-FORWARD-Start':
        print "R-FORWARD-Start"
        BrickPi.MotorSpeed[PORT_D] = 200
    elif value == 'R-FORWARD-Stop':
        print "R-FORWARD-Stop"
        BrickPi.MotorSpeed[PORT_D] = 0
    elif value == 'R-BACK-Start':
        print "R-BACK-Start"
        BrickPi.MotorSpeed[PORT_D] = -200
    elif value == 'R-BACK-Stop':
        print "R-BACK-Stop"
        BrickPi.MotorSpeed[PORT_D] = 0


def main():
    s = socket.socket()
    #host = socket.gethostname()
    host = "192.168.0.10"
    port = 3033
    s.bind((host, port))

    print "Server listening on port {p}...".format(p=port)

    s.listen(5)                 # Now wait for client connection.

    while True:
        try:
            client, addr = s.accept()
            ready = select.select([client, ], [], [], 2)
            if ready[0]:
                data = client.recv(4096)
                commandThread.add(data)
        except KeyboardInterrupt:
            print
            print "Stopping server."
            break
        except socket.error, msg:
            print "Socket error %s" % msg
            break

    cleanup()


def cleanup():
    commandThread.stop()
    commandThread.join()


if __name__ == "__main__":
    main()
