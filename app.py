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

        # Latest received number of anonymous listeners.
        self._last_num_anonymous = 0

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
        self._socket.on('error', self._on_error)
        self._socket.on('kick', self._on_kick)
        self._socket.on('room:num_anonymous', self._on_num_anonymous)
        self._socket.on('room:users', self._on_users)
        self._socket.on('room:user:join', self._on_user_join)
        self._socket.on('room:user:leave', self._on_user_leave)
        self._socket.on('room:song:update', self._on_song_update)
        self._socket.on('room:song:stop', self._on_song_stop)

    def disconnect(self):
        """
        Closes a connection.
        """
        if not self.connected:
            return
        
        self._socket.disconnect()
        self._on_disconnect()

    def join_room(self, shortname):
        """
        Requests to join a particular room.
        """
        self.ensure_connected('You must be connected to join a room.')
        logging.debug('Joining room "%s"...' % shortname)
        self._room_data = self._emit('room:join', shortname)
        self._room_data['shortname'] = shortname
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

        logging.debug('Emitting event "%s"' % event_name)

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
        if self._socket is None:
            raise Exception('No socket exists to wait on.')

        if seconds is None:
            logging.debug('Waiting indefinitely.')
        else:
            logging.debug('Waiting for %d seconds' % seconds)

        self._socket.wait(seconds)

    def _on_connect(self):
        """
        Called when the socket connects.
        """
        logging.info('Connected to DJ at %s:%d' % (self._host, self._port))

        if self._room_data:
            shortname = self._room_data['shortname']
            logging.info('Rejoining last room...')
            self.join_room(shortname)

    def _on_disconnect(self):
        """
        Called when the socket disconnects.
        """
        logging.info('Disconnected from DJ at %s:%d' % (
                self._host, self._port))
        self._last_num_anonymous = 0
        self._socket = None

    def _on_error(self, err=None):
        """
        Called when the socket has an error.
        """
        logging.warning('Error: %s' % err)

    def _on_kick(self, reason=None):
        """
        Handle DJ event "kick", where we're kicked from the room.
        """
        this._room_data = None
        if reason is not None:
            logging.info('Kicked from the room. Reason: %s' % reason)
        else:
            logging.info('Kicked from the room.')

    def _on_num_anonymous(self, num):
        """
        Handle DJ event "num_anonymous", updating the number of anonymous
        listeners.

        Args:
            num: Number of anonymous listeners.
        """
        if num == self._last_num_anonymous:
            return

        self._last_num_anonymous = num
        if num == 1:
            logging.info(
                    'There is currently 1 anonymous listener in the room. '
                    'It\'s probably this client.')
        else:
            logging.info(
                    'There are currently %d anonymous listeners in the room.'
                    % num)

    def _on_users(self, user_data):
        """
        Handle DJ event "room:users" which is a list of all users in the room.
        """
        logging.info(
                'Users currently in the room: ' +
                ', '.join(map(lambda user: user['fullName'], user_data)))

    def _on_user_join(self, user_data):
        """
        Handle DJ event "room:user:join" where a user joined the room.
        """
        logging.info('%s joined the room.' % user_data['fullName'])

    def _on_user_leave(self, user_data):
        """
        Handle DJ event "room:user:leave" where a user left the room.
        """
        logging.info('%s left the room.' % user_data['fullName'])

    def _on_song_update(self, song_data):
        """
        Handle DJ event "room:song:update" where a new song is playing.
        """
        dj = (('User ' + song_data['dj']['username']) if song_data['dj']
                else 'The room')
        logging.info(
                '%s is currenly playing "%s" by %s' % (
                        dj, song_data['title'], song_data['artist']))
    
    def _on_song_stop(self):
        """
        Handle DJ event "room:song:stop" when a stop is stopped.
        """
        logging.info('No song is currently playing.')

    @property
    def connected(self):
        return self._socket and self._socket.connected

    @property
    def in_room(self):
        return self.connected and (self._room_data is not None)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('socketIO_client').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

    client = DJClient('localhost', 9867)

    try:
        client.connect()
        client.join_room('lounge')
        client.wait()
    except KeyboardInterrupt:
        client.disconnect()

