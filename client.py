import socket
import select
import Crypto
from Crypto.PublicKey import RSA
from Crypto import Random
import ast

key = RSA.generate(1024, Random.new().read)
publickey = key.publickey()
private = key.privatekey()

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


def set_number(args):

    return " ".join(args) + " " + SESSION


def del_number(args):

    return " ".join(args) + " " + SESSION


def del_client(args):

    return " ".join(args) + " " + SESSION


def no_command(args):

    return " ".join(args)


def parse_command(argument, args):
    switcher = {
        "SETNUMBER": set_number,
        "DELETENUMBER": del_number,
        "DELETECLIENT": del_client,
    }

    return switcher.get(argument, no_command)(args)


if __name__ == "__main__":

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (addr, port)
    print('connecting to %s port %s' % server_address)
    sock.connect(server_address)

    while True:

        try:

            command = input("> ")

            if command == 'EXIT':

                print('closing socket')
                sock.close()
                break

            msg = command.split(" ")

            command = msg[0] + " " + parse_command(msg[0], msg[1::])

            sock.send(command.encode())

            data = " "
            data = sock.recv(100)

            msg = data.decode().rstrip().split(" ")
            print(parse_response(msg[0], msg[1:]))

        except Exception as e:  # excepção ao ler o socket, o cliente fechou ou morreu
            print("Client disconnected")
            print("Exception -> %s" % (e,))
            print(traceback.format_exc())
