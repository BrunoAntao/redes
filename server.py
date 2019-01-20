import socket
import select
import pickle
import os.path
import shlex
import sys
import traceback  # para informação de excepções

from Crypto.Cipher import AES

addr = '127.0.0.1'
SOCKET_LIST = []    # lista de sockets abertos
RECV_BUFFER = 4096  # valor recomendado na doc. do python
PORT = eval(sys.argv[1])
MASTERPORT = 5001

MASTER = (PORT == MASTERPORT)
SWITCH = False

nfile = sys.argv[2]

def read_file(filename):

    if os.path.isfile(filename):
        
        with open(filename, "rb") as f:

            print('Opened file for read')
            
            table = pickle.load(f)

            return table

    else:

        with open(filename, "w+b") as f:

            print('Created file')

            pickle.dump({}, f)

            return {}

NUMBERS = read_file(nfile)
AUTH = {}

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

    try:

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

    except:

         return "AUTHFAIL \n"

def del_number(args):

    try:
        
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

    except:
        
        return "AUTHFAIL \n"

def del_client(args):

    try:
        
        if check_auth(args[1:]):
    
            if args[0] in NUMBERS:

                del NUMBERS[args[0]]
                write_to_file(NUMBERS, nfile)

                return "DELETED " + args[0] + '\n'

            else:

                return "NOTFOUND " + args[0] + '\n'

        else:

            return "AUTHFAIL \n"

    except:
        
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

def set_master(args):

    if args[0] in NUMBERS:
            NUMBERS[args[0]].append(args[1])
    else:
        NUMBERS[args[0]] = []
        NUMBERS[args[0]].append(args[1])

    write_to_file(NUMBERS, nfile)

    return "NUMBERSET " + args[0] + " " + args[1] + '\n'

def set_salve(args):

    if args[0] in NUMBERS:
            NUMBERS[args[0]].append(args[1])
    else:
        NUMBERS[args[0]] = []
        NUMBERS[args[0]].append(args[1])

    write_to_file(NUMBERS, nfile)

    return "NUMBERSET " + args[0] + " " + args[1] + '\n'

def del_client_master(args):

    if args[0] in NUMBERS:
    
        del NUMBERS[args[0]]
        write_to_file(NUMBERS, nfile)

        return "DELETED " + args[0] + '\n'

    else:

        return "NOTFOUND " + args[0] + '\n'

def del_number_master(args):

    if args[0] in NUMBERS:
    
        if args[1] in NUMBERS[args[0]]:

            NUMBERS[args[0]].remove(args[1])
            write_to_file(NUMBERS, nfile)

            return "DELETED " + args[0] + " " + args[1] + '\n'

        else:

            return "NOTFOUND " + args[1] + '\n'
    else:

        return "NOTFOUND " + args[0] + '\n'

def pong_slave(args):

    return "YES\n"

def parse_command(argument, args):

    switcher = {

        "GETNUMBER": get_number,
        "SETNUMBER": set_number,
        "DELETENUMBER": del_number,
        "DELETECLIENT": del_client,
        "REVERSE": reverse,
        "AUTH": auth,
        "MASTERREV": reverse,
        "MASTERGET": get_number,
        "MASTERSET": set_master,
        "MASTERDELC": del_client_master,
        "MASTERDELN": del_number_master,
        "ISALIVE": pong_slave
    }

    return switcher.get(argument, no_command)(args)

def parse_to_server(command):

    switcher = {

        "SETNUMBER": "MASTERSET",
        "DELETENUMBER": "MASTERDELN",
        "DELETECLIENT": "MASTERDELC",
        "REVERSE": "MASTERREV",
        "GETNUMBER": "MASTERGET"
    }

    return switcher.get(command)

def ping_master():

    try:

        obj = AES.new('k9rtbuyfgyug6dbn', AES.MODE_CFB, '6hghv998njnfbtsc')
        obj2 = AES.new('k9rtbuyfgyug6dbn', AES.MODE_CFB, '6hghv998njnfbtsc')

        encrypted = obj.encrypt("ISALIVE\n")

        master_sock.send(encrypted)
        master_data = master_sock.recv(4096)

        res = str(obj2.decrypt(master_data))[2:-3]

        return res == "YES"

    except Exception as e:
        
        return False

def save(command, known, data):

    global NUMBERS

    if command == "GETNUMBER":

        NUMBERS[known] = []

        for i in data:

            NUMBERS[known].append(i)

    else:

        for i in data:

            NUMBERS[i] = known

    write_to_file(NUMBERS, nfile)

