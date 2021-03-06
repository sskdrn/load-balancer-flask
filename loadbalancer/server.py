class Server:
    def __init__(self,host,port):
        self._host=host
        self._port=port
        self.no_of_connections=0
        self.url=f'http://{host}:{port}'
        self.localurl=f'http://localhost:{port}'
    @property
    def host(self):
        return self._host
    @host.setter
    def host(self, address):
        self._host=address
    @property
    def port(self):
        return self._port
    @port.setter
    def port(self, port):
        self._port=port
