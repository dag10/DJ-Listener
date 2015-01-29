# DJ Listener

A python client for listening to public rooms on a DJ server.

See the [DJ project page](https://github.com/dag10/DJ) for more information.

Installation
---
Using pip, install the modules listed in requirements.txt:

`pip install -r requirements.txt`

You must also install `mplayer` using your system's package manager.

Launching
---
```
usage: app.py [-h] [-p [PORT]] [--no-audio] [--verbose] [-d [DEVICE]]
              host room

Play music from a DJ room.

positional arguments:
  host                  Host of DJ server to connect to.
  room                  Short name of room to to join.

optional arguments:
  -h, --help            show this help message and exit
  -p [PORT], --port [PORT]
                        Port of DJ server to connect to. (default: 80)
  --no-audio            Don't play audio from room.
  --verbose             If set, debug messages will be printed to stdout.
  -d [DEVICE], --alsa-device [DEVICE]
                        ALSA device string. (example: "hw=1.0")
```

Example Output
---
```
$ python app.py dj.example.net lounge
INFO:root:Connected to DJ at dj.example.net:80
INFO:root:Joined room "Lounge"
INFO:root:User drew is currently playing "Catherine" by Magic Man  (length: 3:36) starting from 0:11
INFO:root:There is currently 1 anonymous listener in the room. It's probably this client.
INFO:root:Users currently in the room: Drew Gottlieb (drew)
INFO:root:User drew started playing "Dig" by Incubus (length: 4:16)
INFO:root:User drew started playing "Tranquilize" by Finish Ticket (length: 3:52)
INFO:root:There are currently 2 anonymous listeners in the room.
INFO:root:No song is currently playing.
INFO:root:Drew Gottlieb (drew) left the room.
```

--

[![CSH Logo](http://csh.rit.edu/images/logo.png)](http://csh.rit.edu)
