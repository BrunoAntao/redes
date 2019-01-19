import socket
import select
import pickle
import os.path
import shlex
import sys
import traceback  # para informação de excepções

from Crypto.Cipher import AES
from datetime import datetime

addr = '127.0.0.1'
SOCKET_LIST = []    # lista de sockets abertos
RECV_BUFFER = 4096  # valor recomendado na doc. do python
PORT = 5000

nfile = 'numbers.db'

NUMBERS = read_file(nfile)
AUTH = {}

def read_file(filename):

    if os.path.isfile(filename):
        
        with open(filename, "rb") as f:

            print('Opened file for read')
            
            table = pickle.load(f)

            return table

    else:

        with open(filename, "w+") as f:

            print('Created file')

            return {}

def write_to_file(data, filename):

    with open(filename, "wb") as f:

        print('Opened file for writing')
    
        pickle.dump(data, f)

def get_number(args):

    name = " ".join(args)

    if name in NUMBERS:
        return "CLIENTHASNUMBERS " + " ".join(NUMBERS.get(name)) + "\n"

    return "NOTFOUND " + name + '\n'

def set_number(args):

    if check_auth(args[2:]):

        if args[0] in NUMBERS:
            NUMBERS[args[0]].append(args[1])
        else:
            NUMBERS[args[0]] = []
            NUMBERS[args[0]].append(args[1])

        write_to_file(NUMBERS, nfile)

        return "NUMBERSET " + args[0] + " " + args[1] + '\n'

    else:
        
        return "AUTHFAIL \n"

def del_number(args):

    if check_auth(args[2:]):

        if args[0] in NUMBERS:

            if args[1] in NUMBERS[args[0]]:

                NUMBERS[args[0]].remove(args[1])
                write_to_file(NUMBERS, nfile)

                return "DELETED " + args[0] + " " + args[1] + '\n'

            else:

                return "NOTFOUND " + args[1] + '\n'
        else:

            return "NOTFOUND " + args[0] + '\n'

    else:
    
        return "AUTHFAIL \n"

def del_client(args):

    if check_auth(args[1:]):

        if args[0] in NUMBERS:

            del NUMBERS[args[0]]
            write_to_file(NUMBERS, nfile)

            return "DELETED " + args[0] + '\n'

        else:

            return "NOTFOUND " + args[0] + '\n'

    else:

        return "AUTHFAIL \n"

def reverse(args):

    names = []

    for client in NUMBERS:

        for number in NUMBERS[client]:

            if number == args[0]:

                names.append(client)
    
    if len(names) > 0:

        res = "CLIENTHASNAMES "

        for i in range(len(names)):

            if i != len(names) - 1:

                res += '"%s" ' % (names[i])
            
            else:

                res += '"%s"\n' % (names[i])

        return res

    else:

        return "NOTFOUND " + args[0] + '\n'

def check_auth(args):

    return args[0] in AUTH and AUTH[args[0]]['password'] == args[1]

def auth(args):

    if args[0] in AUTH:

        if AUTH[args[0]]['password'] == args[1]:

            return "AUTHED\n"

        else:

            return "AUTHFAILED\n"

    else:

        AUTH[args[0]] = { 'password': args[1], 'ttl': 60 }

        return "AUTHOK\n"

def no_command(args):

    return 'INVALIDCOMMAND\n'

def parse_command(argument, args):

    switcher = {

        "GETNUMBER": get_number,
        "SETNUMBER": set_number,
        "DELETENUMBER": del_number,
        "DELETECLIENT": del_client,
        "REVERSE": reverse,
        "AUTH": auth,
    }

    return switcher.get(argument, no_command)(args)

def parse_data(data, sock):

    obj = AES.new('k9rtbuyfgyug6dbn', AES.MODE_CFB, '6hghv998njnfbtsc')
    obj2 = AES.new('k9rtbuyfgyug6dbn', AES.MODE_CFB, '6hghv998njnfbtsc')

    for i in range(1,len(SOCKET_LIST)):

        if SOCKET_LIST[i] != sock:

            SOCKET_LIST[i].send(data)

    
    msg = str(obj2.decrypt(data))[2:-1].strip()
    nmsg = shlex.split(msg)

    try:

        result = parse_command(nmsg[0], nmsg[1:])
        print(result)
        sock.send(obj.encrypt(result))
        print("Client %s: Message: '%s'" % (sock.getsockname(), msg))

    except Exception as e:

        print("Exception thrown: " + str(e))
        sock.send("INVALIDCOMMAND\n".encode())
          
if __name__ == "__main__":

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", PORT))  # aceita ligações de qualquer lado
    server_socket.listen(10)
    server_socket.setblocking(0) # o socket deixa de ser blocking
    
    # Adicionamos o socket à lista de sockets a monitorizar
    SOCKET_LIST.append(server_socket)
    
    print("Server started on port %d" % (PORT,))

    timecount = 0
    while True:  # ciclo infinito

        # apagamos os sockets que "morreram" entretanto
        for sock in SOCKET_LIST:
            if sock.fileno() < 0:
                SOCKET_LIST.remove(sock)

        # agora, esperamos que haja dados em algum dos sockets que temos
        rsocks,_,_ = select.select(SOCKET_LIST,[],[], 5)

        if len(rsocks) == 0: # timeout
            timecount += 5

            for k, _ in AUTH.items():

                AUTH[k]['ttl'] -= 5

            AUTH = { k: v for k, v in AUTH.items() if v['ttl'] != 0 }
            
            if timecount % 60 == 0:  # passou um minuto
                print("Timeout on select() -> %d secs" % (timecount))
                timecount = 0
            continue
        
        for sock in rsocks:  # percorrer os sockets com nova informação
             
            if sock == server_socket: # há uma nova ligação
                newsock, addr = server_socket.accept()
                newsock.setblocking(0)
                SOCKET_LIST.append(newsock)
                
                print("New client - %s" % (addr,))
                 
            else: # há dados num socket ligado a um cliente
                try:
                    data = sock.recv(RECV_BUFFER)
                    if data: 
                        parse_data(data, sock)
                        
                    else: # não há dados, o cliente fechou o socket
                        print("Client disconnected 1")
                        sock.close()
                        SOCKET_LIST.remove(sock)
                        
                except Exception as e: # excepção ao ler o socket, o cliente fechou ou morreu
                    print("Client disconnected")
                    print("Exception -> %s" % (e,))
                    print(traceback.format_exc())
                    
                    sock.close()
                    SOCKET_LIST.remove(sock)