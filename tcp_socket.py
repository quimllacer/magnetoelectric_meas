# ============================================================================
# Name        : socket.py
# Author      : Julian Stiefel (jstiefel@ethz.ch)
# Version     : 1.0.0
# Created on  : 25.08.2020
# Copyright   :
# Description : A basic python class to provide TCP socket communication.
# ============================================================================

import socket

class TCP_Socket:
    def __init__(self, ip, port):
        # Opens up a socket connection to the instrument
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((ip, port))
            print('TCP_Socket created.')
        except:
            print('TCP_Socket could not been created.')

    def __del__(self):
        try:
            self.s.close()
            print('Destructor called, TCP_Socket deleted.')
        except:
            print('Desctructor called, TCP_Socket could not been deleted.')

    def send(self, command):
        # Send command
        try:
            command += '\n'
            command = command.encode('ascii')
            self.s.sendall(command)
        except:
            print('Sending data to device failed.')

    def receive(self):
        # Read data until newline character
        data = " "
        while True:
            message = self.s.recv(1024)
            message = message.decode('ascii')
            last = len(message)
            if message[last-1] == '\n':
                data = data + message[:-1]
                return data
            else:
                data = data + message

    def ask(self, command):
        # Return value from query
        try:
            self.send(command)
            response = self.receive()
            return response
        except: 
            print('Asking device for return value failed.')

