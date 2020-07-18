import pytest
from PyAudioStream.audiostream import AudioProperties

SAMPLING = 44100
CHANNELS = 2
LENGTH = 120
FRAMES_IN_AUDIO = 5292000

BYTES_MESSAGE = [AudioProperties._SAMPLING_RATE + b'%d' % SAMPLING,
                  AudioProperties._CHANNELS + b'%d' % CHANNELS,
                  AudioProperties._LENGTH + b'%d' % LENGTH,
                  AudioProperties._FRAMES_IN_AUDIO + b'%d' % FRAMES_IN_AUDIO]


def test_initialization_with_len():
    test_properties = AudioProperties(sampling=SAMPLING, channels=CHANNELS, length=LENGTH)
    assert test_properties.frames_in_audio == FRAMES_IN_AUDIO


def test_initialization_with_frames():
    test_properties = AudioProperties(sampling=SAMPLING, channels=CHANNELS, frames_in_audio=FRAMES_IN_AUDIO)
    assert test_properties.length == LENGTH


def test_initialization_with_all():
    test_properties = AudioProperties(sampling=SAMPLING, channels=CHANNELS, frames_in_audio=FRAMES_IN_AUDIO,
                                      length=LENGTH)
    assert test_properties.length == LENGTH
    assert test_properties.frames_in_audio == FRAMES_IN_AUDIO


def test_initialization_fail_assertion():
    with pytest.raises(AssertionError):
        AudioProperties(sampling=SAMPLING, channels=CHANNELS)


def test_conversion_to_bytes():
    test_properties = AudioProperties(sampling=SAMPLING, channels=CHANNELS, frames_in_audio=FRAMES_IN_AUDIO,
                                      length=LENGTH)
    assert test_properties.to_bytes_message() == BYTES_MESSAGE


def test_from_bytes_message():
    test_properties = AudioProperties.from_bytes_message(BYTES_MESSAGE)
    assert test_properties.length == LENGTH
    assert test_properties.frames_in_audio == FRAMES_IN_AUDIO
    assert test_properties.sampling == SAMPLING
    assert test_properties.channels == CHANNELS