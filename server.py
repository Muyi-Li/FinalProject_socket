"""
There are two Run server.py first and then run the client1.py and client2.py

A: random configuration by HPNX fixed-size lattice + move preference model,
B: 1000 simulated configurations,
C: genetic algorithm + lattice size restriction for optimization.

@author: Xihan Qin
"""


import operator
import socket
import sys
import concurrent.futures
from concurrent.futures import wait, ALL_COMPLETED
import time
from time import perf_counter


###############################################################################
"""
    main body of the program
"""


def main():
    global all_connections
    global all_address
    global MIN_PLAYERS
    global categories
    global all_points
    global active_clients

    MIN_PLAYERS = 2
    categories = {'A': 'Science', 'B': 'Literature', 'C': 'American History', 'D': 'Colleges & Universities',
                  'E': 'Sports', 'F': 'Music'}
    all_connections = []
    all_address = []
    all_points = []
    active_clients =[]

    work()


###############################################################################
"""
    defined programs
"""


def work():
    Player_Collection_and_Game_Start()  # Sate 1 & 2 Collect_subscription & GAME_IN_PROGRESS
    while True:
        ROUND_IN_PROGRES()              # State 3
        CATEGORY_SELECTED()             # State 4
        WAIT_FOR_RING()                 # State 5
        WAIT_FOR_CM_ANSWER()            # State 6
        END_OF_ROUND()                  # State 7
        Transition_state()              # For game master to make a decision to start a new round or end the game


def Player_Collection_and_Game_Start():
    create_socket()
    bind_socket()
    accepting_connections()


def create_socket():
    """
        Create a Socket (connect two computers)
    """
    try:
        global host
        global port
        global s
        host = ""  # the ip address of the server is going to be itself, thus leave it empty for now
        port = 6000  # use an uncommon port which is not used by protocols.
        s = socket.socket()
    except socket.error as msg:
        print("Socket creation error: " + str(msg))


def bind_socket():
    """
        Binding the socket and listening for connections
    """
    try:
        global host
        global port
        global s
        print("Binding the Port: " + str(port))

        s.bind((host, port))  # should use a tuple like (host, port).
        s.listen(5)  # The number of bad connections it is going to tolerate and after which is going to throw an error.
        # The listen error will lead to the except section below.

    except socket.error as msg:
        print("Socket Binding error" + str(msg) + "\n" + "Retrying...")
        bind_socket()  # recursion, call the bind function inside itself



def accepting_connections():
    """
        Handling connection from multiple clients and saving to a list
        Closing previous connections when server.py file is restarted
    """
    global all_connections
    global all_address
    global MIN_PLAYERS
    global all_points

    # close all previous connections first
    for c in all_connections:
        c.close()
    del all_connections[:]
    del all_address[:]

    print("Waiting for clients to subscribe ......")
    while True:
        try:
            conn, address = s.accept()
            # for the case that the connection is established but no activity is done soon.
            s.setblocking(1)  # 1:true, prevents timeout.
            all_connections.append(conn)
            all_address.append(address)
            # address is a list, the first element is the ip address, the second is port number
            print("Connection has been established: " + address[0] + " Port:" + str(address[1]))
            CM_SUBSCRIBE = "Welcome to Network Jeopardy Game!" \
                           "You are successfully connected, please allow some time for other players to get ready."
            conn.send(str.encode(CM_SUBSCRIBE))
            # when enough players stop accepting new connections, and notify all clients
            if len(all_connections) == MIN_PLAYERS:
                list_connections()  # call list_connections to check active clients, and update to "all_connections"
                if len(all_connections) == MIN_PLAYERS:
                    print("Enough players")
                    print("Game start!\n")
                    all_points = [0 for i in range(MIN_PLAYERS)]
                    send_all_message("Game start!\n")
                    break
                else:
                    print("Not enough players, keep waiting")
        except:
            print("Error accepting connections")


