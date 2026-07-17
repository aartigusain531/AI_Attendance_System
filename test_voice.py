from models.voice import VoiceRecorder

recorder = VoiceRecorder()

recorder.play_info()

recorder.record(
    "dataset/voices/TestStudent.wav"
)