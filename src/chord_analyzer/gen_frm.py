from time import sleep


def p_h(*harmonics):
    if (isinstance(harmonics[0], list) or isinstance(harmonics[0], tuple)) and len(harmonics) == 1:
        return ','.join(map(str, harmonics[0]))
    return ','.join(map(str, harmonics))


class Scale:
    harmonics = None

    def __init__(self, *harmonics):
        self.harmonics = harmonics

    def __len__(self):
        return len(self.harmonics)

    def get_note(self, note=0, octave=0):
        harmonics = []
        octave += note // len(self.harmonics)
        note = note % len(self.harmonics)
        if note == 0:
            return octave, (1, )
        for h in self.harmonics[:note]:
            if isinstance(h, int):
                harmonics.append(h)
            else:
                harmonics.extend(h)
        return octave, harmonics

    def total(self):
        n, d = 1, 1
        for h in self.harmonics:
            if isinstance(h, int):
                n *= h
                d *= h - 1
            else:
                for h_ in h:
                    n *= h_
                    d *= h_ - 1
        return n/d


major = Scale(9, 10, 16, 9, 10, 9, 16)
minor = Scale(9, 16, 10, 9, 16, 9, 10)
M_triad = Scale(5, 6, 4)
m_triad = Scale(6, 5, 4)
pentatonic_1 = Scale(6, 10, 9, 6, 10)
pentatonic_2 = Scale(7, 8, 9, 7, 8)

tryout_scales = [
    Scale(7, 8, 3),
]


def get_scale(s, octaves=2, shift=0):
    for i in range(len(s)*octaves+1):
        yield s.get_note((i+shift)%len(s))


def header(bpm=120, sig=(4, 4), prog=1):
    print(f'bpm {bpm} ; sig {sig[0]}/{sig[1]} ; prog {prog}')


def play_scale(scale, octaves=2):
    header()
    print(f'f=220')
    print(f'a0=f ; a0+')
    for o, h in get_scale(scale, octaves):
        print(f'a0={o}@{",".join(map(str, h))} ; sl 1/4')


def play_intervals(*notes):
    header()
    print(f'f=220')
    print(f'a0=f ; a1=a0 ; a0+ ; a1+')
    for o, h in notes:
        print(f'a1={o}@{",".join(map(str, h))} ; a0+ ; sl 1/4')


def play_chords(*chords):
    header()
    print(f'f=220')
    print(f'a0=f')
    for notes in chords:
        max_ch = 1
        for i, (o, h) in enumerate(notes):
            ch = i + 1
            max_ch = ch
            print(f'a{ch}=a0:{o}@{",".join(map(str, h))} ; a{ch}+')
        print('sl 2/4')
        print(' ; '.join(f'a{i}-' for i in range(1, max_ch+1)))


class BaseComposer:
    frequencies = {}
    voices = {}
    send = print
    running = False

    def __init__(self):
        self.initialize()

    def initialize(self):
        for freq_name, freq_value in self.frequencies.items():
            self.send(f'{freq_name}={freq_value}')
        for voice_name, voice_value in self.voices.items():
            self.send(f'{voice_name}={voice_value}')


class Composer1(BaseComposer):
    bpm = 120
    frequencies = {
        'f': 220
    }
    voices = {
        'bass': 'f',
        'tenor': 'bass:1@1'
    }
    sequences = {
        'tenor': get_scale(pentatonic_2)
    }
    bass_harmonics = [1]

    def start(self):
        self.running = True
        beat = 0
        while self.running:
            self.step(beat)
            sleep(60/self.bpm)
            beat = (beat + 1) % self.signature[0]

    def step(self, beat):
        o, h = next(self.sequences['tenor'])
        if beat == 0:
            self.bass_harmonics.extend(h)
            self.send(f'bass- ; bass=f:@{p_h(self.bass_harmonics)}')
            self.sequences['tenor'] = get_scale(pentatonic_2)
            o, h = next(self.sequences['tenor'])
        self.send(
            'tenor- ; tenor=bass:{o}@{h} ; tenor+'.format(o=o, h=p_h(h))
        )

    def stop(self):
        self.running = False
        for voice_name in self.voices:
            self.send(f'{voice_name}-')

    def next(self, value):
        pass



if __name__ == "__main__":
    #c = Composer1()
    #c.start()
    #play_scale(Scale(7, 8, 9, 8, 7))
    #play_scale(Scale(9,16,25,16,9,9,16,25,16))
    # play_chords(
    #     [
    #         (0, [1]),
    #         (0, [4]),
    #         (0, [3]),
    #         (1, [1]),
    #     ],
    #     [
    #         (0, [1]),
    #         (0, [5]),
    #         (0, [3]),
    #         (1, [1]),
    #     ],
    # )
    #play_scale(Scale(9, 10, 11, 12, 10, 11, 12))
    play_scale(Scale(12, 11, 10, 9, 12, 11, 10))
    #play_chords(
    #    [(0, [1]), (0, [7]), (0, [4])],
    #    [(0, [1]), (0, [5]), (0, [3])]
    #)
    #play_chords(
    #    [(0, [1]), (0, [5]), (0, [3]), (0, [3,5])]
    #)
