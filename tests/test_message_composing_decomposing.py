from PyAudioStream.audiostream import _compose_message, _decompose_message, _MSG_PREFIX, _MSG_SUFIX

TEST_STRING = b'TEST_STRING'
TEST_MULTIPLE_MESSAGES = _MSG_PREFIX + b'ABC' + _MSG_SUFIX +_MSG_PREFIX + b'BCD' + _MSG_SUFIX


def test_compose():
    assert _compose_message(TEST_STRING) == _MSG_PREFIX + TEST_STRING + _MSG_SUFIX


def test_decompose():
    expected_result = [b'ABC',b'BCD']
    assert _decompose_message(TEST_MULTIPLE_MESSAGES) == expected_result

