import argparse
from dataclasses import dataclass
from typing import *
import logging
from time import sleep
import traceback

import mido
from lark import Lark, Token, Tree, UnexpectedCharacters

from play_chr import get_port, freq_to_midi


logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
log = logging.getLogger('play_frm')


def get_parser(filename="frm.lark"):
    with open(filename, 'r') as f:
        return Lark(f.read())


def get_file(filename):
    with open(filename, 'r') as f:
        data = f.read()

    while data[-2] == '\n':
        data = data[:-1]

    if data[-1] != '\n':
        data += '\n'

    return data


class TreeList:
    def __init__(self, tree):
        self._tree = []
        self._kwds = {}
        for c in tree.children:
            if isinstance(c, Tree):
                k = c.data.value
                val = TreeList(c)
                if len(list(val)) == 1 and not isinstance(val[0], tuple):
                    val = val[0]
                if k not in self._kwds:
                    self._kwds[c.data.value] = val
                elif isinstance(self._kwds[k], list):
                    self._kwds[k].append(val)
                else:
                    self._kwds[k] = [self._kwds[k], val]
                self._tree.append((c.data.value, val))
            elif isinstance(c, Token):
                self._tree.append(c.value)
            else:
                self._tree.append(c)

    def __getitem__(self, k):
        if isinstance(k, int):
            return self._tree[k]
        if k not in self._kwds:
            raise ValueError(f'Unknown key: {k}')
        itm = self._kwds[k]
        if isinstance(itm, tuple):
            return itm[1]
        return itm

    def __repr__(self):
        return f'TreeList({self._tree})'

    def __iter__(self):
        return iter(self._tree)

    def __contains__(self, k):
        return k in self._kwds


def one_or_many(v):
    if isinstance(v, list):
        return v
    return [v]


@dataclass
class Frequency:
    frequency: float = None

    def freq(self):
        return self.frequency


@dataclass
class Sound:
    channel: int | None
    note: int
    velocity: int


@dataclass
class Note:
    parent: Frequency = None
    octave: int = 0
    harmonics: list[int] = None
    sound: Sound = None
    program: int = None

    def freq(self):
        total_n, total_d = 1, 1
        for n in self.harmonics:
            d = max(1, n-1)
            total_n *= n
            total_d *= d
        octave = self.octave or 0
        return self.parent.freq() * (2**octave) * total_n / total_d


CHANNELS_NUM = 16


class ChannelRegistry:
    channels = None

    def __init__(self, max_channels=None):
        self.channels = [False for _ in range(max_channels or CHANNELS_NUM)]

    def allocate(self):
        for i, occupied in enumerate(self.channels):
            if not occupied:
                self.channels[i] = True
                return i
        return None

    def free(self, i):
        self.channels[i] = False


