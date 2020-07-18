# PyAudioStream
A library allowing for streaming and playback of audio files from server to client over a socket connection.

## Usage
Working demo is provided in the Examples folder.
### Server

Create a server and start accepting new connections
```
class ExampleServer(AudioStreamServer):
    ...
    ...

server = ExampleServer()
server.create_server(host=host, port=port)
server.accept_new_connections()
```

Retrieve messages from connected clients
```
for client, addr in server.get_connected_clients():
    message = server.retrieve_message_from_client(client)
```

Unpack the message and respond accordingly
```
for request in message:
    request_type, request_command, audio_file_context = server.unpack_request(request)
    if request_type == MessageType.STREAM:
        server.handle_audio_frames_request(client, addr, audio_file_context)
    if request_command == MessageCommand.AUDIOFILESLIST:
        self.send_audio_files_list_to_client(client, self._get_audio_files_list())
    if request_command == MessageCommand.AUDIO_PROPERTIES:
        self.send_audio_file_properties(client, self._get_audio_properties(audio_file_context))
```

Example usage provides a basic implementation of reading the audio file and its frames, you will have to use the
code from sample or create your own solution to this.
```
def read_audio_file(self, audio_file_path):
    audio_file = soundfile.SoundFile(audio_file_path)
    return audio_file

def _prepare_frames_list(self, frames_array):
    ready_frames = []
    logging.info(f"Frames to send {frames_array}")
    for frame in frames_array:
        for frame_for_channel in frame:
            ready_frames.append(int(frame_for_channel))
    return ready_frames
```

### Client

Create a client instance and connect to server
```
class ExampleClient(AudioStreamClient):
    ...
    ...

client = ExampleClient()
client.connect(host, port)
```

Ask the server for available audio files
```
song_list = client.retrieve_audio_files_list()
```

Retrieve the desired audio files properties
```
chosen_song_title = client.retrieve_audio_file_properties(chosen_song_title)
```

Request the server to start streaming audio frames
```
client.start_audio_stream(chosen_song_title)
```

Retrieve the audio frames and play them in a loop until the audio playback is finished
```
played_frame = 0

data = []
received_all_data = False
while True:
    if not received_all_data:
        audio_data = self.retrieve_audio_stream()

        if not audio_data:
            pass
        else:
            if MessageType.ENDOFAUDIOFILE in audio_data:
                received_all_data = True
            else:
                data.append(audio_data)


    if received_all_data:
        if len(data) - 1 <= played_frame:
            break

    if len(data) - 1 >= played_frame:
        if MessageType.ENDOFAUDIOFILE in data[played_frame]:
            break

        self.play_streamed_data(data[played_frame])
        played_frame += 1
```

client comes with basic audio playback functionality using PyAudio in the form of initialize_audio_playback and
play_streamed_data methods.

## Regenerating documentation:

inside docs subdirectory
> make html 
