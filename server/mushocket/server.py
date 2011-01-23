
import threading
import time
import SocketServer
import logging


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


class WebSocketHandler(SocketServer.StreamRequestHandler):
    """
    Initiates and sets up a socket for doing WebSocket communications with a
    browser.  Will do handshake, and then leave off to handleRequess
    implementation to deal with the rest.
    """

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
            pass
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
        handshake_fields = {}
        for line in self.linereader():
            self.log("Got content: " + line)
            if line == "":
                break
            elif line.startswith("GET "):
                pass
            else:
                header, value = line.split(": ", 2)
                handshake_fields[header] = value
        self.log(str(handshake_fields))


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