class FrmPlayer:
    bpm = 120
    program = 85
    signature = (4, 4)

    frequencies = {}
    notes = {}

    port = None
    channels = None

    running = False

    def __init__(self, parser):
        log.info('Initializing player')
        self.parser = parser
        log.info('Opening port')
        self.port = get_port()
        self.channels = ChannelRegistry()

    def _send(self, cmd, *args, **kwargs):
        log.debug(f"Sending to port: {cmd} {args}, {kwargs}")
        self.port.send(mido.Message(cmd, *args, **kwargs))

    def get_frequency(self, name):
        try:
            return self.frequencies[name]
        except KeyError:
            raise ValueError(f'No frequencies named {name}')

    def get_note(self, name):
        try:
            return self.notes[name]
        except KeyError:
            raise ValueError(f'No notes named {name}')

    def get_note_or_freq(self, name):
        if name in self.notes:
            return self.notes[name]
        elif name in self.frequencies:
            return self.frequencies[name]
        raise ValueError(f'No notes or frequencies named {name}')

    def stop(self):
        log.info('Stopping..')
        for note in self.notes.values():
            self._stop(note)

    def process(self, data):
        self.running = True
        tl = TreeList(self.parser.parse(data))
        for block in tl:
            match block:
                case ('line', line):
                    if not self.running:
                        return
                    self._run_line(line[0])
                case ('multiline', lines):
                    for line in lines:
                        if not self.running:
                            return
                        self._run_line(line)
                case _:
                    log.info(f'Not a line: {block}')

    def _run_line(self, line):
        if line[0] != 'cmd':
            return
        return self._run_cmd(line[1])

    def _run_cmd(self, cmd):
        op = cmd[0]
        match op:
            case ('bpm', bpm):
                self._set_bpm(int(bpm))
            case ('signature', args):
                fr = args['fraction']
                self._set_signature(int(fr['numerator']), int(fr['denominator']))
            case ('program', args):
                print(args)
                if isinstance(args, TreeList):
                    prog, *names = args
                    for name in names:
                        self._set_note_program(int(prog), name)
                else:
                    prog = args
                    self._set_program(int(prog))
            case ('frequency', args):
                self._new_frequency(args[0], float(args[1]))
            case ('note', args):
                r = args["ratio"]
                if "harmonic" in r:
                    self._new_note(
                        name=args[0],
                        parent_name=r["parent"] if "parent" in r else None,
                        octave=int(r["octave"]) if "octave" in r else None,
                        harmonics=list(map(int, one_or_many(r["harmonic"])))
                    )
                else:
                    self._new_note(
                        name=args[0],
                        parent_name=r["parent"],
                        octave=0,
                        harmonics=(1, )
                    )
            case ('note_on', name):
                self._note_on(name)
            case ('note_off', name):
                self._note_off(name)
            case ('sleep', args):
                fr = args['fraction']
                self._sleep(int(fr['numerator']), int(fr['denominator']))
            case ('sync', args):
                self._sync()
            case _: log.info('Unknown command: %s', cmd)

    def _set_bpm(self, bpm):
        log.info('Setting BPM: %s', bpm)
        self.bpm = bpm

    def _set_signature(self, n, d):
        log.info('Setting signature: %s/%s', n, d)
        self.signature = (n, d)

    def _set_program(self, p):
        log.info('Setting program: %s', p)
        self.program = p

    def _set_note_program(self, p, name):
        log.info('Setting program of %s: %s ', name, p)
        note = self.get_note(name)
        note.program = p

    def _new_frequency(self, name, freq):
        log.info('Setting frequency: %s=%s', name, freq)
        self.frequencies[name] = Frequency(freq)

    def _play(self, note):
        if note.sound is not None:
            c = note.sound.channel
            self._send('note_off', channel=c, note=note.sound.note)
        else:
            c = self.channels.allocate()
            prog = note.program or self.program
            self._send('program_change', channel=c, program=prog)
        n, b = freq_to_midi(note.freq())
        v = 100
        note.sound = Sound(c, n, v)
        self._send('pitchwheel', channel=c, pitch=b)
        self._send('note_on', channel=c, note=n, velocity=v)

    def _stop(self, note):
        if note.sound is None:
            return
        self._send(
            'note_off',
            channel=note.sound.channel,
            note=note.sound.note
        )
        self.channels.free(note.sound.channel)
        note.sound = None

    def _new_note(self, name, parent_name, octave, harmonics):
        log.info('New note: %s=%s:%s@%s', name, parent_name, octave, harmonics)
        if name in self.notes:
            note = self.get_note(name)
            if parent_name is not None:
                note.parent = self.get_note_or_freq(parent_name)
            if octave is not None:
                note.octave = octave
            if harmonics is not None:
                note.harmonics = harmonics
            if note.sound:
                self._play(note)
        else:
            if parent_name is None:
                raise ValueError(f'Can\'t initialize note {name} without a parent')
            if parent_name in self.notes:
                parent = self.get_note_or_freq(parent_name)
            elif parent_name in self.frequencies:
                parent = self.get_frequency(parent_name)
            else:
                raise ValueError(f'No note or frequency with name {parent_name}')
            self.notes[name] = Note(
                parent,
                octave,
                harmonics,
                None,
                None,
            )

    def _note_on(self, name):
        log.info('Note on: %s', name)
        self._play(self.get_note(name))

    def _note_off(self, name):
        log.info('Note off: %s', name)
        self._stop(self.get_note(name))

    def _sleep(self, n, d):
        log.info('Sleep: %s/%s', n, d)
        sleep(n * 60 / (self.bpm * d / self.signature[1]))

    def _sync(self):
        log.info('Syncing.')
        


def run_file(filename):
    try:
        log.info(f'Running: {filename}')
        parser = get_parser()
        player = FrmPlayer(parser)
        file = get_file(filename)
        player.process(file)
    finally:
        player.stop()


def run_cli():
    log.info('Running CLI')
    parser = get_parser()
    player = FrmPlayer(parser)
    while True:
        try:
            inp = input(':> ')
            player.process(inp+"\n")
        except UnexpectedCharacters:
            log.info(f'Failed to parse: {inp}')
            pass
        except EOFError:
            break
        except KeyboardInterrupt:
            break
        except ValueError as e:
            traceback.print_exc()
            continue
    player.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser('Play FRM files')
    parser.add_argument("filename", metavar='filename', nargs="*", help='Filename to play')
    args = parser.parse_args()
    if args.filename:
        for filename in args.filename:
            run_file(filename)
    else:
        run_cli()
