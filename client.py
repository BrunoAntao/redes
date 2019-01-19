import socket
import select
import shlex
from Crypto.Cipher import AES

import ast
import sys

addr = '127.0.0.1'
port = 5000

SESSION = []

def auth_fail(a, args):

    return "UNAUTHORIZED"

def no_response(a, args):

    return a + " " + " ".join(args)

def parse_response(command, res, payload, read):

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

        res = ''

        for i in payload:

            res += read[1] + " has number " + i + "\n"

        return res[:-1]

    elif command == "REVERSE":

        res = ''

        for i in payload:

            res += read[1] + " is the number for " + i + "\n"

        return res[:-1]

    elif command == "SETNUMBER":

        return read[2] + " number set to " + read[3]

    elif command == "DELETENUMBER":

        return read[2] + " number " + read[3] + " deleted from database"

    elif command == "DELETECLIENT":

        return read[2] + " deleted from database"

def auth_send(args):

    global SESSION

    SESSION = [args[0], args[1]]

    return " ".join(args)

def set_number(args):

    return '"%s" ' % (args[0]) + " ".join(args[1:]) + " " + " ".join(SESSION)


def del_number(args):

    return '"%s" ' % (args[0]) + " ".join(args[1:]) + " " + " ".join(SESSION)


def del_client(args):

    return '"%s"' % (args[0]) + " " + " ".join(SESSION)


def get_number(args):

    return '"%s"' % (args[0])

def reverse(args):

    return " ".join(args)

def no_command(args):

    return "command not found"


def parse_command(argument, args):

    switcher = {

        "SETNUMBER": set_number,
        "DELETENUMBER": del_number,
        "DELETECLIENT": del_client,
        "GETNUMBER": get_number,
        "REVERSE": reverse,
        "AUTH": auth_send
    }

    return switcher.get(argument, no_command)(args)

def parse_arg(arg):

    if arg[0] == "-del" and len(arg) == 3:
        
        return "DELETENUMBER"

    elif arg[0] == "-del":

        return "DELETECLIENT"

    elif arg[0] == "-set":

        return "SETNUMBER"

    elif arg[0] == "-auth":

        return "AUTH"

    else:
    
        try:
            
            eval(arg[0])
            return "REVERSE"

        except Exception:
            
            return "GETNUMBER"

if __name__ == "__main__":

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (addr, port)
    sock.connect(server_address)

    while True:

        obj = AES.new('k9rtbuyfgyug6dbn', AES.MODE_CFB, '6hghv998njnfbtsc')
        obj2 = AES.new('k9rtbuyfgyug6dbn', AES.MODE_CFB, '6hghv998njnfbtsc')

        try:
            
            read = input("$ ")
            read = shlex.split(read)

            if read[0] == "getphone":

                command = parse_arg(read[1:])

                if command == "GETNUMBER" or command == "REVERSE":

                    protocol =  command + " " + parse_command(command, read[1:])

                else:

                    protocol =  command + " " + parse_command(command, read[2:])

                ciphertext = obj.encrypt(protocol)
                sock.send(ciphertext)

                data = sock.recv(4096)

                msg = str(obj2.decrypt(data))[2:-3]
                msg = shlex.split(msg)

                print(parse_response(command, msg[0], msg[1:], read))

            else:

                print("Command not known")

        except Exception as e:  # excepção ao ler o socket, o cliente fechou ou morreu

            print("Client disconnected")
            print("Exception -> %s" % (e))
           
