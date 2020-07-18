from __future__ import annotations
import socket
import logging
import re
import threading
import pyaudio
import array

from typing import List, Optional, Tuple, Union


logging.basicConfig(filename='audiostream_logs.log', level=logging.INFO)

_MSG_PREFIX = b'PRE'
_MSG_SUFIX = b'SUF'


def _compose_message(message: bytes) -> bytes:
    """ Composes a message that is ready to be sent over the socket or be joined with other messages.
    Should not be called directly.

    :param message: message to be sent over the socket
    :return: a message that is ready to be sent over the socket or be joined with other messages.
    """
    return _MSG_PREFIX + message + _MSG_SUFIX


def _decompose_message(message: bytes) -> List[bytes]:
    """ Reads the raw socket message and decomposes it into a list of understandable messages or audio frames.
    Should not be called directly.

    :param message: raw socket message
    :return: list of messages or audio frames
    """
    pattern = _MSG_PREFIX + b'(.*?)' + _MSG_SUFIX
    pat = re.compile(pattern)
    return pat.findall(message)


class AudioProperties:
    """ Class representing the audio properties of an audio file, it requires sampling, channels and length or
    the number of frames available in the audio file as one can be derived from the other.
    The class offers a cast to string using __str__ which will provide a representation that is useful purely for logging purposes.
    It also offers a conversion to a bytes message :func:`~audiostream.AudioProperties.to_bytes_message` which is used when transfering the class over the sockets.
    Apart from standard initialization the class can also be instantiated using the static :func:`~audiostream.AudioProperties.from_bytes_message`
    method which will return an instance of AudioProperties class created using a socket message made by :func:`~audiostream.AudioProperties.to_bytes_message` method.

    :param sampling: sampling rate of the associated audio file

    :param channels: number of channels used by the associated audio file

    :param length: length of the audio file in seconds

    :param frames_in_audio: number of frames making up the audio file

    """
    _SAMPLING_RATE = b'SAMPLING_RATE_'
    _CHANNELS = b'CHANNELS_'
    _LENGTH = b'LENGTH_'
    _FRAMES_IN_AUDIO = b'FRAMES_IN_AUDIO_'

    def __init__(self, sampling, channels, length=None, frames_in_audio=None):
        self.sampling = sampling
        self.channels = channels

        if not length and not frames_in_audio:
            raise AssertionError("Length or frames_in_audio must be provided")
        if length and frames_in_audio:
            self.length = length
            self.frames_in_audio = frames_in_audio
        elif length:
            self.length = length
            self.frames_in_audio = self.sampling * self.length
        elif frames_in_audio:
            self.frames_in_audio = frames_in_audio
            self.length = self.frames_in_audio / self.sampling

    def __str__(self):
        return f"\nNumber of frames: {self.frames_in_audio}" \
               f"\nSampling rate: {self.sampling}" \
               f"\nLength in seconds: {self.length}" \
               f"\nNumber of channels: {self.channels}"

    def to_bytes_message(self) -> List[bytes]:
        """ Converts the instance of the class into a list of byte messages which can be sent over the socket"""
        return [self._SAMPLING_RATE + b'%d' % int(self.sampling),
                self._CHANNELS + b'%d' % int(self.channels),
                self._LENGTH + b'%d' % int(self.length),
                self._FRAMES_IN_AUDIO + b'%d' % int(self.frames_in_audio)]

    @staticmethod
    def from_bytes_message(byte_messages: List[bytes]) -> AudioProperties:
        """ Creates and returns an instance of AudioProperties class out of a bytes message created using
        :func:`~audiostream.AudioStreamClient.to_bytes_message` method

        :param byte_messages: list of bytes containing the data about sample rate, channels
         and length or frames in audio of an audio file.
        :type byte_messages: List[bytes]
        """
        sampling_rate = None
        channels = None
        length = None
        frames_in_audio = None
        for byte_message in byte_messages:
            if AudioProperties._SAMPLING_RATE in byte_message:
                sampling_rate = int(byte_message[len(AudioProperties._SAMPLING_RATE):].decode('utf-8'))
            if AudioProperties._CHANNELS in byte_message:
                channels = int(byte_message[len(AudioProperties._CHANNELS):].decode('utf-8'))
            if AudioProperties._LENGTH in byte_message:
                length = int(byte_message[len(AudioProperties._LENGTH):].decode('utf-8'))
            if AudioProperties._FRAMES_IN_AUDIO in byte_message:
                frames_in_audio = int(byte_message[len(AudioProperties._FRAMES_IN_AUDIO):].decode('utf-8'))
        return AudioProperties(sampling=sampling_rate, channels=channels, length=length, frames_in_audio=frames_in_audio)


