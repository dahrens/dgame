# coding=utf-8
import random, logging


class EnvironmentGenerator(object):

    def __init__(self, config, seed = None):
        self.config = config
        if seed:
            random.seed(seed)

    def create(self, env, player):
        self.env = env
        logging.debug('generated env tiles len: {}/{}'.format(len(self.env.tiles), len(self.env.tiles[0])))
        self.open_pos = self._get_pos_set((1, 1), (self.env.size[0] - 2, self.env.size[1] - 2))
        self.close_pos = set()
        self.rooms = []
        cfg = self.config['map_config'][self.env.map_size_name]
        for _ in range(cfg['large_rooms']):
            room_positions = self.gen_room(self.config['large_room'])
            if room_positions:
                self.rooms.append(room_positions)
            else:
                logging.warning('can not find suitable place for another room.')
        for _ in range(cfg['small_rooms']):
            room_positions = self.gen_room(self.config['small_room'])
            if room_positions:
                self.rooms.append(room_positions)
            else:
                logging.warning('can not find suitable place for another room.')
        for _ in range(cfg['medium_rooms']):
            room_positions = self.gen_room(self.config['medium_room'])
            if room_positions:
                self.rooms.append(room_positions)
            else:
                logging.warning('can not find suitable place for another room.')
        for hero in player.heros:
            hero.position = random.sample(self.rooms[0]['free'], 1)[0]
            hero.env = self.env
            self.env.creatures[hero.position] = hero
        return self.env

    def gen_room(self, size_template):
        size = (random.randrange(size_template[0][0], size_template[1][0]),
                random.randrange(size_template[0][1], size_template[1][1]))
        logging.debug('generate room with size: {}'.format(size))
        for i in range(1000):
            start_pos = self._get_free_pos()
            logging.debug('try to generate room at : {}'.format(start_pos))
            room_pos = self._get_pos_set(start_pos, size)
            if room_pos <= self.open_pos:
                self._close_position(room_pos)
                break
            if i == 999:
                return False
        room_pos_used = set()
        room_pos_free = set()
        for x, y in room_pos:
            if x == start_pos[0] or y == start_pos[1] or x == start_pos[0] + size[0] - 1 or y == start_pos[1] + size[1] - 1:
                self.env.tiles[x][y].image = self.env.biome.wall
                room_pos_used.add((x, y))
            else:
                self.env.tiles[x][y].image = self.env.biome.passable
                self.env.tiles[x][y].state = self.env.tiles[x][y].STATE_PASSABLE
                room_pos_free.add((x, y))
        return {'used': room_pos_used, 'free': room_pos_free}


    def _get_pos_set(self, start_pos, size):
        s = set()
        for x in range(start_pos[0], start_pos[0] + size[0]):
            for y in range(start_pos[1], start_pos[1] + size[1]):
                s.add((x, y))
        return s

    def _close_position(self, pos_set):
        self.open_pos -= pos_set
        self.close_pos = self.close_pos | pos_set

    def _get_free_pos(self):
        return random.sample(self.open_pos, 1)[0]
