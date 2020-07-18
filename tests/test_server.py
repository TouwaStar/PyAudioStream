import pytest
from unittest.mock import MagicMock, call
from PyAudioStream.audiostream import AudioStreamServer, MessageCommand, MessageType, _MSG_SUFIX, _MSG_PREFIX, \
    _compose_message


def test_retrieve_connected_clients():
    test_server = AudioStreamServer()
    connected_clients_list = [1, 2]
    test_server._connected_clients = connected_clients_list
    assert test_server.get_connected_clients() == connected_clients_list


def test_sanitize_message_ok():
    test_server = AudioStreamServer()
    exp_message = b'1'

    test_message = 1
    assert test_server._sanitize_message(test_message) == exp_message

    test_message = b'1'
    assert test_server._sanitize_message(test_message) == exp_message

    test_message = '1'
    assert test_server._sanitize_message(test_message) == exp_message

    exp_message = b'1.000000'
    test_message = 1.0
    assert test_server._sanitize_message(test_message) == exp_message


def test_sanititze_message_fail():
    test_server = AudioStreamServer()
    test_message = ['abc', 'def']
    with pytest.raises(TypeError):
        test_server._sanitize_message(test_message)


def test_unpack_request():
    test_server = AudioStreamServer()
    message = MessageType.GIVE + MessageCommand.AUDIO_PROPERTIES
    exp_result = (MessageType.GIVE, MessageCommand.AUDIO_PROPERTIES, None)
    assert test_server.unpack_request(message) == exp_result


def test_unpack_request_audio_file():
    test_server = AudioStreamServer()
    message = MessageType.GIVE + MessageCommand.AUDIO_PROPERTIES + b'_' + b'test'
    exp_result = (MessageType.GIVE, MessageCommand.AUDIO_PROPERTIES, 'test')
    assert test_server.unpack_request(message) == exp_result


def test_stream_audio_frames():
    test_server = AudioStreamServer()
    mock_client = MagicMock()
    mock_client.send = MagicMock()
    audio_frames = [1, 2, 3, 4, 5, 6]
    frames_in_message = 3
    test_server._stream_audio_frames_to_client(mock_client, audio_frames, frames_in_message)

    calls = [call(_compose_message(
        b'%d' % (frames_in_message * len(_MSG_PREFIX + b'2147483647' + _MSG_SUFIX) + frames_in_message))),
             call(b'PRE1SUFPRE2SUFPRE3SUF000000000000000000000000000000'),
             call(b'PRE4SUFPRE5SUF0000000000000000000000000000000000000'),
             call(_compose_message(MessageType.ENDOFAUDIOFILE))]
    mock_client.send.assert_has_calls(calls, any_order=False)
