from scipy.io import wavfile

import progression_producer
import synth
import numpy as np

vibe = 'demon-palace'  # raw_input("Pick a vibe\n")
# print ("You picked: " + vibe)
mood = 'porcelain'  # raw_input("Pick a mood\n")
spice = 'coriander'  # raw_input("Pick a spice\n")


output = progression_producer.Progression(vibe, mood, spice)
print(output)

octave = 4
duration = 20
chordDuration = duration / len(output.chordSequence)
synthChords = np.zeros((int(chordDuration * 44100)))

chords = []

for chord in output.chordSequence:
    synthNotesList = []
    for note in chord.notes:
        noteName = note.noteName
        synthNote = synth.Note(noteName, octave, chordDuration)
        synthNotesList.append(synthNote)

    print(len(synthNotesList))
    chords.append(synth.Chord(synthNotesList))

print(len(chords))

progression = np.array([])

for i in range(len(chords)):
    progression = np.append(progression, chords[i].wav)

# np.append(synthChords, synth.Chord(synthNotesList).wav)
# synthChords = synthChords + synth.Chord(synthNotesList).wav

wavfile.write('synthChords.wav', rate=44100, data=progression.astype(np.int16))

