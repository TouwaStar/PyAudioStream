from unittest.mock import MagicMock
from PyAudioStream.audiostream import AudioStreamClient, AudioProperties, MessageCommand, MessageType, _compose_message

SAMPLING = 44100
CHANNELS = 2
LENGTH = 120
FRAMES_IN_AUDIO = 5292000
AUDIO_PROPERTIES = AudioProperties(sampling=SAMPLING, channels=CHANNELS, frames_in_audio=FRAMES_IN_AUDIO,
                                   length=LENGTH)


def test_initialize_playback():
    test_client = AudioStreamClient()
    test_client.initialize_audio_playback(AUDIO_PROPERTIES)
    assert test_client._stream


def test_playback():
    test_client = AudioStreamClient()
    test_client._stream = MagicMock()
    test_client.play_streamed_data([1])
    assert test_client._stream.called_once()


def test_connecting():
    test_client = AudioStreamClient()
    test_client._socket = MagicMock()
    host = '1'
    port = 1
    test_client.connect(host, port)
    assert test_client._socket.connect.called_once_with((host, port))


def test_feature_request():
    expected_result = [b'test']
    test_client = AudioStreamClient()
    test_client._socket = MagicMock()
    test_client._read_message = MagicMock()
    test_client._read_message.return_value = expected_result
    result = test_client._request_feature(MessageCommand.AUDIO_PROPERTIES)
    assert result == expected_result


def test_send_message():
    test_client = AudioStreamClient()
    test_client._socket = MagicMock()
    message_type = MessageType.GIVE
    message_command = MessageCommand.AUDIO_PROPERTIES
    test_client._send_message(message_type=message_type, message_command=message_command)
    assert test_client._socket.send.called_once_with(_compose_message(message_type+message_command))


def test_send_message_audio_file():
    test_client = AudioStreamClient()
    test_client._socket = MagicMock()
    message_type = MessageType.GIVE
    message_command = MessageCommand.AUDIO_PROPERTIES
    audio_file_name = 'abc'
    test_client._send_message(message_type=message_type, message_command=message_command, audio_file=audio_file_name)
    assert test_client._socket.send.called_once_with(_compose_message(message_type+message_command+b'_'+audio_file_name.encode('utf-8')))