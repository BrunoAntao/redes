import socket
import select

from Crypto.Cipher import AES

import ast
import sys

obj = AES.new('k9rtbuyfgyug6dbn', AES.MODE_CFB, '6hghv998njnfbtsc')
obj2 = AES.new('k9rtbuyfgyug6dbn', AES.MODE_CFB, '6hghv998njnfbtsc')

addr = '127.0.0.1'
port = 5000

SESSION = ""


def auth(a, args):

    global SESSION

    SESSION = args[0]

    return "AUTHORIZED"


def auth_fail(a, args):

    return "UNAUTHORIZED"


def no_response(a, args):

    return a + " " + " ".join(args)


def parse_response(argument, args):

    switcher = {

        "AUTHOK": auth,
        "AUTHFAIL": auth_fail,
    }

    return switcher.get(argument, no_response)(argument, args)

def parse_response_noauth(command, res, payload):

    if res == "NOTFOUND":
    
        return "Not found"

    elif command == "GETNUMBER":

        return sys.argv[2] + " has number" + " ".join(payload)

    elif command == "SETNUMBER":

        return sys.argv[2] + " number set to " + sys.argv[3]

    elif command == "DELETENUMBER":

        return sys.argv[2] + " number " + sys.argv[3] + " deleted from database"

    elif command == "DELETECLIENT":

        return sys.argv[2] + " deleted from database"



def set_number(args):

    return " ".join(args) + " " + SESSION


def del_number(args):

    return " ".join(args) + " " + SESSION


def del_client(args):

    return " ".join(args) + " " + SESSION


def get_number(args):

    return " ".join(args)

def no_command(args):

    return " ".join(args)


def parse_command(argument, args):

    switcher = {

        "SETNUMBER": set_number,
        "DELETENUMBER": del_number,
        "DELETECLIENT": del_client,
        "GETNUMBER": get_number
    }

    return switcher.get(argument, no_command)(args)

def parse_arg(arg):

    if arg[0] == "del" and len(arg) == 3:

        return "DELETENUMBER"

    elif arg[0] == "del":

        return "DELETECLIENT"

    elif arg[0] == "set":

        return "SETNUMBER"

    elif arg[0] == "get":

        return "GETNUMBER"

    else:

        return "NOTFOUND"

def first_auth(sock):

    command = "AUTH nuni ola"

    sock.send(command.encode())

    data = " "
    data = sock.recv(100)

    msg = data.decode().rstrip().split(" ")

    parse_response(msg[0], msg[1:])

if __name__ == "__main__":

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (addr, port)
    sock.connect(server_address)

    try:

        #first_auth(sock)
        
        command = parse_arg(sys.argv[1:])
        protocol =  command + " " + parse_command(command, sys.argv[2:])

        ciphertext = obj.encrypt(protocol)
        sock.send(ciphertext)

        data = sock.recv(4096)
        msg = str(obj2.decrypt(data))[2:-3].split(" ")

        print(parse_response_noauth(command, msg[0], msg[1:]))

        #print(parse_response(msg[0], msg[1:]))

    except Exception as e:  # excepção ao ler o socket, o cliente fechou ou morreu

        print("Client disconnected")
        print("Exception -> %s" % (e))
           