def ROUND_IN_PROGRES():
    global client_id
    while True:
        send_all_message("\nStart New Round.\n")
        print_active_clients()
        cmd = input("For master: \n"
                    "type 'select' <client id> from above to choose a client to pick a category \n"
                    "master> ")
        # select a client to pick up a category and notify all clients
        if 'select' in cmd:
            # receive the message from the selected client, the get_target function ensures the message is from the selected client
            conn = get_target(cmd)
            if conn is not None:
                SM_NEW_ROUND = "please wait for " + client_id + " to choose a category\n"
                send_all_message(SM_NEW_ROUND)
                pick_category(conn)
                break
        else:
            print("Command not recognized, please select again.")



def list_connections():
    """
        Display all current active connections with client
    """
    global all_connections
    global active_clients

    for i, conn in enumerate(all_connections):
        try:
            # Check'number'of'alive'connections'
            # send a dummy connection request to check if the connection is still active
            conn.send(str.encode('test'))
            # because we don't know how much data we will get back, need to set the size (201480) high enough
            conn.recv(1024)
        except:
            # if do not receive anything back, the connection is not active, delete the connection
            del all_connections[i]
            del all_address[i]
            continue
        act_client = str(i) + "   " + str(all_address[i][0]) + "   " + str(all_address[i][1]) + "\n"
        active_clients.append(act_client)


def print_active_clients():
    global active_clients
    print("----Active Clients----" + "\n")
    for act_client in active_clients:
        print(act_client)


def get_target(cmd):
    """
        Selecting the target
    """
    global all_connections
    global client_id
    try:
        target = cmd.replace('select ', '')  # target = id
        target = int(target)
        conn = all_connections[target]
        client_id = str(all_address[target][0]) + ' ' + str(all_address[target][1])
        print("You are now connected to: " + client_id)
        return conn
    except:
        print("Selection not valid")
        return None


def pick_category(conn):
    """
        Send message to chosen client
    """
    global client_id
    global categories

    message = "Please pick a category from: "
    options = ['A', 'B', 'C', 'D', 'E', 'F']

    for opt in options:
        if opt == 'F':
            message += "and " + opt + ": " + categories[opt] + "."
        else:
            message += opt + ": " + categories[opt] + ", "
    print("waiting response from client, %s.\n" % client_id)
    conn.send(str.encode(message))  # encode transfer the data from string to bytes, data are sent by bytes.
    while True:
        try:
            client_response = str(conn.recv(1024), "utf-8")  # CM_CATEGORY message
            if client_response in options:
                print("client, %s, made a choice, %s: %s\n" % (client_id, client_response, categories[client_response]))
                SM_CATEGORY = "category is chosen, " + client_response + ": " + categories[client_response] + \
                              ". Game master will ask a question from this category. \n" \
                              "Waiting for the question."
                send_all_message(SM_CATEGORY)
                break
        except:
            print("Error receiving response from the client")
            break


def send_all_message(message):
    while True:
        try:
            for i, conn in enumerate(all_connections):
                conn.send(str.encode(message))
                conn.recv(1024)
            if i >= (len(all_connections)-1):
                break

        except:
            print("Error sending messages to all clients")
            break


def CATEGORY_SELECTED():
    SM_QUESTION = input("Question input> ")
    msg = "\n\nYou have about 20 seconds to read the question and prepare to ring." \
          "\nWhen you receive 'start' from Game master." \
          " You can race to be the first to answer by sending any letter back to master.\n" \
          "Ready......."
    SM_QUESTION = "\n\n" + "Question: " + SM_QUESTION + msg
    send_all_message(SM_QUESTION)


def client_ring(conn):
    SM_ring = "start! You can ring now."
    conn.send(str.encode(SM_ring))
    t_start = perf_counter()
    while True:
        CM_RING = str(conn.recv(1024), "utf-8")
        if CM_RING!='test' and len(CM_RING) > 0:
            t_stop = perf_counter()
            t = t_stop - t_start
            break
    return (t, conn)


def thread_ring():
    global all_connections
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(client_ring, all_connections)
    return results


