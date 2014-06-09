import pygame, os


BIOMES_PATH = ['data', 'sprites', 'biomes']

BIOMES = {
    'default': {
        'entrance': 'stone_stairs_up',
        'exit': 'stone_stairs_down',
        'unpassable': ['stone_dark0', 'wall_vines0', 'wall_vines1', 'wall_vines2', 'wall_vines3', 'wall_vines4', 'wall_vines5', 'wall_vines6'],
        'passable': ['floor_vines0', 'floor_vines1', 'floor_vines2', 'floor_vines3', 'floor_vines4', 'floor_vines5', 'floor_vines6']
    },
}


class SpriteSheet(dict):

    def __init__(self, biome = 'default', image_format = 'png', sprite_size = (32, 32)):
        path = BIOMES_PATH
        path.append(biome)
        self.folder = os.path.join(*path)
        for f in os.listdir(self.folder):
            if f.endswith('.' + image_format):
                self[f.split('.')[0]] = pygame.image.load(os.path.join(*[self.folder, f])).convert()


class MapUi(pygame.Surface):

    SCROLL_UP = 1
    SCROLL_DOWN = 2
    SCROLL_LEFT = 3
    SCROLL_RIGHT = 4

    def __init__(self, tiles, biome = 'default', size_in_tiles = (100, 100), tile_size = (32, 32), camera_size = (20 * 32, 20 * 32), camera_position = (0, 0)):
        self.biome = biome
        self.width = size_in_tiles[0] * tile_size[0]
        self.height = size_in_tiles[1] * tile_size[1]
        self.size_in_tiles = size_in_tiles
        self.tile_size = tile_size
        self.camera_size = camera_size
        self.camera_position = camera_position
        self.biome_sheet = SpriteSheet(self.biome)
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
                self.blit(self.biome_sheet.get(tile.ui), (tile.position[0] * self.tile_size[0], tile.position[1] * self.tile_size[1]))
        self.render_camera()

    def render_camera(self):
        self.camera = self.subsurface(pygame.Rect(self.camera_position, self.camera_size))


class TileUi(pygame.Surface):

    def __init__(self, size):
        self.width = size[0]
        self.height = size[1]
        self.size = size