def ask_master(sock, nmsg, encrypt_master, encrypt_key, decrypt_master):

    new_com = parse_to_server(nmsg[0])

    if nmsg[0] == "GETNUMBER":

        protocol = new_com + ' "%s"' % (nmsg[1])

    else:

        protocol = new_com + ' ' + nmsg[1]

    encrypted = encrypt_master.encrypt(protocol + '\n')

    master_sock.send(encrypted)
    master_data = master_sock.recv(RECV_BUFFER)

    res = str(decrypt_master.decrypt(master_data))[2:-3]

    to_save = shlex.split(res)

    save(nmsg[0], nmsg[1], to_save[1:])

    cypher = encrypt_key.encrypt(res + '\n')

    sock.send(cypher)

def notify_master(sock, nmsg, encrypt_master, encrypt_key, result):

    new_com = parse_to_server(nmsg[0])

    if nmsg[0] == "SETNUMBER":

        protocol = new_com + ' "%s" ' % (nmsg[1]) + nmsg[2]

    elif nmsg[0] == "DELETENUMBER":

        protocol = new_com + ' "%s" ' % (nmsg[1]) + nmsg[2]

    else:

        protocol = new_com + ' "%s"' % (nmsg[1])

    encrypted = encrypt_master.encrypt(protocol + '\n')

    master_sock.send(encrypted)
    master_data = master_sock.recv(4096)

    cypher = encrypt_key.encrypt(result)
    sock.send(cypher)

def parse_data(data, sock):

    encrypt_key = AES.new('k9rtbuyfgyug6dbn', AES.MODE_CFB, '6hghv998njnfbtsc')
    decrypt_key = AES.new('k9rtbuyfgyug6dbn', AES.MODE_CFB, '6hghv998njnfbtsc')

    decrypt_master = AES.new('k9rtbuyfgyug6dbn', AES.MODE_CFB, '6hghv998njnfbtsc')
    encrypt_master = AES.new('k9rtbuyfgyug6dbn', AES.MODE_CFB, '6hghv998njnfbtsc')

    msg = str(decrypt_key.decrypt(data))[2:-3].strip()
    nmsg = shlex.split(msg)

    try:

        result = parse_command(nmsg[0], nmsg[1:])

        if result.split(" ")[0] == "NOTFOUND" and not MASTER and (nmsg[0] == "GETNUMBER" or nmsg[0] == "REVERSE"):

            ask_master(sock, nmsg, encrypt_master, encrypt_key, decrypt_master)
            
        elif not MASTER and (nmsg[0] == "SETNUMBER" or nmsg[0] == "DELETENUMBER" or nmsg[0] == "DELETECLIENT"):

            try:
                
                if result != "AUTHFAIL \n":
    
                    notify_master(sock, nmsg, encrypt_master, encrypt_key, result)

                else:

                    sock.send(encrypt_key.encrypt("AUTHFAIL\n"))

            except:
                
                sock.send(encrypt_key.encrypt("AUTHFAIL\n"))

        else:

            cypher = encrypt_key.encrypt(result)
            sock.send(cypher)
        
        print("Client %s: Message: '%s'" % (sock.getsockname(), msg))

    except Exception as e:

        print("Exception thrown: " + str(e))
        sock.send(encrypt_key.encrypt("INVALIDCOMMAND\n"))

def switch_master():

    global SOCKET_LIST

    global new_master_socket

    new_master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    new_master_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    new_master_socket.bind(("0.0.0.0", MASTERPORT))  # aceita ligações de qualquer lado
    new_master_socket.listen(10)
    new_master_socket.setblocking(0) # o socket deixa de ser blocking
    
    SOCKET_LIST.append(new_master_socket)

if __name__ == "__main__":

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", PORT))  # aceita ligações de qualquer lado
    server_socket.listen(10)
    server_socket.setblocking(0) # o socket deixa de ser blocking
    
    SOCKET_LIST.append(server_socket)

    if not MASTER:

        global master_sock

        master_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (addr, MASTERPORT)
        master_sock.connect(server_address)

    # Adicionamos o socket à lista de sockets a monitorizar
    
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

            if not MASTER:

                if not ping_master():

                    switch_master()

                    MASTER = True
                    SWITCH = True

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
        
            elif SWITCH and sock == new_master_socket:

                newsock, addr = new_master_socket.accept()
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