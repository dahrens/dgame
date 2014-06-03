import sys, pygame
from itertools import chain
from dgame.event import *
from dgame.ui import *
import logging


class Map(ActorMixin, ViewportSprite):

    mouse = True

    def __init__(self, parent, tile_size = 64, size_in_tiles = (8, 8), rect = pygame.Rect((0, 0), (64 * 5, 64 * 5)), viewport_position = (0, 0)):
        self.tile_width = self.tile_height = 64
        sprite_size = (size_in_tiles[0] * self.tile_width, size_in_tiles[1] * self.tile_height)
        super(Map, self).__init__(rect, parent, sprite_size, viewport_position)
        self.tiles = [[Tile(pygame.Rect((x * self.tile_width, y * self.tile_height), (self.tile_width, self.tile_height)), (x, y), self.sprite) for y in range(size_in_tiles[1])] for x in range(size_in_tiles[0])]
        self.hovered_tile = None

    def handle_mouse(self, event):
        self.tile_hover(event.pos)
        return True

    def tile_hover(self, position):
        c = self._get_current_hovered_tile(position)
        if self.hovered_tile == c: return
        if self.hovered_tile != None:
            self.hovered_tile.toggle_hover()
        c.toggle_hover()
        self.hovered_tile = c
        pygame.event.post(pygame.event.Event(UI_RENDER, {'el': self}))

    def _get_current_hovered_tile(self, position):
        x = position[0] / self.tile_width
        y = position[1] / self.tile_width
        return self.tiles[x][y]


class Tile(Sprite):

    def __init__(self, rect, map_pos, parent):
        self.map_pos = map_pos
        self.border = 2
        self.inner_rect = pygame.Rect((self.border, self.border),
                                      (rect.width - 2 * self.border, rect.height - 2 * self.border))
        self._hover = False
        self.color = (190, 190, 190)
        self.hover_color = (200, 200, 200)
        self.background_color = (255, 255, 255)
        self.background_hover_color = (255, 0, 0)
        super(Tile, self).__init__(rect, parent)

    def toggle_hover(self):
        self._hover = not self._hover
        pygame.event.post(pygame.event.Event(UI_RENDER, {'el': self}))

    def _render(self):
        self.sprite.fill(self.background_color if not self._hover else self.background_hover_color)
        self.sprite.fill(self.color if not self._hover else self.hover_color,
                         self.inner_rect)
        font = pygame.font.Font(None, 14)
        font_surface = font.render(str(self.map_pos), False, pygame.Color("black"))
        self.sprite.blit(font_surface, (self.border * 2, self.border * 2))


class Game(ActorMixin):

    key = True

    def __init__(self):
        pygame.init()
        self.modes = pygame.display.list_modes()
        self.screen_size = self.width , self.height = (800, 600)  # self.modes[0]
        self.fullscreen = False
        if self.fullscreen:
            screen = pygame.display.set_mode(self.screen_size, pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
        else:
            screen = pygame.display.set_mode(self.screen_size)
        screen.fill((0, 0, 0))
        self.dispatcher = EventDispatcher()
        self.dispatcher.register(self)
        self.map = Map(pygame.display.get_surface())
        self.map.render()
        self.dispatcher.register(self.map)

    def handle_key(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return True

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                running = self.dispatcher.dispatch(event)
            pygame.display.flip()
        sys.exit()


if __name__ == '__main__':
    Game().run()
