import sys, pygame
from pygame import gfxdraw
import logging


class ActorMixin(object):
    mouse = False
    key = False
    active = True

    def handle_mouse(self, event):
        pass

    def handle_key(self, event):
        pass

class EventDispatcher(object):
    def __init__(self):
        self.mouse_actors = []
        self.key_actors = []

    def register(self, actor):
        if actor.key: self.key_actors.append(actor)
        if actor.mouse: self.mouse_actors.append(actor)

    def dispatch(self, event):
        if event.type == pygame.MOUSEMOTION or event.type == pygame.MOUSEBUTTONUP or event.type == pygame.MOUSEBUTTONDOWN:
            self._mouse(event)
            return True
        elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
            self._key(event)
            return True
        elif event.type == pygame.QUIT:
            return False
        else:
            logging.warning('Unhandled event: ' + str(event))
            return True

    def _mouse(self, event):
        for m in self.mouse_actors:
            if not m.active: continue
            if m.handle_mouse(event): return
        logging.warning('Unhandled event: ' + str(event))

    def _key(self, event):
        for k in self.key_actors:
            if not k.active: continue
            if k.handle_key(event): return
        logging.warning('Unhandled event: ' + str(event))


class Map(ActorMixin):

    mouse = True

    def __init__(self):
        self.tile_side_length = 16
        self.border = 2
        self.tiles = {}
        # self.surface = pygame.surface.Surface()
        width = pygame.display.get_surface().get_size()[0]
        self.hovered_tile = None
        for i in range(0, width / self.tile_side_length):
            self.tiles[i] = {}
            for j in range(0, width / self.tile_side_length):
                t = Tile((i * (self.tile_side_length + self.border), j * (self.tile_side_length + self.border)), (self.tile_side_length, self.tile_side_length), pygame.display.get_surface())
                t.render()
                self.tiles[i][j] = t

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

    def _get_current_hovered_tile(self, position):
        x = position[0] / (self.tile_side_length + self.border)
        y = position[1] / (self.tile_side_length + self.border)
        return self.tiles[x][y]

class Tile(object):
    def __init__(self, position, size, surface):
        self.surface = surface
        self.position = position
        self.size = size
        self.color = (255, 255, 255)
        self.hover_color = (100, 100, 100)
        self._hover = False

    def toggle_hover(self):
        self._hover = not self._hover
        self.render()

    def render(self):
        color = self.color if not self._hover else self.hover_color
        self.surface.fill(color, pygame.Rect(self.position, self.size))


class Menu(ActorMixin):

    ACTIVATE = pygame.USEREVENT + 1
    DEACTIVATE = pygame.USEREVENT + 2
    mouse = True
    key = True

    def __init__(self):
        pass


class Game(ActorMixin):

    key = True

    def __init__(self):
        pygame.init()
        self.modes = pygame.display.list_modes()
        self.screen_size = self.width , self.height = self.modes[0]
        self.fullscreen = True
        if self.fullscreen:
            screen = pygame.display.set_mode(self.screen_size, pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
        else:
            screen = pygame.display.set_mode(self.screen_size)
        screen.fill((0, 0, 0))
        self.dispatcher = EventDispatcher()
        self.dispatcher.register(self)
        self.map = Map()
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
