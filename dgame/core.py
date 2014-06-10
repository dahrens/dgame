# coding=utf-8
import pygame, sys, logging, yaml, collections, dgame
from dgame.event import EventDispatcher, ActorMixin
from dgame.generate import MapGenerator
from dgame.ui import MapUi, TileUi, CreatureUi


class Player(ActorMixin):

    key = True

    def __init__(self):
        self.ui = CreatureUi()

class Map(ActorMixin):

    key = True

    def __init__(self, biome = None, size_in_tiles = (100, 100), tile_size = (32, 32)):
        self.size_in_tiles = size_in_tiles
        self.tile_size = tile_size
        self.biome = biome
        self.tiles = [[Tile((x, y)) for y in range(self.size_in_tiles[1])] for x in range(self.size_in_tiles[0])]
        self.ui = MapUi(self.tiles, self.biome, self.size_in_tiles, self.tile_size)

    def handle_key(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
            return self.ui.scroll(MapUi.SCROLL_UP)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
            return self.ui.scroll(MapUi.SCROLL_DOWN)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
            return self.ui.scroll(MapUi.SCROLL_LEFT)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
            return self.ui.scroll(MapUi.SCROLL_RIGHT)
        else:
            return False


class Tile(object):

    STATE_PASSABLE = 1
    STATE_UNPASSABLE = 2

    def __init__(self, position, state = STATE_UNPASSABLE):
        self.position = position
        self.state = state
        self.objects = []
        self.ui = TileUi()


class Configuration(dict):

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

class Game(ActorMixin):

    key = True

    def __init__(self):
        pygame.init()
        self.modes = pygame.display.list_modes()
        logging.basicConfig(level = logging.DEBUG)
        self.cfg = Configuration()
        logging.debug('cfg: {}'.format(self.cfg))
        tile_width, tile_height = self.cfg['ui']['tiles']['size']
        self.screen_size = self.width , self.height = self.cfg['gfx']['resolution']
        self.fullscreen = self.cfg['gfx']['fullscreen']
        if self.fullscreen:
            self.screen = pygame.display.set_mode(self.screen_size, pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
        else:
            self.screen = pygame.display.set_mode(self.screen_size)
        self.screen.fill((0, 0, 0))
        self.dispatcher = EventDispatcher()
        self.dispatcher.register(self)
        dgame.ui.init_biomes(self.cfg['ui']['biomes'])
        self.map_generator = MapGenerator(biome = dgame.ui.current_biome, size_in_tiles = (80, 40))
        self.map = self.map_generator.run()
        self.map.ui.camera_size = (40 * tile_width, 20 * tile_height)
        self.dispatcher.register(self.map)
        self.map.ui.render()
        self.screen.blit(self.map.ui.camera, (0, 0))

    def handle_key(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return True

    def run(self):
        running = True
        pygame.key.set_repeat(10, 10)
        while running:
            for event in pygame.event.get():
                running = self.dispatcher.dispatch(event)
            self.screen.blit(self.map.ui.camera, (0, 0))
            pygame.display.flip()
        sys.exit()


if __name__ == '__main__':
    Game().run()
