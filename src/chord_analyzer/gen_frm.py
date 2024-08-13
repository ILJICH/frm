



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


def get_scale(s, octaves=2):
    for i in range(len(s)*octaves+1):
        yield s.get_note(i)


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


if __name__ == "__main__":
    play_scale(Scale(7, 8, 9, 8, 7))
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
