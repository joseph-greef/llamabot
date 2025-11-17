
import traceback

import discord
import pydub


class MixedAudio(discord.AudioSource):
    def __init__(self, sound_path):
        self.__active_sounds = [
            pydub.AudioSegment.from_file(sound_path)
        ]

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
        self.__active_sounds.append(pydub.AudioSegment.from_file(sound_path))


    def cleanup(self):
        pass


    def is_opus(self):
        return True


    def read(self):
        if self.__active_sounds:
            #base silence onto which to mix
            mixed = pydub.AudioSegment.silent(duration=20, frame_rate=48000)

            sounds_to_delete = []
            for i in range(len(self.__active_sounds)):
                #Pull out 20ms of each chunk and overlay it onto the silence
                chunk = self.__active_sounds[i][:20]
                self.__active_sounds[i] = self.__active_sounds[i][20:]
                mixed = mixed.overlay(chunk)

                #If we expend the sample mark it to remove from active
                if len(self.__active_sounds[i]) == 0:
                    sounds_to_delete.append(i)

            #delete from the back of the list to the front
            sounds_to_delete.reverse()
            for i in sounds_to_delete:
                del self.__active_sounds[i]

            #get the raw data and pad/crop it to the exact length
            raw_data = mixed.raw_data
            expected_bytes = discord.opus.Encoder.SAMPLES_PER_FRAME * 2 * 16
            if len(raw_data) < expected_bytes:
                raw_data += b'\00' * (expected_bytes - len(raw_data))
            elif len(raw_data) > expected_bytes:
                raw_data = raw_data[:expected_bytes]

            #opus encode the padded data
            return self.__encoder.encode(raw_data,
                                         discord.opus.Encoder.SAMPLES_PER_FRAME)

        else:
            #empty byte string is the signal for no more data
            return b''
