# coding=utf-8
'''
The core components of the game.

dgame is just a playground for python and pygame.
'''
from __future__ import print_function
import pygame
import sys, os, logging
import collections, yaml
import math
from dgame.event import EventDispatcher, CommandQueue, UndoCommand, FlushCommand, OneWayCommand
from dgame.ui import Map, Entity, Floor, FpsLayer
from dgame.image import Biome, CreatureSheet
from dgame.ai import AStar, Node

PROFILE = False
DEBUG = False


class Player(object):
    '''The player knows about its heros and is an actor.'''

    def __init__(self, heros, env = None):
        self.heros = heros
        self.active_hero = heros[0]
        self.env = env
        self.command_queue = CommandQueue()

    def move_active_hero_up(self):
        '''Triggered by the event dispatcher.'''
        return self.env.create_move_creature_command(self.active_hero, self.env.position_up(self.active_hero.position), self.command_queue)

    def move_active_hero_down(self):
        '''Triggered by the event dispatcher.'''
        return self.env.create_move_creature_command(self.active_hero, self.env.position_down(self.active_hero.position), self.command_queue)

    def move_active_hero_left(self):
        '''Triggered by the event dispatcher.'''
        return self.env.create_move_creature_command(self.active_hero, self.env.position_left(self.active_hero.position), self.command_queue)

    def move_active_hero_right(self):
        '''Triggered by the event dispatcher.'''
        return self.env.create_move_creature_command(self.active_hero, self.env.position_right(self.active_hero.position), self.command_queue)

    def test_flush_command(self):
        '''There are no commands that should be performed at the end of the turn. This is just proof of concept.'''
        cmd = FlushCommand('test_flush', lambda: print('flushed'))
        self.command_queue.add(cmd)
        return True

    def end_turn(self):
        '''End the current turn'''
        self.command_queue.flush()
        for hero in self.heros:
            hero.end_turn()
        return True

    def next_hero(self):
        '''Switch to the next hero the player controls'''
        i = self.heros.index(self.active_hero) + 1
        if (i) < len(self.heros):
            self.active_hero = self.heros[i]
        else:
            self.active_hero = self.heros[0]
        return True

    def undo(self):
        '''Undo the last made command in the command queue.'''
        self.command_queue.undo()
        return True


class Creature(object):
    '''A creature can move around in the environment'''

    def __init__(self, config, sheet = None, size = (1, 1), pos = None, env = None):
        self.sheet = sheet
        self.max_hp = config['hp']
        self.hp = config['hp']
        self.moves_max = config['moves']
        self.moves = config['moves']
        self.env = env
        self.position = pos
        if self.env and self.position:
            self.env.creatures.append(self)
        self.ui = Entity(self.sheet)

    @property
    def x(self):
        return self.position[0]

    @property
    def y(self):
        return self.position[1]

    @property
    def reachable_positions(self):
        return self.env.reachable_positions(self, self.moves)

    def end_turn(self):
        self.moves = self.moves_max

    def move(self, position):
        self.moves -= 1
        self._move(position)

    def undo_move(self, position):
        self.moves += 1
        self._move(position)

    def _move(self, position):
        '''Set position, for usage in lambda statements. TODO: move over in env? not sure...'''
        self.env.get_tile(self.position).state = Tile.STATE_PASSABLE
        self.env.get_tile(position).state = Tile.STATE_UNPASSABLE
        self.position = position


class Tile(object):
    '''A tile is field on the map.'''

    STATE_UNPASSABLE = -1
    STATE_PASSABLE = 1

    def __init__(self, env, pos, size = (1, 1)):
        self.position = pos
        self.size = size
        self.env = env
        self.state = self.STATE_UNPASSABLE
        self.ui = Floor(self.env.biome, self.state)

    @property
    def x(self):
        return self.position[0]

    @property
    def y(self):
        return self.position[1]

    def __eq__(self, l):
        if l.x == self.x and l.y == self.y:
            return True
        else:
            return False