class MessageType:
    """ Class determining possible types of messages sent from client to server and generic answers
    the server might return apart from audio data
    """
    GIVE = b'GIVE_'
    STREAM = b'STREAM_'

    ENDOFMESSAGE = b'END OF SOCKET MESSAGE'
    ENDOFAUDIOFILE = b'END OF AUDIO FILE'


class MessageCommand:
    """ Class determining possible extensions of basic message types """
    AUDIO_PROPERTIES = b'AUDIO_PROPERTIES_'
    AUDIOFILESLIST = b'AUDIO_FILES_LIST'


class AudioStreamClient:
    """ This is client class used for communicating with the server.
      It provides the means for requesting audio files list, retrieving an audio files properties and
      requesting a stream of an audio file. It contains a basic implementation of an audio output allowing for playing the
      streamed data using the pyaudio library in the form of :func:`~audiostream.AudioStreamClient.initialize_audio_playback` and
      :func:`~audiostream.AudioStreamClient.play_streamed_data` methods which can be overriden.
     """
    def __init__(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        """ Needed to save them for auto reconnection """
        self.__host = None
        self.__port = None

        self._stream_message_size = 0


        self._py_audio = None
        self._stream = None

    def initialize_audio_playback(self, audio_properties: AudioProperties) -> None:
        """ Method for initializing the audio playback based on provided audio properties,
        should be overridden along with :func:`~audiostream.AudioStreamClient.play_streamed_data`
        if custom audio playback is created.

        :param audio_properties: instance of audio properties used for initializing audio playback
        :type audio_properties: AudioProperties
        """
        self._py_audio = pyaudio.PyAudio()
        self._stream = self._py_audio.open(format=pyaudio.paInt32,
                                           channels=audio_properties.channels,
                                           rate=audio_properties.sampling,
                                           output=True)

    def play_streamed_data(self, audio_frames: List[bytes]) -> None:
        """ Method for playing the audio based on provided audio frame,
        should be overridden along with :func:`~audiostream.AudioStreamClient.play_streamed_data`
        if custom audio playback is created.

        :param audio_frames: a list of audio frames each containing one discrete time step in the audio file.
        :type audio_frames: list
        """
        intel = array.array('l')
        for audio_frame in audio_frames:
            intel.append(int(audio_frame))
        self._stream.write(intel.tobytes())

    def connect(self, host: str, port: int) -> None:
        """ Attempts connection to a server at a given host and port

        :param host: ip address of the host, should be a string in the format of '127.0.0.1'
        :type host: str

        :param port: port over which the connection should be made
        :type port: int
        """
        logging.info(f'Connecting to {host}:{port}')
        try:
            self._socket.connect((host, port))
        except ConnectionRefusedError:
            logging.error(f"Couldn't connect to server, make sure it's running before connecting")
            raise

        self.__host = host
        self.__port = port

    def close(self) -> None:
        """ Closes the socket, no need to notify server of the event.
        """
        self._socket.close()

    def _read_message(self, data_size: int = 1024) -> List[bytes]:
        """ Retrieves the specified number of bytes from the socket and returns a list of decomposed messages.
        Should not be called directly.

        :param data_size: number of bytes read from socket
        :return: list of decomposed messages from the read socket bytes
        """
        message = self._socket.recv(data_size)
        return _decompose_message(message)

    def _send_message(self, message_type: bytes, message_command: Optional[bytes] = None, audio_file: Optional[str] = None) -> None:
        """ Sends a :class:`audiostream.MessageCommand` of the specified :class:`audiostream.MessageType` or
         associated with specified audio file to the server. Should not be called directly.

        :param message_type: attribute from the :class:`audiostream.MessageType` class
        :param message_command:  optional attribute from the :class:`audiostream.MessageCommand` class
        :param audio_file: optional name of the audio file associated with the request
        """
        if not message_command and not audio_file:
            raise AssertionError("Can't send a message using only its type")
        message = message_type
        if message_command:
            message += message_command
        if audio_file:
            if type(audio_file) is not bytes:
                audio_file = audio_file.encode('utf-8')
            message += audio_file
        message = _compose_message(message)
        logging.info(f"Sending message to server {message}")
        self._socket.send(message)

    def _request_feature(self, command: bytes, audio_file: Optional[str] = None, size: int = 1024) -> List[bytes]:
        """ Requests a feature from the client specified by the :class:`audiostream.MessageCommand` class and
        an optional associated audio file, after sending a request for the feature
        it awaits until server sends the response. Should not be called directly.

        :param command: attribute from the :class:`audiostream.MessageCommand` class
        :param audio_file: optional name of the audio file associated with the request
        :param size: expected size of the response message
        :return: decomposed server response
        """
        self._send_message(MessageType.GIVE, message_command=command, audio_file=audio_file)
        return self._await_messages(size)

    def _await_messages(self, size: int = 1024) -> List[bytes]:
        """ Awaits incoming message from the server and returns a decomposed list of actual messages
        contained in the socket message. Should not be called directly.

        :param size: size of the incoming message
        :return: list of decomposed messages
        """
        self._socket.setblocking(True)
        messages_retrieved = self._read_message(size)
        self._socket.setblocking(False)
        return messages_retrieved

    def retrieve_audio_files_list(self) -> List[str]:
        """ Asks the server for list of audio files available for streaming
        :return: list of audio files
        """
        logging.info("Requesting audio files from server")
        self._send_message(MessageType.GIVE, message_command=MessageCommand.AUDIOFILESLIST)
        audio_file_list = []
        while True:
            try:
                unpacked = self._read_message()
            except socket.error:
                continue
            for unpacked_message in unpacked:
                if MessageType.ENDOFMESSAGE in unpacked_message:
                    logging.info(f"Retrieved audio files {audio_file_list}")
                    return audio_file_list
                audio_file_list.append(unpacked_message.decode('utf-8'))


    def retrieve_audio_file_properties(self, audio_file: str) -> AudioProperties:
        """ Asks the server for properties of provided audio file

        :param audio_file: the audio file for which we want to retrieve properties
        :type audio_file: str

        :return: audio properties of the requested audio file
        """
        byte_properties = self._request_feature(MessageCommand.AUDIO_PROPERTIES, audio_file=audio_file)
        return AudioProperties.from_bytes_message(byte_properties)

    def start_audio_stream(self, audio_file: str) -> None:
        """ Tells servers to start streaming the provided audio file,
        first message back is the size of incoming messages,
        every next message is a combination of one or more audio frames
        up until receiving ENDOFAUDIOFILE message indicating all audio frames have been transferred

        :param audio_file: the audio file which we want to start the stream for
        :type audio_file: str
        """
        self._send_message(MessageType.STREAM, audio_file=audio_file)
        self._stream_message_size = int(self._await_messages()[0].decode('utf-8'))
        logging.info(f"Received stream message size {self._stream_message_size}")

    def retrieve_audio_stream(self) -> Union[List[bytes], None]:
        """ Should be called in a loop to retrieve the audio frames to stream,
         will return None if no data is ready for retrieval. """
        try:
            message = self._read_message(self._stream_message_size)
        except socket.error:
            return None
        return message


class AudioStreamServer:
    """ This is server class used for communicating with clients.
      It provides the means for creating a new server instance, accepting new connections and
      handling requests from clients including streaming of audio frames.
     """
    def __init__(self):
        self._socket = socket.socket()

        self._accept_connections_thread = None
        self._connected_clients_lock = threading.Lock()
        self._connected_clients = []

        self._open_stream_lock = threading.Lock()
        self._open_streams = dict()


    def create_server(self, host: str, port: int, max_connections: int = 5) -> None:
        """ Creates a new server socket using the specified parameters.

        :param host: address at which the server is hosted

        :param port: port at which the server is available

        :param max_connections: the maximum ammount of connections that the server will accept simultaneously.
        """
        logging.info(f"Binding server to {host}:{port}")
        self._socket.bind((host, port))
        self._socket.listen(max_connections)


    def get_connected_clients(self) -> List[Tuple[socket.socket, Tuple[str, int]]]:
        """ Returns a list of currently connected client sockets and their addresses """
        self._connected_clients_lock.acquire(blocking=True)
        connected_clients_copy = self._connected_clients.copy()
        self._connected_clients_lock.release()
        return connected_clients_copy

    def _accept_new_connections(self) -> None:
        """ Internal method to be used as a thread spawned by :func:`~audiostream.AudioStreamServer.accept_new_connections`
         which will keep accepting new client connections in a loop
        """
        while True:
            client, addr = self._socket.accept()
            logging.info(f"Accepted new client connection: {addr}")
            client.setblocking(False)
            client.settimeout(1)
            self._connected_clients_lock.acquire(blocking=True)
            self._connected_clients.append((client, addr))
            self._connected_clients_lock.release()

    def accept_new_connections(self) -> None:
        """ Creates a daemon thread for accepting new client connections,
        if the thread still exists it won't spawn another."""
        if not self._accept_connections_thread or not self._accept_connections_thread.is_alive():
            self._accept_connections_thread = threading.Thread(target=self._accept_new_connections, daemon=True)
            self._accept_connections_thread.start()


    def _sanitize_message(self, message: Union[int, float, str, bytes]) -> bytes:
        """ Ensures correct message format was provided and transforms the message into bytes
        to be composed into a socket message, not to be used directly.

        :param message: an int, float, utf-8 str or bytes message to be sanitized.
        :return: bytes which can be composed into a message for sending over the socket
        """
        if type(message) is int:
            message = b'%d' % message
        if type(message) is float:
            message = b'%f' % message
        if type(message) is str:
            message = message.encode('utf-8')
        if type(message) is not bytes:
            raise TypeError(f"Messages sent can only be of type bytes, int or float. Got {type(message)}")
        return message

    def _send_message_to_client(self, client: socket.socket, message) -> None:
        """ Sends message to specified client, should not be called directly.

        :param client: client to which the message sent

        :param message: message which is of type int, float, str, or bytes
        """
        message = self._sanitize_message(message)
        logging.info(f"Sending message to client {message}")

        print(_compose_message(message))
        client.send(_compose_message(message))

    def send_audio_files_list_to_client(self, client: socket.socket, audio_files_list: List[str]) -> None:
        """ Sends one by one audio files which are available for streaming to the provided client
        """
        for audio_file in audio_files_list:
            audio_file = audio_file.encode('utf-8')
            self._send_message_to_client(client, audio_file)
        self._send_message_to_client(client, MessageType.ENDOFMESSAGE)

    def unpack_request(self, message: bytes) -> (bytes, bytes, str):
        """ Translates the received client message to a known combination of commands from :class:`audiostream.MessageType`,
         :class:`audiostream.MessageCommand` and an optional audio file context.

         :return: returns a tuple containing :class:`audiostream.MessageType`, :class:`audiostream.MessageCommand`, and
          optionally name of the associated audio file, None if not provided
        """
        _type, _command, _audio_file = None, None, None
        if message.startswith(MessageType.GIVE):
            _type = MessageType.GIVE
        elif message.startswith(MessageType.STREAM):
            _type = MessageType.STREAM
            _audio_file = message[len(_type):].decode('utf-8')
        if _type:
            if message.startswith(MessageCommand.AUDIO_PROPERTIES, len(_type)):
                _command = MessageCommand.AUDIO_PROPERTIES
            if message.startswith(MessageCommand.AUDIOFILESLIST, len(_type)):
                _command = MessageCommand.AUDIOFILESLIST
        if _command and _command is not MessageCommand.AUDIOFILESLIST:
            if len(message) != len(_type) + len(_command):
                _audio_file = message[len(_type)+len(_command):].decode('utf-8')

        return _type, _command, _audio_file

    def _stream_audio_frames_to_client(self, client: socket.socket, frames: List[int], frames_in_message: int = 100) -> None:
        """ Streams the audio frames to the provided client in a loop until all frames are sent or client disconnects,
         for the time of streaming the audio frames no other messages should be sent to client,
         sends the :class:`audiostream.MessageType.ENDOFAUDIOFILE` after all frames have been sent.

        :param client: the client for which the frames should be sent

        :param frames: the audio frames which will be sent to the client

        :param frames_in_message: the amount of frames which will be sent in a single message,
         tweaking this parameter can provide better transfer efficiency depending on the situation
        """
        try:
            client.setblocking(True)
            counter = 0
            frames_message = b''
            msg_size = frames_in_message * len(_MSG_PREFIX + b'-2147483647' + _MSG_SUFIX)
            logging.info(f"Message size {msg_size}")
            client.send(_compose_message(b'%d' % msg_size))

            for frame in frames:
                counter += 1
                sanitized_frame = self._sanitize_message(frame)
                frames_message += _compose_message(sanitized_frame)
                if counter >= frames_in_message:
                    counter = 1
                    fillout = msg_size - len(frames_message)
                    frames_message += b'0' * fillout
                    client.send(frames_message)
                    frames_message = b''
            self._send_message_to_client(client, MessageType.ENDOFAUDIOFILE)
            client.setblocking(False)
        except ConnectionResetError:
            logging.info(f"Connection has been closed by client {client.getsockname()}")

            self._connected_clients_lock.acquire(blocking=True)
            for connected_client in self._connected_clients.copy():
                if client == connected_client[0]:
                    logging.info(f"Removed client from existing connections")
                    self._connected_clients.remove(connected_client)
            self._connected_clients_lock.release()


    def stream_audio_frames_to_client(self, client: socket.socket, addr: Tuple[str,int], frames) -> None:
        """ Creates a new thread streaming audio frames to provided client

        :param client: client which will receive the audio frames

        :param addr: address of the client which will be receiving the audio frames, it will be used later as
         the clients identifier for class:`audiostream.AudioStreamServer.get_currently_streaming_clients.` method

        :param frames: audio frames which will be streamed to the client
        """
        logging.info(f"Starting new steam audio frames thread for {client}")
        stream_frames_thread = threading.Thread(target=self._stream_audio_frames_to_client, args=(client, frames,), daemon=True)
        self._open_stream_lock.acquire(blocking=True)
        self._open_streams[addr] = stream_frames_thread
        stream_frames_thread.start()
        self._open_stream_lock.release()
        print(f"Thread started")

    def get_currently_streaming_clients(self) -> List[int]:
        """ Returns a list of clients which are currently streaming audio from the server.
         :return: List of addresses of currently streaming clients
        """

        self._open_stream_lock.acquire(blocking=True)
        for open_stream in self._open_streams.copy():
            if not self._open_streams[open_stream].isAlive():
                self._open_streams.pop(open_stream)
        streaming_clients = [addr for addr in self._open_streams]
        self._open_stream_lock.release()
        return streaming_clients

    def send_audio_file_properties(self, client: socket.socket, audio_properties: AudioProperties) -> None:
        """ Sends audio properties to provided client, should be called in response to
        :func:`~audiostream.AudioStreamClient.retrieve_audio_file_properties` request

        :param client: client which requested the audio file properties

        :param audio_properties: instance of :class:`audiostream.AudioProperties` class which will be sent to the user
        """
        properties_message = b''
        for audio_property in audio_properties.to_bytes_message():
            sanitized_message = self._sanitize_message(audio_property)
            properties_message += _compose_message(sanitized_message)

        client.send(properties_message)

    def retrieve_message_from_client(self, client: socket.socket, message_size_buff=1024) -> Optional[List[bytes]]:
        """ Checks for a new message from the given client, returns none if no message is awaiting or a list of commands

        :param client: client for which we are checking if a new message has arrived

        :param message_size_buff: size of the buffer used when retrieving a message, default value is 1024 which
         should be more than sufficient if client keeps using :class:`audiostream.MessageType` and :class:`audiostream.MessageCommand`
        :type message_size_buff: int

        :return: list of decomposed messages retrieved from the client.
        """
        try:
            message = client.recv(message_size_buff)
            print(message)
        except socket.error:
            return None
        if message:
            logging.info(f"Received new message from client: {client.getsockname()}: {message}")
        return _decompose_message(message)
