import os
import sys

# ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import match_voice

VOICE_DIR = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'voices')
# choose a sample that exists (pick first .webm/.wav file)
sample = None
for fname in os.listdir(os.path.join(os.path.dirname(__file__), '..', 'dataset', 'voices')):
    if fname.lower().endswith(('.webm', '.wav', '.ogg', '.mp4')):
        sample = os.path.join(VOICE_DIR, fname)
        break
if not sample:
    raise SystemExit('No voice files found in dataset/voices')

print('ROOT=', ROOT)
print('VOICE_DIR=', VOICE_DIR)
print('sample path=', sample)

try:
    with open(sample, 'rb') as f:
        data = f.read()
except Exception as e:
    print('Error opening sample:', e)
    raise

roll, score = match_voice(data)
print('Matched roll:', roll)
print('Score:', score)
