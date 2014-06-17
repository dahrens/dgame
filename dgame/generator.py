# coding=utf-8
'''
Generating the environment. Needs refactoring.
'''
import random, logging
from dgame.core import Creature


class EnvironmentGenerator(object):

    def __init__(self, config, creature_config, seed = None):
        self.config = config
        self.creature_config = creature_config
        if seed:
            random.seed(seed)

    def create(self, env, creatures):
        '''Create a environment based on the configuration on a incoming environment that includes only unpassable tiles.'''
        self.env = env
        self.open_pos = self._get_pos_set((1, 1), (self.env.size[0] - 2, self.env.size[1] - 2))
        self.close_pos = set()
        self.rooms = []
        self.gen_rooms_from_config(self.config['map_config'][self.env.map_size_name])
        self.place_player_heros()
        self.place_creatures(creatures)
        return self.env

    def place_creatures(self, creatures):
        '''Place some creatures in the environment.'''
        for _ in range(2):
            pos = random.sample(self.rooms[0]['free'], 1)[0]
            Creature(config = self.creature_config['sheep'],
                     sheet = creatures['sheep'],
                     env = self.env,
                     pos = pos)
            self.env.get_tile(pos).state = -1

    def place_player_heros(self):
        '''Place all heros of the player together in the first generated room.'''
        for hero in self.env.player.heros:
            hero.position = random.sample(self.rooms[0]['free'], 1)[0]
            hero.env = self.env
            self.env.creatures.append(hero)
            self.env.get_tile(hero.position).state = -1

    def gen_rooms_from_config(self, config):
        '''Try to generate all rooms configured.'''
        for room_type, num in config.iteritems():
            for _ in range(num):
                try:
                    self.rooms.append(self.gen_room(self.config[room_type]))
                except Exception:
                    logging.warning('can not find suitable place for another room.')

    def gen_room(self, size_template):
        '''Generate a room with a random size described by size_template.'''
        size = (random.randrange(size_template[0][0], size_template[1][0]),
                random.randrange(size_template[0][1], size_template[1][1]))
        start_pos, room_pos = self.find_free_space(size)
        room_pos_used, room_pos_free = self.decorate_room(start_pos, room_pos, size)
        return {'used': room_pos_used, 'free': room_pos_free}

    def find_free_space(self, size):
        '''Find s suitable place for a room in the map.'''
        for i in range(1000):
            start_pos = self._get_free_pos()
            room_pos = self._get_pos_set(start_pos, size)
            if room_pos <= self.open_pos:
                self._close_position(room_pos)
                return start_pos, room_pos
            if i == 999:
                raise Exception('Can not find suitable place.')

    def decorate_room(self, start_pos, room_pos, size):
        '''Fill a room with different tiles.'''
        room_pos_used = set()
        room_pos_free = set()
        for x, y in room_pos:
            if x == start_pos[0] or y == start_pos[1] or x == start_pos[0] + size[0] - 1 or y == start_pos[1] + size[1] - 1:
                self.env.tiles[x][y].ui.image = self.env.biome.wall
                room_pos_used.add((x, y))
            else:
                self.env.tiles[x][y].ui.image = self.env.biome.passable
                self.env.tiles[x][y].state = self.env.tiles[x][y].STATE_PASSABLE
                room_pos_free.add((x, y))
        return room_pos_used, room_pos_free

    def _get_pos_set(self, start_pos, size):
        '''Get a set including all positions from start_pos with size.'''
        s = set()
        for x in range(start_pos[0], start_pos[0] + size[0]):
            for y in range(start_pos[1], start_pos[1] + size[1]):
                s.add((x, y))
        return s

    def _close_position(self, pos_set):
        '''Mark a set of positions as used.'''
        self.open_pos -= pos_set
        self.close_pos = self.close_pos | pos_set

    def _get_free_pos(self):
        '''Get a random posotion of the map that is unused.'''
        return random.sample(self.open_pos, 1)[0]
