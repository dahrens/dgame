# coding=utf-8
'''
dgame is just a playground for python and pygame.
'''
import pygame
import sys, os, logging, math
import collections, random, yaml
from itertools import chain
from dgame.event import EventDispatcher, ActorMixin
from dgame.generator import MapGenerator

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


class SpriteDict(dict):
    '''
    Load a folder with images into itself.

    You can access them like this:
        sd = SpriteDict(*path)
        sd['filenamewithoutextension']

    '''

    def __init__(self, path, image_format = 'png'):
        self.folder = os.path.join(*path)
        for f in os.listdir(self.folder):
            if f.endswith('.' + image_format):
                self[f.split('.')[0]] = pygame.image.load(os.path.join(*[self.folder, f])).convert()


class Biome(object):
    '''A Biome is colletion of images, that are abstracted to their use'''

    def __init__(self, name, config):
        self._name = name
        self._config = config
        self._sheet = SpriteDict(['data', 'sprites', 'biomes', name])

    @property
    def unpassable(self):
        return self._sheet[self._config['unpassable'][random.randrange(0, len(self._config['unpassable']))]]

    @property
    def passable(self):
        return self._sheet[self._config['passable'][random.randrange(0, len(self._config['passable']))]]

    @property
    def wall(self):
        return self._sheet[self._config['wall'][random.randrange(0, len(self._config['wall']))]]


class Map(pygame.sprite.DirtySprite, ActorMixin):
    '''The game map. UI and logic combine :-/'''

    SCROLL_UP = 1
    SCROLL_DOWN = 2
    SCROLL_LEFT = 3
    SCROLL_RIGHT = 4

    key = True

    def __init__(self, biome = None, size_in_tiles = (128, 128), tile_size = (32, 32), rect = pygame.Rect((0, 0), (20 * 32, 20 * 32)), position_camera = (0, 0)):
        super(Map, self).__init__()
        self.biome = biome
        self.size_in_tiles = size_in_tiles
        self.tile_size = tile_size
        self.width = size_in_tiles[0] * tile_size[0]
        self.height = size_in_tiles[1] * tile_size[1]
        self.rect = rect
        self.camera_rect = pygame.Rect(position_camera, self.rect.size)

        self.surface = pygame.Surface((self.width, self.height))
        self.surface.fill((200, 200, 200))
        self.background = self.surface.copy()

        self.tiles = [[self._default_tile(x, y) for y in range(self.size_in_tiles[1])] for x in range(self.size_in_tiles[0])]
        self.scroll_speed = 16

        self.group = pygame.sprite.LayeredDirty(chain.from_iterable(self.tiles))
        self.image = self.surface.subsurface(self.camera_rect)
        self.rect = rect

    def handle_key(self, event):
        '''Handles all keyboard bound events.'''
        if event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
            return self.scroll(self.SCROLL_UP)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
            return self.scroll(self.SCROLL_DOWN)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
            return self.scroll(self.SCROLL_LEFT)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
            return self.scroll(self.SCROLL_RIGHT)
        else:
            return False

    def scroll(self, direction):
        '''Scrolls the map self.scroll_speed pixels in the given direction'''
        if direction == self.SCROLL_UP \
        and self.camera_rect.y - self.scroll_speed >= 0:
                self.camera_rect.y -= self.scroll_speed
        elif direction == self.SCROLL_DOWN \
        and self.camera_rect.y + self.scroll_speed <= self.height - self.camera_rect.height:
                self.camera_rect.y += self.scroll_speed
        elif direction == self.SCROLL_LEFT \
        and self.camera_rect.x - self.scroll_speed >= 0:
                self.camera_rect.x -= self.scroll_speed
        elif direction == self.SCROLL_RIGHT \
        and self.camera_rect.x + self.scroll_speed <= self.width - self.camera_rect.width:
                self.camera_rect.x += self.scroll_speed
        else: return False
        return True

    def update(self, *arg):
        self.group.clear(self.surface, self.background)
        self.group.update()
        self.group.set_clip(self.camera_rect)
        self.group.draw(self.surface)
        self.image = self.surface.subsurface(pygame.Rect(self.camera_rect))

    def _default_tile(self, x, y):
        return Tile((x, y),
                    pygame.Rect((x * self.tile_size[0], y * self.tile_size[1]),
                                self.tile_size),
                    self.biome.unpassable)


class Tile(pygame.sprite.DirtySprite):
    '''One tile of the map.'''

    STATE_PASSABLE = 1
    STATE_UNPASSABLE = 2

    def __init__(self, pos_map, pos_surface, background = None, state = STATE_UNPASSABLE):
        super(Tile, self).__init__()
        self.pos_map = pos_map
        self.rect = pos_surface
        self.image = background
        self.state = state


class FpsLayer(pygame.sprite.Sprite):
    '''Sprite to show the FPS'''

    def __init__(self, font, clock, position):
        super(FpsLayer, self).__init__()
        self.font = font
        self.clock = clock
        self.position = position
        self.update()

    def update(self, *args):
        self.image = self.font.render(str(math.ceil(self.clock.get_fps() * 1000) / 1000) + ' fps', True, (10, 10, 10))
        self.rect = pygame.Rect(self.position, self.image.get_rect().size)


class Game(ActorMixin):
    '''Currently the launcher.

    TODO: seperate game from launch process, to allow saving.

    '''

    key = True

    def __init__(self):
        pygame.init()
        self.modes = pygame.display.list_modes()
        self.cfg = Configuration()
        logging.debug('cfg: {}'.format(self.cfg))

        self.screen_size = self.width , self.height = self.cfg['gfx']['resolution']
        if self.cfg['gfx']['fullscreen']:
            self.screen = pygame.display.set_mode(self.screen_size, pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
        else:
            self.screen = pygame.display.set_mode(self.screen_size)
        self.background = pygame.Surface(self.screen_size)
        self.background.fill((200, 200, 200))
        self.screen.blit(self.background, (0, 0))

        self.font = pygame.font.SysFont('mono', 20, bold = True)
        self.clock = pygame.time.Clock()
        self.fps = 30
        self.playtime = 0.0

        self.biomes = self.init_biomes(self.cfg['ui']['biomes'])
        self.dispatcher = EventDispatcher()
        self.map = Map(biome = self.biomes['default'],
                       size_in_tiles = (100, 100),
                       tile_size = self.cfg['ui']['tiles']['size'],
                       rect = pygame.Rect((0, 0), (self.width, self.height - 200)))
        self.map_generator = MapGenerator()
        self.map = self.map_generator.create(self.map)
        self.fps_ui = FpsLayer(self.font, self.clock, (self.width - 150, self.height - 30))

        self.dispatcher.register(self)
        self.dispatcher.register(self.map)

        self.ui_group = pygame.sprite.RenderUpdates(self.map, self.fps_ui)

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
            milliseconds = self.clock.tick(self.fps)
            self.playtime += milliseconds / 1000.0
            self.ui_group.clear(self.screen, self.background)
            self.ui_group.update()
            pygame.display.update(self.ui_group.draw(self.screen))

    def init_biomes(self, c):
        _b = {}
        for name, config in c.iteritems():
            _b[name] = Biome(name, config)
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
