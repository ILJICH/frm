from dataclasses import dataclass
from time import time

import pygame

from play_frm import Frequency, Note, FrmPlayer


class Voice:
    base: str = None
    octave: int = 0
    harmonics: list = None

    program = 1

    def __init__(self, base, octave=0, harmonics=None):
        self.base = base
        self.octave = octave
        self.harmonics = harmonics or [1]

    def add_harmonic(self, harmonic):
        self.harmonics.append(harmonic)
        self.harmonics.sort()

    def remove_harmonic(self, harmonic):
        if harmonic in self.harmonics:
            self.harmonics.remove(harmonic)
        else:
            self.harmonics.append(-harmonic)

    def is_on(self):
        return self.harmonics != [1]

    def copy(self):
        return Voice(self.base, self.octave, self.harmonics[:])

    def to_frm(self):
        return '{base}:{octave}@{harmonics}'.format(
            base=self.base,
            octave=self.octave,
            harmonics=",".join(map(str, self.harmonics[1:]))
        )

    def __repr__(self):
        return f'Voice({self.to_frm()})'


@dataclass
class DroneState:
    name: str
    voice: Voice = None
    parent: str = 'f'


class Player:
    state = {
        'voice': None,
        'drones': {
            1: DroneState('d1'),
            2: DroneState('d2'),
            3: DroneState('d3'),
            4: DroneState('d4'),
            5: DroneState('d5'),
            6: DroneState('d6'),
            7: DroneState('d7'),
            8: DroneState('d8'),
            9: DroneState('d9'),
            0: DroneState('d0'),
        },
        'modifiers': {
            'octave': 0,
            'space': 0
        }
    }
    def __init__(self):
        self.frm = FrmPlayer(None)
        self.frm._new_frequency('f', 220)
        self.frm._new_note('voice', 'f', 0, [1])
        for i in range(0, 10):
            self.frm._new_note(f'd{i}', 'f', 0, [1])
        self.state['voice'] = Voice('f')

    def stop(self):
        self.frm.stop()

    def _update_voice(self, voice_name, voice):
        self.frm._note_off(voice_name)
        if voice.is_on():
            self.frm._new_note(
                voice_name,
                voice.base,
                voice.octave,
                voice.harmonics
            )
            self.frm._note_on(voice_name)

    def harmonic_on(self, harmonic):
        self.state['voice'].add_harmonic(harmonic)
        self._update_voice('voice', self.state['voice'])

    def harmonic_off(self, harmonic):
        self.state['voice'].remove_harmonic(harmonic)
        self._update_voice('voice', self.state['voice'])

    @classmethod
    def get_callback(cls, h):
        def clb(player, on):
            if on:
                player.harmonic_on(h)
            else:
                player.harmonic_off(h)
        return clb

    @classmethod
    def get_octave_callback(cls, delta):
        def clb(player, on):
            player.state['modifiers']['octave'] += delta if on else -delta
            player.state['voice'].octave = player.state['modifiers']['octave']
            player._update_voice('voice', player.state['voice'])
        return clb

    @classmethod
    def get_modifier_callback(cls, name, delta=1):
        def clb(player, on):
            player.state['modifiers'][name] += delta if on else -delta
        return clb

    @classmethod
    def get_drone_callback(cls, drone):
        def clb(player, on):
            if player.state['modifiers']['space']:
                if on:
                    player.state['drones'][drone].voice = player.state['voice'].copy()
            elif player.state['drones'][drone].voice is not None:
                if on:
                    player._update_voice(
                        player.state['drones'][drone].name,
                        player.state['drones'][drone].voice
                    )
                else:
                    player.frm._note_off(player.state['drones'][drone].name)
        return clb


