# coding=utf-8
'''
The core components of the game.

dgame is just a playground for python and pygame.
'''
from __future__ import print_function
import pygame
import sys, os, logging
import collections, yaml
from dgame.event import EventDispatcher, CommandQueue, UndoCommand, FlushCommand
from dgame.ui import Camera, Tile, Entity, FpsLayer
from dgame.image import Biome, CreatureSheet
from dgame.generator import EnvironmentGenerator

PROFILE = False
DEBUG = True

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
    '''The player knows about its heros and is an actor.'''

    def __init__(self, heros, env = None):
        self.heros = heros
        self.active_hero = heros[0]
        self.env = env
        self.command_queue = CommandQueue()

    def move_active_hero_up(self):
        '''Triggered by the event dispatcher.'''
        self._move_active_hero(self.active_hero.position_up)

    def move_active_hero_down(self):
        '''Triggered by the event dispatcher.'''
        self._move_active_hero(self.active_hero.position_down)

    def move_active_hero_left(self):
        '''Triggered by the event dispatcher.'''
        self._move_active_hero(self.active_hero.position_left)

    def move_active_hero_right(self):
        '''Triggered by the event dispatcher.'''
        self._move_active_hero(self.active_hero.position_right)

    def test_flush_command(self):
        cmd = FlushCommand('test_flush', lambda: print('flushed'))
        self.command_queue.add(cmd)

    def end_turn(self):
        self.command_queue.flush()

    def undo(self):
        '''Undo the last made command in the command queue.'''
        self.command_queue.undo()

    def _move_active_hero(self, new_pos):
        '''Generates a command and adds it to the command queue if the move is possible.'''
        hero = self.active_hero
        old_pos = hero.position
        target_tile = self.env.get_tile(new_pos)
        if target_tile.state == Tile.STATE_PASSABLE:
            hero = self.active_hero
            cmd = UndoCommand('move_creature', lambda: hero.move(new_pos), lambda: hero.move(old_pos))
            self.command_queue.add(cmd)


class Creature(object):
    '''A creature can move around in the environment'''

    def __init__(self, creature_sheet = 'klara'):
        self.creature_sheet = creature_sheet
        self.entity = Entity(pygame.Rect((0, 0), (1, 1)),
                             self.creature_sheet.static)

    @property
    def position(self):
        return self.entity.topleft

    @position.setter
    def position(self, v):
        self.entity.topleft = v

    @property
    def position_up(self):
        return (self.position[0], self.position[1] - 1)

    @property
    def position_down(self):
        return (self.position[0], self.position[1] + 1)

    @property
    def position_left(self):
        return (self.position[0] - 1, self.position[1])

    @property
    def position_right(self):
        return (self.position[0] + 1, self.position[1])

    def move(self, position):
        '''Set position, for usage in lambda statements.'''
        self.position = position


class Environment(object):
    '''The environment knows about the map and there creatures in it.'''

    def __init__(self, biome, config, map_size_name):
        self.config = config
        self.map_size_name = map_size_name
        self.size = self.width, self.height = config['map_size'][map_size_name]
        self.tile_size = self.tile_width, self.tile_height = config['tile_size']
        self.biome = biome
        self.tiles = [[self._default_tile(x, y) for y in range(self.height)] for x in range(self.width)]
        self.creatures = {}

    def _default_tile(self, x, y):
        '''Create this tile x times on initialize.'''
        return Tile(pygame.Rect((x, y), (1, 1)),
                    self.biome.unpassable)

    def get_tile(self, position):
        '''Get the tile at position.'''
        x, y = position
        return self.tiles[x][y]


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
        self.env_generator = EnvironmentGenerator(self.cfg['generator'], seed = 'testing')
        self.env = self.env_generator.create(Environment(biome = self.biomes['default'],
                                                         config = self.cfg['environment'],
                                                         map_size_name = 'small'),
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
