# coding=utf-8
'''
dgame is just a playground for python and pygame.
'''
from __future__ import division
import pygame
import sys, os, logging, math
import collections, random, yaml
from dgame.event import EventDispatcher, ActorMixin
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
        self._config['_all'] = []
        for imgs in self._config.itervalues():
            self._config['_all'].extend(imgs)
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

    @property
    def rand(self):
        return self._sheet[self._config['_all'][random.randrange(0, len(self._config['_all']))]]


ZOOM_LEVELS = [0.25, 0.5, 1.0, 2.0, 4.0]


class Camera(pygame.sprite.Sprite, ActorMixin):

    SCROLL_UP = 1
    SCROLL_DOWN = 2
    SCROLL_LEFT = 3
    SCROLL_RIGHT = 4

    ZOOM_IN = 5
    ZOOM_OUT = 6

    key = True

    class Viewport(object):

        def __init__(self, x, y, w, h):
            self.x = x
            self.y = y
            self.w = w
            self.h = h

    def __init__(self, rect, env, offset = [0.0, 0.0]):
        super(Camera, self).__init__()
        self.env = env
        self.rect = rect
        self.image = pygame.Surface(rect.size).convert()
        self.scroll_speed = 0.5
        self.zoom = 1.0
        self.viewport = self.Viewport(offset[0],
                                 offset[1],
                                 math.ceil(self.rect.width / self.env.tile_width * self.zoom),
                                 math.ceil(self.rect.height / self.env.tile_height * self.zoom))

    def update(self):
        visible_tiles = self._get_visibile()
        self.image.fill((200, 200, 200))
        for tile in visible_tiles:
            self.image.blit(tile.zbg[self.zoom], pygame.Rect(((tile.x - self.viewport.x) * self.env.tile_width * self.zoom,
                                                              (tile.y - self.viewport.y) * self.env.tile_height * self.zoom),
                                                              (int(self.env.tile_width * self.zoom),
                                                               int(self.env.tile_height * self.zoom))))

    def handle_key(self, event):
        '''Handles all keyboard bound events.'''
        if event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
            return self._scroll(self.SCROLL_UP)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
            return self._scroll(self.SCROLL_DOWN)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
            return self._scroll(self.SCROLL_LEFT)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
            return self._scroll(self.SCROLL_RIGHT)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
            return self._scroll(self.SCROLL_RIGHT)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_KP_PLUS:
            return self._zoom(self.ZOOM_IN)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_KP_MINUS:
            return self._zoom(self.ZOOM_OUT)
        else:
            return False

    def _scroll(self, direction):
        '''Scrolls the map self.scroll_speed pixels in the given direction'''
        if direction == self.SCROLL_UP \
        and self.viewport.y - self.scroll_speed >= 0:
                self.viewport.y -= self.scroll_speed
        elif direction == self.SCROLL_DOWN \
        and self.viewport.y + self.scroll_speed <= self.env.height - self.viewport.h:
                self.viewport.y += self.scroll_speed
        elif direction == self.SCROLL_LEFT \
        and self.viewport.x - self.scroll_speed >= 0:
                self.viewport.x -= self.scroll_speed
        elif direction == self.SCROLL_RIGHT \
        and self.viewport.x + self.scroll_speed <= self.env.width - self.viewport.w:
                self.viewport.x += self.scroll_speed
        else: return False
        return True

    def _zoom(self, direction):
        if direction == self.ZOOM_IN \
        and self.zoom * 2 in ZOOM_LEVELS:
                self.zoom *= 2.0
        elif direction == self.ZOOM_OUT\
        and self.zoom / 2 in ZOOM_LEVELS:
                self.zoom /= 2.0
        else: return False
        return True

    def _get_visibile(self):
        v = []
        for x in range(int(math.floor(self.viewport.x)), int(math.ceil(self.viewport.x + (self.viewport.w / self.zoom)))):
            for y in range(int(math.floor(self.viewport.y)), int(math.ceil(self.viewport.y + (self.viewport.h / self.zoom)))):
                try:
                    v.append(self.env.tiles[x][y])
                except IndexError: pass
        return v


class Environment(object):

    def __init__(self, size, tile_size, biome):
        self.size = self.width, self.height = size
        self.tile_size = self.tile_width, self.tile_height = tile_size
        self.biome = biome
        self.tiles = [[self._default_tile(x, y) for y in range(self.height)] for x in range(self.width)]

    def _default_tile(self, x, y):
        return Tile(pygame.Rect((x, y), (1, 1)),
                    self.biome.unpassable)


class Tile(pygame.Rect):

    def __init__(self, rect, bg):
        super(Tile, self).__init__(rect)
        self.bg = bg
        self.zbg = {}
        self.set_bg(bg)

    def set_bg(self, bg):
        self.bg = bg
        for zl in ZOOM_LEVELS:
            self.zbg[zl] = pygame.transform.scale(bg, (int(self.bg.get_rect().width * zl),
                                                       int(self.bg.get_rect().height * zl)))


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
        self.fps = self.cfg['gfx']['max_fps']
        self.playtime = 0.0

        self.biomes = self.init_biomes(self.cfg['ui']['biomes'])
        self.dispatcher = EventDispatcher()
        self.env = Environment(biome = self.biomes['default'],
                       size = (128, 128),
                       tile_size = self.cfg['ui']['tiles']['size'])
        self.env_generator = EnvironmentGenerator()
        self.env = self.env_generator.create(self.env)
        self.camera = Camera(pygame.Rect((0, 0), (self.width, self.height - 200)), self.env)

        self.fps_ui = FpsLayer(self.font, self.clock, (self.width - 150, self.height - 30))

        self.dispatcher.register(self)
        self.dispatcher.register(self.camera)

        self.ui_group = pygame.sprite.LayeredUpdates(self.camera, self.fps_ui)

    def handle_key(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return True

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