class Environment(object):
    '''The environment knows about the map and there creatures in it.'''

    def __init__(self, biome, config, map_size_name, player):
        self.config = config
        self.map_size_name = map_size_name
        self.size = self.width, self.height = config['map_size'][map_size_name]
        self.tile_size = self.tile_width, self.tile_height = config['tile_size']
        self.biome = biome
        self.tiles = [[self._default_tile(x, y) for y in range(self.height)] for x in range(self.width)]
        self.creatures = []
        self.player = player
        self.player.env = self
        self.path_finder = AStar(self)

    def _default_tile(self, x, y):
        '''Create this tile x times on initialize.'''
        return Tile(self, (x, y))

    def get_node(self, tile, from_tile = False):
        '''Get a node of the map, for a* algorithm.'''
        x = tile.x
        y = tile.y
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return None
        d = tile.state
        if d == -1 and not from_tile:
            return None

        return Node(tile, d, ((y * self.width) + x));

    def get_adjacent_nodes(self, curnode, dest):
        '''Get adjacent nodes'''
        result = []

        cl = curnode.location
        dl = dest

        n = self._handle_astar_node(cl.x + 1, cl.y, curnode, dl.x, dl.y)
        if n: result.append(n)
        n = self._handle_astar_node(cl.x - 1, cl.y, curnode, dl.x, dl.y)
        if n: result.append(n)
        n = self._handle_astar_node(cl.x, cl.y + 1, curnode, dl.x, dl.y)
        if n: result.append(n)
        n = self._handle_astar_node(cl.x, cl.y - 1, curnode, dl.x, dl.y)
        if n: result.append(n)
        return result

    def _handle_astar_node(self, x, y, from_node, dest_x, dest_y):
        n = self.get_node(self.tiles[x][y])
        if n is not None:
            dx = max(x, dest_x) - min(x, dest_x)
            dy = max(y, dest_y) - min(y, dest_y)
            em_cost = dx + dy
            n.m_cost += from_node.m_cost
            n.score = n.m_cost + em_cost
            n.parent = from_node
            return n
        return None

    def create_move_creature_command(self, creature, new_pos, queue = None):
        '''Generates and executes a command; adds it to the command queue if the move is possible and the queue is given.'''
        if creature.moves == 0: return False
        if self.get_tile(new_pos).state == Tile.STATE_UNPASSABLE: return False
        old_pos = creature.position
        if queue != None:
            cmd = UndoCommand('move_creature', lambda: creature.move(new_pos), lambda: creature.undo_move(old_pos))
            queue.add(cmd)
        else: OneWayCommand('move_creature', lambda: creature.move(new_pos)).do()
        return True

    def get_tile(self, position):
        '''Get the tile at position.'''
        x, y = position
        return self.tiles[x][y]

    def reachable_positions(self, start, distance):
        '''Return all reachable positions from start in distance. TODO: optimize astar, cause of many calcs here.'''
        rp = set()
        for x in range(start.x - distance, start.x + distance + 1):
            for y in range(start.y - distance, start.y + distance + 1):
                if x == start.x and y == start.y: continue
                if math.fabs(x - start.x) + math.fabs(y - start.y) <= distance and self.tiles[x][y].state == Tile.STATE_PASSABLE:
                    end = self.tiles[x][y]
                    start_tile = self.tiles[x][y]
                    p = self.path_finder.find_path(start_tile, end)
                    if p and len(p.nodes) <= distance + 1:
                        rp.add((x, y))
        return rp

    def position_up(self, pos):
        return (pos[0], pos[1] - 1)

    def position_down(self, pos):
        return (pos[0], pos[1] + 1)

    def position_left(self, pos):
        return (pos[0] - 1, pos[1])

    def position_right(self, pos):
        return (pos[0] + 1, pos[1])


class Configuration(dict):
    '''Game configuration based on YAML files.'''

    def __init__(self, default_config = 'data/config.yaml', user_config = 'data/user_config.yaml'):
        self.user_file_path = user_config
        default_file = file(default_config, 'rb')
        user_file = file(self.user_file_path, 'rb')
        self.update(yaml.load(default_file))
        self._user_config = yaml.load(user_file)
        user_file.close()
        default_file.close()
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


class Launcher():
    '''
    Launch the game.
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
        self.player = Player(heros = [Creature(self.cfg['creatures']['sheep'], self.creatures['sheep']),
                                      Creature(self.cfg['creatures']['sheep'], self.creatures['sheep']),
                                      Creature(self.cfg['creatures']['sheep'], self.creatures['sheep']),
                                      Creature(self.cfg['creatures']['sheep'], self.creatures['sheep'])])
        from dgame.generator import EnvironmentGenerator
        self.env_generator = EnvironmentGenerator(self.cfg['generator'], self.cfg['creatures'], seed = 'testing')
        self.env = self.env_generator.create(Environment(biome = self.biomes['default'],
                                                         config = self.cfg['environment'],
                                                         map_size_name = 'small',
                                                         player = self.player),
                                             self.creatures)
        self.camera = Map(pygame.Rect((0, 0), (self.width, self.height - 256)),
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
        pygame.key.set_repeat(200, 10)
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
        profile_result = profile(Launcher().run)
        print(profile_result)
    else:
        Launcher().run()
