import numpy as np
from scipy import signal
from scipy.io import wavfile

# Returns the frequency of the nth key
def key_freq(n):
    return (2**(1 / 12))**(n - 49) * 440 # Hz

# Converts the note and octave into a frequency
def note_freq(octave, note):
    # The note progression of most octaves
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'] 

    if octave == 0:
        # 0th octave has only these 3
        notes = ['A', 'A#', 'B']

        if note in notes:
            freq = key_freq(notes.index(note) + 1)
            return freq
        else:
            print('Err: Note not in octave!')
            return 0

    elif octave == 8:
        # One note in the 8th octave
        notes = ['C']

        if note in notes:
            freq = key_freq(88)
            return freq
        else:
            print('Err: Note not in octave!')
            return 0

    else:
        # Else is a normal octave
        if note in notes:
            n = 12 * (octave - 1) + notes.index(note) + 4
            freq = key_freq(n)
            return freq
        else:
            print('Err: Note not in octave!')
            return 0

# This function is stolen, bit of a black box to me
def get_adsr_weights(frequency, duration, length, decay, sustain_level, sample_rate=44100):

    assert abs(sum(length)-1) < 1e-8
    assert len(length) ==len(decay) == 4
    
    intervals = int(duration*frequency)
    len_A = np.maximum(int(intervals*length[0]),1)
    len_D = np.maximum(int(intervals*length[1]),1)
    len_S = np.maximum(int(intervals*length[2]),1)
    len_R = np.maximum(int(intervals*length[3]),1)
    
    decay_A = decay[0]
    decay_D = decay[1]
    decay_S = decay[2]
    decay_R = decay[3]
    
    A = 1/np.array([(1-decay_A)**n for n in range(len_A)])
    A = A/np.nanmax(A)
    D = np.array([(1-decay_D)**n for n in range(len_D)])
    D = D*(1-sustain_level)+sustain_level
    S = np.array([(1-decay_S)**n for n in range(len_S)])
    S = S*sustain_level
    R = np.array([(1-decay_R)**n for n in range(len_R)])
    R = R*S[-1]
    
    weights = np.concatenate((A,D,S,R))
    smoothing = np.array([0.1*(1-0.1)**n for n in range(5)])
    smoothing = smoothing/np.nansum(smoothing)
    weights = np.convolve(weights, smoothing, mode='same')
    
    weights = np.repeat(weights, int(sample_rate*duration/intervals))
    tail = int(sample_rate*duration-weights.shape[0])
    if tail > 0:
        weights = np.concatenate((weights, weights[-1]-weights[-1]/tail*np.arange(tail)))
    return weights

# Gets the pure frequency of a note. No timbre
def get_note(octave, note, duration = 0, beats = 0, bpm = 0, waveform = 'sine', 
        harmonics = 10, sample_rate=44100, amplitude=4096, save = False):
    if duration == 0:
        duration = beats * (60 / bpm)

    frequency = note_freq(octave, note)
    freqs = []
    amps = []

    for n in range(1,harmonics):
        freqs.append((n + 1) * frequency)
        amps.append((0.5)**n * amplitude)

    t = np.linspace(0, duration, int(sample_rate*duration)) # Time axis

    if waveform == 'sine':
        wave = amplitude*np.sin(2*np.pi*frequency*t)

        for i in range(len(freqs)):
            wave += amps[i]*np.sin(2*np.pi*freqs[i]*t)
    elif waveform == 'sawtooth':
        wave = amplitude*signal.sawtooth(2 * np.pi * frequency * t)

        for i in range(len(freqs)):
            wave += amps[i]*signal.sawtooth(2 * np.pi * freqs[i] * t)
    elif waveform == 'square':
        wave = amplitude*signal.square(2*np.pi*frequency*t)

        for i in range(len(freqs)):
            wave += amps[i]*signal.square(2*np.pi*freqs[i]*t)

    return wave, frequency

# Adds the timbre of a piano to the pure frequency
class Note:
    def __init__(self, note, octave, duration, waveform = 'sine', adsr = [0.05, 0.25, 0.55, 0.15], 
            harmonics = 10, sustain_level = 0.1, decay = [0.085, 0.02, 0.005, 0.1], save = False):
        # vvv This is important but you dont need to worry about it vvv
        self.octave = octave
        self.note = note
        self.duration = duration
        self.waveform = waveform
        self.adsr = adsr
        self.harmonics = harmonics
        self.sustain_level = sustain_level
        self.decay = decay
        self.save = save
        # ^^^ This stuff ^^^

        # This just gets us a raw pitch pipe note with no adsr
        wav, f = get_note(self.octave, self.note, self.duration, 
                waveform = self.waveform, harmonics = self.harmonics, save = self.save)
        # This gets us the weights for the adsr
        weights = get_adsr_weights(f, self.duration, self.adsr, decay = self.decay, 
                sustain_level = self.sustain_level)
    
        # Multiply the wave by the weights and normalize amplitude to get the final thing
        dat = wav * weights
        dat = dat * (4096/np.max(dat))

        # If the user wants to save the wav, save the wav
        if save:
            wavfile.write(('' + str(note) + str(octave) + '.wav'), rate=44100, data=dat.astype(np.int16))

        # Can now reference a note C4 with C4.wav to get the sine wave data
        self.wav = dat

class Chord():
    # args is a tuple with all the input variables
    def __init__(self, noteList):
        # Note: this will only work if we assume that the duration of all the notes are the same
        
        dur = noteList[0].duration * 44100
        self.wav = np.zeros((int(dur),))

        # Just add the wave data for each chord inputted
        for i in noteList:
            self.wav += i.wav
        

#C4 = Note('C', 4, 4)
#G4 = Note('G', 4, 4)

#C4G4 = Chord([C4, G4])

# wavfile.write('firstchord.wav', rate=44100, data=C4G4.wav.astype(np.int16))
