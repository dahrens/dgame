# coding=utf-8
'''
dgame is just a playground for python and pygame.
'''
import pygame
import sys, os, logging
import collections, yaml
from dgame.event import EventDispatcher
from dgame.ui import Camera, Tile, Entity, FpsLayer
from dgame.image import Biome, CreatureSheet
from dgame.generator import EnvironmentGenerator

PROFILE = False
DEBUG = False

class Configuration(dict):
    '''Game configuration based on YAML files.'''

    def __init__(self, default_config = 'data/config.yaml', user_config = 'data/user_config.yaml'):
        self.user_file_path = user_config
        default_file = file(default_config, 'rb')
        user_file = file(self.user_file_path, 'rb')
        self.update(yaml.load(default_file))
        self._user_config = yaml.load(user_file)
        user_file.close()
        self.update(self._user_config)

    def update_user_config(self, *args, **kwargs):
        self._user_config.update(*args, **kwargs)
        user_file = file(self.user_file_path, 'w+')
        yaml.dump(self._user_config, user_file)
        user_file.close()
        self.update(self._user_config)

    def update(self, u):
        return self.update_dict(self, u)

    def update_dict(self, d, u):
        for k, v in u.iteritems():
            if isinstance(v, collections.Mapping):
                r = self.update_dict(d.get(k, {}), v)
                d[k] = r
            else:
                d[k] = u[k]
        return d


class Player(object):

    def __init__(self, heros):
        self.heros = heros
        self.active_hero = heros[0]

    def move_active_hero_up(self):
        self.active_hero.move(Creature.MOVE_UP)

    def move_active_hero_down(self):
        self.active_hero.move(Creature.MOVE_DOWN)

    def move_active_hero_left(self):
        self.active_hero.move(Creature.MOVE_LEFT)

    def move_active_hero_right(self):
        self.active_hero.move(Creature.MOVE_RIGHT)

class Creature(object):

    MOVE_UP = 1
    MOVE_DOWN = 2
    MOVE_LEFT = 3
    MOVE_RIGHT = 4

    def __init__(self, creature_sheet = 'klara'):
        self.creature_sheet = creature_sheet
        self.env = None
        self.entity = Entity(pygame.Rect((0, 0), (1, 1)),
                             self.creature_sheet.static)

    @property
    def position(self):
        return self.entity.topleft

    @position.setter
    def position(self, v):
        self.entity.topleft = v

    def move(self, direction):
        nb = self.env.get_passable_neighbours(self.position)
        if direction == self.MOVE_UP:
            new_p = self.position[0], self.position[1] - 1
        elif direction == self.MOVE_DOWN:
            new_p = self.position[0], self.position[1] + 1
        elif direction == self.MOVE_LEFT:
            new_p = self.position[0] - 1, self.position[1]
        elif direction == self.MOVE_RIGHT:
            new_p = self.position[0] + 1, self.position[1]
        if new_p in nb:
            self.position = new_p

class Environment(object):

    def __init__(self, size, tile_size, biome):
        self.size = self.width, self.height = size
        self.tile_size = self.tile_width, self.tile_height = tile_size
        self.biome = biome
        self.tiles = [[self._default_tile(x, y) for y in range(self.height)] for x in range(self.width)]
        self.creatures = {}

    def _default_tile(self, x, y):
        return Tile(pygame.Rect((x, y), (1, 1)),
                    self.biome.unpassable)

    def get_passable_neighbours(self, position):
        n = [(position[0] - 1, position[1]),
             (position[0] + 1, position[1]),
             (position[0], position[1] - 1),
             (position[0], position[1] + 1)]
        pn = []
        for x, y in n:
            if self.tiles[x][y].state == Tile.STATE_PASSABLE:
                pn.append((x, y))
        return pn


class Game():
    '''Currently the launcher.

    TODO: seperate game from launch process, to allow saving.

    '''

    def __init__(self):
        pygame.init()
        self.modes = pygame.display.list_modes()
        self.cfg = Configuration()
        logging.debug('cfg: {}'.format(self.cfg))

        self.screen_size = self.width , self.height = self.cfg['gfx']['resolution']
        if self.cfg['gfx']['fullscreen']:
            self.screen = pygame.display.set_mode(self.screen_size, pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
        else:
            self.screen = pygame.display.set_mode(self.screen_size, pygame.NOFRAME)
        self.background = pygame.Surface(self.screen_size)
        self.background.fill((200, 200, 200))
        self.screen.blit(self.background, (0, 0))

        self.font = pygame.font.SysFont('mono', 20, bold = True)
        self.clock = pygame.time.Clock()
        self.fps = self.cfg['gfx']['max_fps']
        self.playtime = 0.0

        self.biomes = self.init_biomes()
        self.creatures = self.init_creatures()
        self.player = Player(heros = [Creature(self.creatures['klara'])])
        self.env_generator = EnvironmentGenerator(seed = 'testing')
        self.env = self.env_generator.create(Environment(biome = self.biomes['default'],
                                                         size = self.cfg['environment']['map_size']['small'],
                                                         tile_size = self.cfg['environment']['tile_size']
                                                         ),
                                             player = self.player)
        self.camera = Camera(pygame.Rect((0, 0), (self.width, self.height - 256)),
                             self.env,
                             zoom_levels = self.cfg['ui']['camera']['zoom_levels'],
                             zoom_level = self.cfg['ui']['camera']['zoom_level'],
                             scroll_speed = self.cfg['ui']['camera']['scroll_speed'])
        self.fps_ui = FpsLayer(self.font, self.clock, (self.width - 150, self.height - 30))

        self.dispatcher = EventDispatcher(self.cfg['controls'], {'camera': self.camera,
                                                                 'game': self,
                                                                 'player': self.player})

        self.ui_group = pygame.sprite.LayeredUpdates(self.camera, self.fps_ui)

    def quit(self):
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def run(self):
        running = True
        pygame.key.set_repeat(100, 10)
        while running:
            for event in pygame.event.get():
                running = self.dispatcher.dispatch(event)
            milliseconds = self.clock.tick(self.fps)
            self.playtime += milliseconds / 1000.0
            self.ui_group.clear(self.screen, self.background)
            self.ui_group.update()
            pygame.display.update(self.ui_group.draw(self.screen))

    def init_biomes(self):
        _b = {}
        for name, config in self.cfg['image']['biomes'].iteritems():
            _b[name] = Biome(name, config, self.cfg['ui']['camera']['zoom_levels'])
        return _b

    def init_creatures(self):
        _b = {}
        for name, config in self.cfg['image']['creatures'].iteritems():
            _b[name] = CreatureSheet(name, config, self.cfg['ui']['camera']['zoom_levels'])
        return _b


if __name__ == '__main__':
    def profile(function, *args, **kwargs):
        """ Returns performance statistics (as a string) for the given function."""
        def _run():
            function(*args, **kwargs)
        import cProfile as profile
        import pstats
        sys.modules['__main__'].__profile_run__ = _run
        identifier = function.__name__ + '()'
        profile.run('__profile_run__()', identifier)
        p = pstats.Stats(identifier)
        p.stream = open(identifier, 'w')
        p.sort_stats('time').print_stats(50)
        p.stream.close()
        s = open(identifier).read()
        os.remove(identifier)
        return s
    if DEBUG:
        logging.basicConfig(level = logging.DEBUG)
    if PROFILE:
        profile_result = profile(Game().run)
        print(profile_result)
    else:
        Game().run()
