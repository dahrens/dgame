import pygame, sys, logging
from dgame.event import EventDispatcher, ActorMixin
from dgame.generate import MapGenerator
from dgame.ui import MapUi, Biomes, init_biomes


class Map(ActorMixin):

    key = True

    def __init__(self, biome = None, size_in_tiles = (100, 100), tile_size = (32, 32)):
        self.size_in_tiles = size_in_tiles
        self.tile_size = tile_size
        self.biome = biome
        self.tiles = [[Tile((x, y), ui = biome.unpassable) for y in range(self.size_in_tiles[1])] for x in range(self.size_in_tiles[0])]
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

    def __init__(self, position, state = STATE_UNPASSABLE, ui = None):
        self.position = position
        self.state = state
        self.ui = ui


class Game(ActorMixin):

    key = True

    def __init__(self):
        pygame.init()
        self.modes = pygame.display.list_modes()
        logging.basicConfig(level = logging.DEBUG)
        tile_width, tile_height = (32, 32)
        self.screen_size = self.width , self.height = (40 * tile_width, 20 * tile_height)
        self.fullscreen = False
        if self.fullscreen:
            self.screen = pygame.display.set_mode(self.screen_size, pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
        else:
            self.screen = pygame.display.set_mode(self.screen_size)
        self.screen.fill((0, 0, 0))
        self.dispatcher = EventDispatcher()
        self.dispatcher.register(self)
        init_biomes()
        self.map_generator = MapGenerator(biome = Biomes['default'], size_in_tiles = (80, 40))
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
