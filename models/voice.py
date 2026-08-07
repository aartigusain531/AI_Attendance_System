import os
import wave
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write


class VoiceRecorder:

    def __init__(self):

        self.sample_rate = 16000
        self.channels = 1
        self.duration = 5

    # ----------------------------------

    def record(self, filename):

        """
        Record voice and save as WAV
        """

        print("\n===================================")
        print(" Voice Recording Started")
        print(" Speak clearly...")
        print("===================================\n")

        recording = sd.rec(
            int(self.duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="int16"
        )

        sd.wait()

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        write(
            filename,
            self.sample_rate,
            recording
        )

        print("\nVoice Saved Successfully.")
        print(filename)

        return filename

    # ----------------------------------

    def play_info(self):

        print("\nRecording Settings")
        print("------------------------")
        print(f"Sample Rate : {self.sample_rate}")
        print(f"Channels    : {self.channels}")
        print(f"Duration    : {self.duration} sec")