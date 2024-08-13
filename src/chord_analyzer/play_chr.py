import math
import time
import traceback

import mido


A4 = 440.0
A4_code = 69

s12_2 = 2.0**(1/12)
bend_limit = 2**13
bend_semitones = 2.0


def get_port():
    return mido.open_output(
        [o for o in mido.get_output_names() if o.startswith('FLUID')][0]
    )


def freq_to_midi(freq):
    note = int(math.log2(freq/A4)*12 + A4_code)
    bend = int(bend_limit * 12.0 / bend_semitones * math.log2(freq/midi_to_freq(note, 0)))
    return note, bend


def midi_to_freq(note, bend):
    return (A4 * 2.0**((note-A4_code)/12) *  2**((bend_semitones/12)*(bend/bend_limit)))


class Interval:
    n: int = 1
    d: int = 1
    parent = None
    _freq: float = 440.0
    def __init__(self, n: int, d: int, parent = None):
        self.n = n
        self.d = d
        self.parent = parent

    def set_freq(self, freq: float):
        if self.n != 1 or self.d != 1:
            raise ValueError('Can only set frequency on the root')
        self._freq = freq

    def freq(self):
        if self.n == 1 and self.d == 1:
            return self._freq
        return self.parent.freq() * float(self.n) / float(self.d)


class ChrPlayer:
    index = {}

    def __init__(self, freq=220.0):
        self.port = get_port()
        self.b0 = Interval(1, 1)

    def _names(self, names):
        for name in names:
            v = self.index.get(name)
            if v is None:
                continue
            yield name, v

    def _send(self, cmd, *args, **kwargs):
        print(cmd, args, kwargs)
        self.port.send(mido.Message(cmd, *args, **kwargs))

    def play(self, *names):
        for _, v in self._names(names):
            note, bend = freq_to_midi(v['interval'].freq())
            self._send('note_on', channel=v['channel'], note=note, velocity=127)
            self._send('pitchwheel', channel=v['channel'], pitch=bend)
            v['note'] = note

    def all_play(self):
        for name in self.index:
            self.play(name)

    def stop(self, *names):
        for _, v in self._names(names):
            if v['note'] is None:
                continue
            self._send('note_off', channel=v['channel'], note=v['note'])
            v['note'] = None

    def all_stop(self):
        for name in self.index:
            self.stop(name)

    def add_note(self, name, channel, interval):
        self.index[name] = {
            'channel': channel,
            'interval': interval,
            'note': None
        }

    def change_note(self, name, interval):
        self.index[name]['interval'] = interval

    def remove_note(self, *names):
        for name, v in self._names(names):
            if v['note'] is not None:
                self._stop(name)
            del self.index[name]

    def program_change(self, program, *names):
        for _, v in self._names(names):
            self._send('program_change', channel=v['channel'], program=program)
            v['note'] = None

    def get_interval(self, s):
        p = None
        if ':' in s:
            p, s = s.split(':')
            n, d = s.split('/')
            result = Interval(int(n), int(d), self.index[p]['interval'])
        else:
            result = Interval(1, 1)
            result.set_freq(float(s))
        return result

    def state(self):
        print('Current state:')
        for name, v in self.index.items():
            i = v['interval']
            print(f'{name}({v["channel"]}) {i.n}/{i.d} {"on" if v["note"] is not None else "off"}')
        print('-' * 10)

    def process(self, cmd, args):
        match cmd:
            case 'program':
                self.program_change(int(args[0]), *args[1:])
            case 'ap':
                self.all_play()
            case 'as':
                self.all_stop()
            case 'a':
                print()
                self.add_note(
                    args[0], int(args[1]), self.get_interval(args[2])
                )
            case 'c':
                self.change_note(args[0], self.get_interval(args[1]))
            case 'r':
                self.remove_note(*args)
            case 'p':
                self.play(*args)
            case 's':
                self.stop(*args)
            case 'i':
                self.state()
            case _:
                self.all_stop()
                self.all_play()


if __name__ == "__main__":
    player = ChrPlayer(220.0)
    while True:
        try:
            inp = input('command: ').split(' ')
            if inp[0] == "#":
                continue
            if inp[0] == 'sleep':
                time.sleep(float(inp[1]))
                continue
        except (KeyboardInterrupt, EOFError):
            break

        try:
            player.process(inp[0], inp[1:])
        except Exception as e:
            print(f'Failed to parse: {inp}')
            traceback.print_exc()
    player.all_stop()
