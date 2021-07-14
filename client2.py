import socket
import time
import threading


NUMBER_OF_THREADS = 2
JOB_NUMBER = [1, 2]

s = socket.socket()
# https://stackoverflow.com/questions/31080499/python-socket-running-server-and-client-from-the-same-pc/49080407
host = '127.0.0.1'  # connect internally '127.0.0.1',  biomix & eecis login from '69.137.150.164'
port = 6000

s.connect((host, port))  # JOINING_GAME state

def input_msg():
    cmd = input()
    s.send(str.encode(cmd))

def input_timer():
    time.sleep(30)
    s.send(str.encode('time out'))

def other_conditions(master_message, lists_of_strings):
    judge_point = 0
    for i in lists_of_strings:
        if i not in master_message:
            judge_point += 1
    if judge_point == len(lists_of_strings) and master_message != '':
        return True
    else:
        return False


while True:
    modifiedSentence = s.recv(1024)
    master_message = modifiedSentence.decode()
    # when master sends dummy message to test the connection.
    if 'test' in master_message:
        # CM_SUBSCRIBE message included here, player name is set as port number, no need to import name manually
        s.send(str.encode('test'))
    if "category from" in master_message:
        print('From Game Master: ', master_message)
        # CM_CATEGORY, player id is not needed here. player id will be automatically recognized by the server.
        while True:
            cmd = input("Choose a category from A to F, e.g. A: \n")
            options = ['A', 'B', 'C', 'D', 'E', 'F']
            if cmd in options:
                s.send(str.encode(cmd))
                break
            else:
                print("Your answer is not recognized, please read the message from the game master and choose again.")
    if "You can ring now" in master_message:                      # SM_RING_CLIENT message
        print('From Game Master: ', master_message)
        while True:
            cmd = input("ring> ")                   # ring-in input, simultaneous ring is solved at the server
            if cmd == '':
                print("You can type any letter to ring before pressing enter, please try again.")
            else:
                break
        s.send(str.encode(cmd))                     # CM_RING message sent here
    if 'Type your answer' in master_message:
        print('From Game Master: ', master_message)
        t1 = threading.Thread(target=input_msg)     # CM_ANSWER message
        t2 = threading.Thread(target=input_timer)   # timer, if no answer received in 30s. send 'time out' to server

        t2.start()
        t1.start()

        t2.join()
        t1.join(30)
    if 'End of the game!' in master_message:
        print('From Game Master: ', master_message)
        s.close()
        break
    # SM_NEW_GAME message, SM_NEW_ROUND message, SM_CATEGORY message,
    # SM_CATEGORY message, SM_QUESTION message, SM_ANSWER message
    if other_conditions(master_message, ['test', "category from", "You can ring now", 'Type your answer',
                                         'End of the game!']):
        print('From Game Master: ', master_message)
        s.send(str.encode('test'))




