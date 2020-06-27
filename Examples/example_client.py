import sys
import logging

from PyAudioStream.audiostream import AudioStreamClient, MessageType

logging.basicConfig(filename='audiostream_logs.log', level=logging.INFO)


class ExampleClient(AudioStreamClient):
    def __init__(self):
        super().__init__()
        self.songs = dict()
        self._stream = None


    def choose_song(self):
        print("PICK SONG NUMBER")
        song_list = list(self.songs.keys())
        for i, song in enumerate(song_list):
            print(f"{i}. {song}")
        song_pick = int(input())
        return song_list[song_pick]


    def play_audio(self, ):
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
                        logging.info("Received all of data")
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


def main():
    host = '127.0.0.1'
    port = 8900

    if len(sys.argv) > 1:
        host = sys.argv[1]

    if len(sys.argv) > 2:
        port = int(sys.argv[2])

    client = ExampleClient()
    client.connect(host, port)

    while True:
        song_list = client.retrieve_audio_files_list()
        for song in song_list:
            if song not in client.songs:
                client.songs[song] = None

        chosen_song_title = client.choose_song()

        if not client.songs[chosen_song_title]:
            client.songs[chosen_song_title] = client.retrieve_audio_file_properties(chosen_song_title)

        client.start_audio_stream(chosen_song_title)
        client.initialize_audio_playback(client.songs[chosen_song_title])
        logging.info(f"Playing audio {chosen_song_title}")
        print(f"Playing audio {chosen_song_title}")
        client.play_audio()



if __name__ == "__main__":
    main()


