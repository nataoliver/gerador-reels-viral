import os
import shutil
import subprocess

# import soundfile as sf
# from kittentts import KittenTTS as KittenModel

from config import ROOT_DIR, get_tts_voice

# KITTEN_MODEL = "KittenML/kitten-tts-mini-0.8"
# KITTEN_SAMPLE_RATE = 24000

class TTS:
    def __init__(self) -> None:
        # self._model = KittenModel(KITTEN_MODEL)
        # self._voice = get_tts_voice()
        pass

    def synthesize(self, text, output_file=os.path.join(ROOT_DIR, ".mp", "audio.wav")):
        # audio = self._model.generate(text, voice=self._voice)
        # sf.write(output_file, audio, KITTEN_SAMPLE_RATE)
        
        mudo_path = os.path.join(ROOT_DIR, "mudo.mp3")
        
        # OBRIGATÓRIO (MODERN_REELS_ENGINEER): buscar mudo.mp3 na raiz ou gerar silêncio via FFmpeg
        if os.path.exists(mudo_path):
            shutil.copy(mudo_path, output_file)
        else:
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", 
                "-t", "3", output_file
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        return output_file