def WAIT_FOR_RING():
    global all_connections
    global first_ring_conn
    global first_ring_id
    global first_ring_idx


    first_ring_conn = None
    first_ring_id = None
    first_ring_idx = None

    time.sleep(20)
    print("Waiting for all clients to ring......\n")
    while True:
        results = thread_ring()
        results = list(results)
        results_list = results.copy()
        results_list.sort(key=operator.itemgetter(0))  # sort by first value in the tuple
        if len(results_list) > 1:
            if results_list[0][0] == results_list[1][0]:
                # solve simultaneous ring
                ring_again_ms = "more than 1 player ring at the same time, please be prepared to ring again."
                send_all_message(ring_again_ms)
                WAIT_FOR_RING()
        first_ring_conn = results_list[0][1]
        first_ring_idx = all_connections.index(first_ring_conn)
        first_ring_id = all_address[first_ring_idx][0] + ' ' + str(all_address[first_ring_idx][1])
        SM_RING_CLIENT = "Player " + str(first_ring_id) + " got the chance to answer. " \
                                                          "\nWaiting for the answer (up to 30 s)......\n"
        print(SM_RING_CLIENT)
        send_all_message(SM_RING_CLIENT)
        results_list = []
        break


def WAIT_FOR_CM_ANSWER():
    global first_ring_conn
    global first_ring_id
    global CLIENT_ANSWER

    print('Wait for the first ringed client to answer......')
    SM_first_Client = "You have 30 secs to answer the question. \nType your answer: "
    first_ring_conn.send(str.encode(SM_first_Client))
    while True:
        CM_ANSWER = str(first_ring_conn.recv(1024), "utf-8")
        if CM_ANSWER == 'time out':
            first_ring_conn.send(str.encode("time out! Waiting for the game master's message."))
        send_all_message("Answer is received, please wait for the master's judgement of the correctness......\n")
        CLIENT_ANSWER = f'Answer from {first_ring_id}: {CM_ANSWER}'
        print(CLIENT_ANSWER)
        break


def END_OF_ROUND():
    global all_points
    global first_ring_id
    global first_ring_idx
    global CLIENT_ANSWER
    global all_address
    global winner_idx_list

    # let the master judge is the answer is correct
    while True:
        judge = input("If the answer is correct, type 'Y'; if wrong, type 'N'; if time out, type 'X'.\n")
        if judge == 'Y':
            all_points[first_ring_idx] += 100
            SM_CLIENT_ANSWER = CLIENT_ANSWER + " is...... CORRECT!!!\n"
            send_all_message(SM_CLIENT_ANSWER)
            break
        elif judge == 'N':
            all_points[first_ring_idx] += 0
            SM_CLIENT_ANSWER = CLIENT_ANSWER + " is......wrong. Good Luck next time!\n"
            send_all_message(SM_CLIENT_ANSWER)
            break
        elif judge == 'X':
            all_points[first_ring_idx] += 0
            SM_CLIENT_ANSWER = str(first_ring_id) + "times out. Good Luck next time!\n"
            send_all_message(SM_CLIENT_ANSWER)
            break
        else:
            print('Your response is not recognized, please try it again.')

    all_points_msg = "The end of this round!\nAll players:\n"
    highest_point = 0
    for i in range(len(all_points)):
        if all_points[i] > highest_point:
            highest_point = all_points[i]
        all_points_msg += all_address[i][0] + ' ' + str(all_address[i][1]) + ' points: ' + str(all_points[i]) + '\n'
    winner_idx_list = [i for (i,j) in enumerate(all_points) if j == highest_point]
    all_points_msg += "Waiting for game master's next message...... \n"
    send_all_message(all_points_msg)
    print("End of this round. Please wait for the instruction for the next step......")
    time.sleep(3)


def Transition_state():
    global all_points
    global all_connections
    global winner_idx_list
    global all_address

    while True:
        cmd = input("Type 'Y' to continue to the next round, type 'N' to end the game\n")
        if cmd == 'Y':
            break
        elif cmd == 'N':
            end_msg = "End of the game! The winner(s) is/are:\n"
            winner = ''
            for i in winner_idx_list:
                winner += all_address[i][0] + ' ' + str(all_address[i][1]) + ' points: ' + str(all_points[i]) + '\n'
            end_msg += winner
            print(end_msg)
            send_all_message(end_msg)
            for conn in all_connections:
                conn.close()
            s.close()
            sys.exit(0)
        else:
            print('Your response is not recognized, please try it again.')

###############################################################################
if __name__ == '__main__':
    main()

sys.exit(0)
