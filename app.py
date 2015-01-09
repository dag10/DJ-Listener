import logging
from socketIO_client import SocketIO


class DJClient():
    class NotConnectedException(Exception):
        """
        Exception thrown when client is not connected.
        """
        pass

    class DJError(Exception):
        """
        Exception thrown when the DJ api returns an error message.
        """
        pass

    def ensure_connected(self, message=None):
        """
        Raises a NotConnectedException if not connected.
        """
        if not self.connected:
            raise self.NotConnectedException(message)

    def __init__(self, host, port=80):
        """
        Creates a new DJ client.

        Args:
            host: Hostname of DJ server.
            port: Port of DJ server.
        """
        # Host of DJ server
        self._host = host

        # Port of DJ server
        self._port = port

        # Active socket.io connection (if any)
        self._socket = None

        # Dict of room data for current room (or room just before disconnect)
        self._room_data = None

    def connect(self):
        """
        Initiates socket.io websocket connection.
        """
        if self.connected:
            self.disconnect()

        self._socket = SocketIO(
                    self._host, self._port, wait_for_connection=True)

        self._socket.on('connect', self._on_connect)
        self._socket.on('disconnect', self._on_disconnect)
        self._socket.on('room:num_anonymous', self._on_num_anonymous)
        self._socket.on('kick', self._on_kick)

    def disconnect(self):
        """
        Closes a connection.
        """
        if not self.connected:
            return
        
        self._socket.disconnect()
        self._socket = None

    def join_room(self, room):
        """
        Requests to join a particular room.
        """
        self.ensure_connected('You must be connected to join a room.')
        self._room_data = self._emit('room:join', room)
        self._room_data['shortname'] = room
        logging.info('Joined room "%s"' % self._room_data['name'])

    def leave_room(self):
        """
        Requests to leave the room.
        """
        self.ensure_connected('You must be connected to leave a room.')
        self._emit('room:leave')
        self._room_data = None

    def _emit(self, event_name, params=None, ignore_error=False):
        """
        Sychronous, blocking wrapper for socket.emit.

        Args:
            event_name: Socket.io event name to emit.
            params: Optional params to emit with the event.
            ignore_error: If True, ignore any API errors in the response.

        Returns:
            Callback data.
        """
        self.ensure_connected()

        # Hack to allow callback to modify parent scope data.
        cb_data = [None]
        def callback(data=None):
            cb_data[0] = data

        self._socket.emit(event_name, params, callback)
        self._socket.wait_for_callbacks()
    
        # Raise DJError if response has error message.
        if (not ignore_error and isinstance(cb_data, dict)
                    and 'error' in cb_data.keys()):
                raise self.DJError(cb_data['error'])

        return cb_data[0]

    def wait(self, seconds=None):
        if not self.connected:
            raise self.NotConnectedException()
        self._socket.wait(seconds)

    def _on_connect(self):
        """
        Called when the socket connects.
        """
        logging.info('Connected to DJ at %s:%d' % (self._host, self._port))

        if self._room_data:
            shortname = self._room_data['shortname']
            logging.info('Rejoining room "%s"' % shortname)
            self.join_room(shortname)

    def _on_disconnect(self):
        """
        Called when the socket disconnects.
        """
        logging.info('Disconnected from DJ at %s:%d' % (
                self._host, self._port))

    def _on_num_anonymous(self, num):
        """
        Handle DJ event "num_anonymous", updating the number of anonymous
        listeners.

        Args:
            num: Number of anonymous listeners.
        """
        if num == 1:
            logging.info('There is 1 anonymous listener in the room.')
        else:
            logging.info('There are %d anonymous listeners in the room.' % num)

    def _on_kick(self, reason=None):
        """
        Handle DJ event "kick", where we're kicked from the room.
        """
        this._room_data = None
        if reason is not None:
            logging.info('Kicked from the room. Reason: %s' % reason)
        else:
            logging.info('Kicked from the room.')

    @property
    def connected(self):
        return self._socket and self._socket.connected

    @property
    def in_room(self):
        return self.connected and (self._room_data is not None)


if __name__ == '__main__':
    try:
        logging.basicConfig(level=logging.INFO)
        client = DJClient('localhost', 9867)
        client.connect()
        client.join_room('lounge')
        client.wait()
    except KeyboardInterrupt:
        client.disconnect()

