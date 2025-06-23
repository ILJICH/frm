import time

from play_chr import get_output_port
from play_frm import FrmPlayer, Note


class Composer:
    patterns = None
    bpm = 80
    freq = 220

    def __init__(self, frm, patterns):
        self.frm = frm
        self.patterns = patterns
        self.state = {
            'beat': 0
        }
        self.frm._new_frequency('f', self.freq)
        self.frm._new_note('root', 'f', 0, [1])
        for pattern in self.patterns:
            pattern.setup(self.frm)
        self.running = False

    def start(self):
        self.running = True
        start_time = time.time()
        beat_time = 60 / self.bpm
        while self.running:
            self._beat()
            # Technically, that could work wrong if compute time exceeds
            # the beat time, but I don't care enough
            time.sleep(beat_time - (time.time() - start_time) % beat_time)

    def _beat(self, inp=None):
        for pattern in self.patterns:
            pattern.update(self.state)
        if inp and self.state['beat'] > 6:
            self.state['beat'] = 0
        else:
            self.state['beat'] += 1

    def stop(self):
        for pattern in self.patterns:
            pattern.teardown()


class BasePattern:
    def setup(self):
        pass

    def update(self, state):
        pass

    def teardown(self):
        pass


class SimpleBassPattern(BasePattern):
    def __init__(self, name='bass', parent='root', period=5):
        self.name = name
        self.parent = parent
        self.period = period

    def setup(self, frm):
        self.frm = frm
        self.frm._new_note(self.name, self.parent, 0, [1])

    def update(self, state):
        if state['beat'] % self.period == 0:
            self.frm._note_off(self.name)
            self.frm._new_note(self.name, self.parent, 0, [1])
            self.frm._note_on(self.name)

    def teardown(self):
        self.frm._note_off(self.name)

class SimpleScalePattern(BasePattern):
    def __init__(self, name='scale', parent='root', scale=None):
        self.name = name
        self.parent = parent
        self.scale = scale
        self.note = Note(
            parent=None,
            octave=0,
            harmonics=[1],
            sound=None,
            program=None
        )

    def setup(self, frm):
        self.frm = frm
        self.frm._new_note(self.name, self.parent, 0, [1])

    def update(self, state):
        self.frm._note_off(self.name)
        if state['beat'] == 0:
            self.note.octave = 0
            self.note.harmonics = [1]
        else:
            self.note.harmonics.append(
                self.scale[(state['beat']-1)%len(self.scale)]
            )
        self.frm._new_note(
            self.name, self.parent, self.note.octave, self.note.harmonics
        )
        print(self.note.absolute())
        self.frm._note_on(self.name)

    def teardown(self):
        self.frm._note_off(self.name)


if __name__ == "__main__":
    frm = FrmPlayer(None, get_output_port('FLUID'))
    c = Composer(frm, [
        SimpleBassPattern(),
        SimpleScalePattern(scale=[7, 8, 9, 7, 8])]
    )
    try:
        c.start()
    except KeyboardInterrupt:
        c.stop()
