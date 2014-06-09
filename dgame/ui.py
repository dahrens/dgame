import pygame, os, random


_BIOMES_CONFIG = {
    'default': {
        'entrance': 'stone_stairs_up',
        'exit': 'stone_stairs_down',
        'unpassable': ['stone_dark0'],
        'passable': ['floor_vines0'],
        'wall': ['wall_vines0', 'wall_vines1', 'wall_vines2', 'wall_vines3', 'wall_vines4', 'wall_vines5', 'wall_vines6'],
        'floor': ['floor_vines1', 'floor_vines2', 'floor_vines3', 'floor_vines4', 'floor_vines5', 'floor_vines6'],
    },
}

_Biomes = {}

class SpriteSheet(dict):

    def __init__(self, path, image_format = 'png', sprite_size = (32, 32)):
        self.folder = os.path.join(*path)
        for f in os.listdir(self.folder):
            if f.endswith('.' + image_format):
                self[f.split('.')[0]] = pygame.image.load(os.path.join(*[self.folder, f])).convert()

class Biome(object):

    def __init__(self, name, config):
        self._name = name
        self._config = config
        self._sheet = SpriteSheet(['data', 'sprites', 'biomes', name])

    @property
    def unpassable(self):
        return self._sheet[self._config['unpassable'][random.randrange(0, len(self._config['unpassable']))]]

    @property
    def passable(self):
        return self._sheet[self._config['passable'][random.randrange(0, len(self._config['passable']))]]

    @property
    def wall(self):
        return self._sheet[self._config['wall'][random.randrange(0, len(self._config['wall']))]]

def init_biomes():
    for name, config in _BIOMES_CONFIG.iteritems():
        _Biomes[name] = Biome(name, config)


def get_biome(name = None):
    if name == None and not '_current' in _Biomes:
        _Biomes['_current'] = _Biomes['default']
    elif name != None:
        _Biomes['_current'] = _Biomes[name]
    return _Biomes['_current']


class MapUi(pygame.Surface):

    SCROLL_UP = 1
    SCROLL_DOWN = 2
    SCROLL_LEFT = 3
    SCROLL_RIGHT = 4

    def __init__(self, tiles, biome = None, size_in_tiles = (100, 100), tile_size = (32, 32), camera_size = (20 * 32, 20 * 32), camera_position = (0, 0)):
        self.biome = biome
        self.width = size_in_tiles[0] * tile_size[0]
        self.height = size_in_tiles[1] * tile_size[1]
        self.size_in_tiles = size_in_tiles
        self.tile_size = tile_size
        self.camera_size = camera_size
        self.camera_position = camera_position
        self.scroll_speed = 16
        self.tiles = tiles
        super(MapUi, self).__init__((self.width, self.height))
        self.fill((0, 0, 0))
        self.camera = self.subsurface(pygame.Rect(camera_position, camera_size))

    def scroll(self, direction):
        scrolled = False
        if direction == self.SCROLL_UP:
            if self.camera_position[1] - self.scroll_speed >= 0:
                self.camera_position = (self.camera_position[0], self.camera_position[1] - self.scroll_speed)
                scrolled = True
        elif direction == self.SCROLL_DOWN:
            if self.camera_position[1] + self.scroll_speed <= self.height - self.camera_size[1]:
                self.camera_position = (self.camera_position[0] , self.camera_position[1] + self.scroll_speed)
                scrolled = True
        elif direction == self.SCROLL_LEFT:
            if self.camera_position[0] - self.scroll_speed >= 0:
                self.camera_position = (self.camera_position[0] - self.scroll_speed, self.camera_position[1])
                scrolled = True
        elif direction == self.SCROLL_RIGHT:
            if self.camera_position[0] + self.scroll_speed <= self.width - self.camera_size[0]:
                self.camera_position = (self.camera_position[0] + self.scroll_speed, self.camera_position[1])
                scrolled = True
        else:
            raise Exception('Do not know the direction')
        if scrolled: self.render_camera()
        return scrolled

    def render(self):
        for column in self.tiles:
            for tile in column:
                self.blit(tile.ui.background, (tile.position[0] * self.tile_size[0], tile.position[1] * self.tile_size[1]))
        self.render_camera()

    def render_camera(self):
        self.camera = self.subsurface(pygame.Rect(self.camera_position, self.camera_size))


class TileUi(pygame.sprite.Sprite):

    def __init__(self):
        super(TileUi, self).__init__()
        self.background = get_biome().unpassable


class CreatureUi(pygame.Surface):
    pass
