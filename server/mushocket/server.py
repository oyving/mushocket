
import threading
import time
import SocketServer
import logging
import hashlib
import struct

class WebSocketKey(object):

    numbers = [str(x) for x in xrange(0, 10)]

    def __init__(self, payload, key1, key2):
        self.payload = payload
        self.key1 = key1
        self.key2 = key2

    def response(self):
        key1spaces = self.key_spaces(self.key1)
        key2spaces = self.key_spaces(self.key2)

        key1numbers = self.key_numbers(self.key1)
        key2numbers = self.key_numbers(self.key2)

        print "Debug:", key1numbers
        print "Debug:", key2numbers

        if key1spaces == 0 or key2spaces == 0:
            return False

        key1value = key1numbers / key1spaces
        key2value = key2numbers / key2spaces

        return hashlib.md5(
            struct.pack(">I", key1value) +
            struct.pack(">I", key2value) +
            self.payload).digest()

    def key_spaces(self, key):
        return key.count(" ")

    def key_numbers(self, key):
        result = ""
        for c in key:
            if c in self.numbers:
                result += c
        return int(result)




class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


class WebSocketHandler(SocketServer.StreamRequestHandler):
    """
    Initiates and sets up a socket for doing WebSocket communications with a
    browser.  Will do handshake, and then leave off to handleRequess
    implementation to deal with the rest.
    """

    numbers = [str(x) for x in range(0, 10)]

    def log(self, message):
        """
        Print messages in a simple standardized format to stdout
        """
        print "[%s] [%s] %s" % (
            time.time(), self.client_address, message)

    def setup(self):
        SocketServer.StreamRequestHandler.setup(self)
        self.start_session = time.time()
        self.log("Initiated new session")

    def handle(self):
        """
        Handle simple request.
        """
        if self.handshake():
            # handle normal request case
            for line in self.linereader():
                if line != "":
                    self.log("Received: " + line)
                    self.rfile.write("Received: " + line)
        else:
            self.log("Handshake not successful")
        
        # terminating, shut down handling
        self.log("Terminating session")

    def linereader(self):
        while True:
            yield self.rfile.readline().strip()

    def handshake(self):
        """
        Initialize communication by doing a hand-shake with the client.
        """
        fields = {}
        for line in self.linereader():
            self.log("Got content: " + line)
            if line == "":
                break
            elif line.startswith("GET "):
                pass
            else:
                header, value = line.split(": ", 2)
                fields[header] = value

        payload = self.rfile.read(8)

        self.log("Fields: " + str(fields))
        self.log("Payload: " + payload)

        # now we can check the fields and see if they have correct values
        correct = fields.get("Upgrade", "") == "WebSocket"
        correct = correct and fields.get("Connection", "") == "Upgrade"
        correct = correct and "Sec-WebSocket-Key1" in fields
        correct = correct and "Sec-WebSocket-Key2" in fields

        if not correct:
            return False

        key1 = fields.get("Sec-WebSocket-Key1")
        key2 = fields.get("Sec-WebSocket-Key2")
        origin = fields.get("Origin")

        response = WebSocketKey(payload, key1, key2).response()

        self.log("Calculated response: " + response)

        self.wfile.write("HTTP/1.1 101 WebSocket Protocol Handshake\r\n")
        self.wfile.write("Upgrade: WebSocket\r\n")
        self.wfile.write("Connection: Upgrade\r\n")
        self.wfile.write("Sec-WebSocket-Origin: " + origin + "\r\n")
        self.wfile.write("Sec-WebSocket-Location: ws://localhost:8080/mushocket\r\n")
        self.wfile.write("Sec-WebSocket-Protocol: mush\r\n")
        self.wfile.write("\r\n")
        self.wfile.write(response)

        self.log("Response sent")

        return True


if __name__ == '__main__':
    server = ThreadedTCPServer(("", 8080), WebSocketHandler)

    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.setDaemon(True)
    server_thread.start()

    try:
        while server_thread.is_alive:
            server_thread.join(timeout=60)
    except Exception, e:
        pass

    server.shutdown()
