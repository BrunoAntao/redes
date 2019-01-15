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

def parse_response(command, res, payload):

    if res == "NOTFOUND":
    
        return "Not found"

    elif res == "AUTHFAIL":

        return "Not authorized"

    elif res == "AUTHFAILED":

        return "Your ursername or password is wrong"

    elif res == "AUTHOK":

        return "Authed"

    elif res == "AUTHED":

        return "Already authed"

    elif command == "GETNUMBER":

        return sys.argv[2] + " has number " + " ".join(payload)

    elif command == "REVERSE":

        return sys.argv[2] + " is the number for " + " ".join(payload)

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
        "GETNUMBER": get_number,
        "REVERSE": get_number
    }

    return switcher.get(argument, no_command)(args)

def parse_arg(arg):

    if arg[0] == "del" and len(arg) == 5:
        
        return "DELETENUMBER"

    elif arg[0] == "del":

        return "DELETECLIENT"

    elif arg[0] == "set":

        return "SETNUMBER"

    elif arg[0] == "get":

        try:
            
            eval(arg[1])
            return "REVERSE"

        except Exception:
            
            return "GETNUMBER"

    elif arg[0] == "auth":

        return "AUTH"

    else:

        return "NOTFOUND"

if __name__ == "__main__":

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (addr, port)
    sock.connect(server_address)

    try:
        
        command = parse_arg(sys.argv[1:])
        protocol =  command + " " + parse_command(command, sys.argv[2:])

        ciphertext = obj.encrypt(protocol)
        sock.send(ciphertext)

        data = sock.recv(4096)
        msg = str(obj2.decrypt(data))[2:-3].split(" ")

        print(parse_response(command, msg[0], msg[1:]))

    except Exception as e:  # excepção ao ler o socket, o cliente fechou ou morreu

        print("Client disconnected")
        print("Exception -> %s" % (e))
           
