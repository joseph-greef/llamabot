
import traceback

import discord
import pydub


class MixedAudio(discord.AudioSource):
    def __init__(self, sound_path):
        self.__active_sounds = {
            str(sound_path): pydub.AudioSegment.from_file(sound_path)
        }

        self.__encoder = discord.opus.Encoder(
            application='audio',
            bitrate=128,
            fec=True,
            expected_packet_loss=0.15,
            bandwidth='full',
            signal_type='auto',
        )
        pass


    def add_sound(self, sound_path):
        self.__active_sounds[str(sound_path)] = pydub.AudioSegment.from_file(sound_path)


    def cleanup(self):
        pass


    def is_opus(self):
        return True


    def read(self):
        if self.__active_sounds:
            mixed = pydub.AudioSegment.silent(duration=20, frame_rate=48000)

            #Iterate through a copy of the dict so we can modify the dict
            for path, segment in list(self.__active_sounds.items()):
                #Pull out 20ms of each chunk and overlay it onto the silence
                chunk = segment[:20]
                self.__active_sounds[path] = segment[20:]

                mixed = mixed.overlay(chunk)

                #If we expend the sample remove it from active
                if len(self.__active_sounds[path]) == 0:
                    del self.__active_sounds[path]

            raw_data = mixed.raw_data
            expected_bytes = discord.opus.Encoder.SAMPLES_PER_FRAME * 2 * 16
            if len(raw_data) < expected_bytes:
                raw_data += b'\00' * (expected_bytes - len(raw_data))
            elif len(raw_data) > expected_bytes:
                raw_data = raw_data[:expected_bytes]
            return self.__encoder.encode(raw_data,
                                         discord.opus.Encoder.SAMPLES_PER_FRAME)

        else:
            return b''