mapping = {
    pygame.K_TAB: Player.get_callback(1),
    pygame.K_q: Player.get_callback(3),
    pygame.K_w: Player.get_callback(4),
    pygame.K_e: Player.get_callback(5),
    pygame.K_r: Player.get_callback(6),
    pygame.K_t: Player.get_callback(7),
    pygame.K_y: Player.get_callback(8),
    pygame.K_u: Player.get_callback(9),
    pygame.K_i: Player.get_callback(10),
    pygame.K_o: Player.get_callback(11),
    pygame.K_p: Player.get_callback(12),
    pygame.K_LEFTBRACKET: Player.get_callback(13),
    pygame.K_RIGHTBRACKET: Player.get_callback(14),
    pygame.K_BACKSLASH: Player.get_callback(15),
    pygame.K_a: Player.get_callback(16),
    pygame.K_s: Player.get_callback(17),
    pygame.K_d: Player.get_callback(18),
    pygame.K_f: Player.get_callback(19),
    pygame.K_g: Player.get_callback(20),
    pygame.K_h: Player.get_callback(21),
    pygame.K_j: Player.get_callback(22),
    pygame.K_k: Player.get_callback(23),
    pygame.K_l: Player.get_callback(24),
    pygame.K_SEMICOLON: Player.get_callback(25),
    pygame.K_QUOTE: Player.get_callback(26),
    pygame.K_z: Player.get_callback(27),
    pygame.K_x: Player.get_callback(28),
    pygame.K_c: Player.get_callback(29),
    pygame.K_v: Player.get_callback(30),
    pygame.K_b: Player.get_callback(31),
    pygame.K_n: Player.get_callback(32),
    pygame.K_m: Player.get_callback(33),
    pygame.K_COMMA: Player.get_callback(34),
    pygame.K_PERIOD: Player.get_callback(35),
    pygame.K_SLASH: Player.get_callback(36),
    pygame.K_RSHIFT: Player.get_octave_callback(1),
    pygame.K_LSHIFT: Player.get_octave_callback(1),
    pygame.K_LCTRL: Player.get_octave_callback(-1),
    pygame.K_RCTRL: Player.get_octave_callback(-1),
    pygame.K_SPACE: Player.get_modifier_callback('space'),
    pygame.K_1: Player.get_drone_callback(1),
    pygame.K_2: Player.get_drone_callback(2),
    pygame.K_3: Player.get_drone_callback(3),
    pygame.K_4: Player.get_drone_callback(4),
    pygame.K_5: Player.get_drone_callback(5),
    pygame.K_6: Player.get_drone_callback(6),
    pygame.K_7: Player.get_drone_callback(7),
    pygame.K_8: Player.get_drone_callback(8),
    pygame.K_9: Player.get_drone_callback(9),
    pygame.K_0: Player.get_drone_callback(0),
}


code_to_name = {getattr(pygame, name): name for name in dir(pygame) if name.startswith('K_')}


def run():
    pygame.init()

    player = Player()
    drawer = Drawer()

    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            # if event.type == pygame.KEYDOWN:
            #     print(code_to_name.get(event.key))
            if event.type == pygame.QUIT:
                running = False
                break
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
                break
            elif event.type in (pygame.KEYDOWN, pygame.KEYUP) and event.key in mapping:
                mapping[event.key](player, event.type == pygame.KEYDOWN)

        dt = clock.tick(100)
        state = player.state
        drawer.update(state)

    player.stop()
    pygame.quit()


class Drawer:
    def __init__(self):
        self.screen = pygame.display.set_mode((1280, 720))
        self.font = pygame.font.SysFont('notosans', size=50)

    def draw_voice(self, voice, x, y):
        if voice is None:
            octave = 0
            harmonics = [1]
        else:
            octave = voice.octave
            harmonics = voice.harmonics

        octave_text_surface = self.font.render(
            str(octave),
            True,
            'white'
        )
        harmonics_text_surface = self.font.render(
            '@' + ','.join(map(str, harmonics[1:])),
            True,
            'white'
        )
        self.screen.blit(octave_text_surface, (x, y))
        self.screen.blit(harmonics_text_surface, (x + 50, y))

    def draw_harmonics(self, voice, x, y):
        text_surface = self.font.render(
            '@' + ','.join(map(str, voice.harmonics[1:])),
            True,
            'white'
        )
        self.screen.blit(text_surface, (x, y))

    def draw_octave(self, octave, x, y):
        text_surface = self.font.render(
            str(octave),
            True,
            'white'
        )
        self.screen.blit(text_surface, (x, y))

    def update(self, state):
        self.screen.fill('purple')
        self.draw_voice(state['voice'], 50, 100)
        self.draw_voice(state['drones'][1].voice, 50, 200)
        self.draw_voice(state['drones'][2].voice, 650, 200)
        self.draw_voice(state['drones'][3].voice, 50, 300)
        self.draw_voice(state['drones'][4].voice, 650, 300)
        self.draw_voice(state['drones'][5].voice, 50, 400)
        self.draw_voice(state['drones'][6].voice, 650, 400)
        self.draw_voice(state['drones'][7].voice, 50, 500)
        self.draw_voice(state['drones'][8].voice, 650, 500)
        self.draw_voice(state['drones'][9].voice, 50, 600)
        self.draw_voice(state['drones'][0].voice, 650, 600)

        pygame.display.flip()


if __name__ == "__main__":
    run()
