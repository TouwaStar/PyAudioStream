import sys
import os
import soundfile
import logging
import time

from PyAudioStream.audiostream import AudioStreamServer, AudioProperties, MessageType, MessageCommand

DEFAULT_AUDIO_PATH = ""


class ExampleServer(AudioStreamServer):
    def __init__(self, path_to_audio_files):
        super().__init__()
        self.audio_files_path = path_to_audio_files

    def _get_audio_files_list(self):
        audio_files = []
        for filename in os.listdir(self.audio_files_path):
            audio_files.append(filename)
        return audio_files

    def read_audio_file(self, audio_file_path):
        audio_file = soundfile.SoundFile(audio_file_path)
        return audio_file

    def _get_audio_properties(self, audio_file_context):
        audio_file = self.read_audio_file(os.path.join(self.audio_files_path, audio_file_context))
        audio_properties = AudioProperties(sampling=audio_file.samplerate,
                                           channels=audio_file.channels,
                                           length=len(audio_file) / audio_file.samplerate)
        return audio_properties

    def handle_give_request(self, client, request_command, audio_file_context):
        if type(audio_file_context) == bytes:
            audio_file_context = audio_file_context.decode('utf-8')

        if request_command == MessageCommand.AUDIOFILESLIST:
            self.send_audio_files_list_to_client(client, self._get_audio_files_list())
        if request_command == MessageCommand.AUDIO_PROPERTIES:
            self.send_audio_file_properties(client, self._get_audio_properties(audio_file_context))

    def _prepare_frames_list(self, frames_array):
        ready_frames = []
        for frame in frames_array:
            for frame_for_channel in frame:
                ready_frames.append(int(frame_for_channel))
        return ready_frames

    def handle_audio_frames_request(self, client, addr, audio_file_context):
        audio_file = self.read_audio_file(os.path.join(self.audio_files_path, audio_file_context))
        self.stream_audio_frames_to_client(client, addr, self._prepare_frames_list(audio_file.read(dtype='int32')))


def main():
    path_to_audio_files = os.path.join(os.path.dirname(os.path.abspath(__file__)),'example_audio')
    host = '127.0.0.1'
    port = 8900

    if len(sys.argv) > 1:
        path_to_audio_files = sys.argv[1]

    if len(sys.argv) > 2:
        port = str(sys.argv[2])

    server = ExampleServer(path_to_audio_files)
    server.create_server(host=host, port=port)

    server.accept_new_connections()

    while True:
        time.sleep(0.5)
        for client, addr in server.get_connected_clients():
            currently_streaming_clients = server.get_currently_streaming_clients()
            if addr in currently_streaming_clients:
                continue
            message = server.retrieve_message_from_client(client)
            if not message:
                continue
            for request in message:
                logging.info(f"Handling request {request}")
                request_type, request_command, audio_file_context = server.unpack_request(request)
                if request_type == MessageType.GIVE:
                    server.handle_give_request(client, request_command, audio_file_context)
                if request_type == MessageType.STREAM:
                    server.handle_audio_frames_request(client, addr, audio_file_context)



if __name__ == "__main__":
    main()
