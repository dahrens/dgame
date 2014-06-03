import sys, pygame
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

    def __init__(self, size_in_tiles = (100, 100), viewport_size = (64 * 24, 64 * 16), initial_viewport_position = (0, 0)):
        self.tile_width = self.tile_height = 64
        size = (size_in_tiles[0] * self.tile_width, size_in_tiles[1] * self.tile_height)
        self.surface = pygame.surface.Surface(size)
        self.tiles = [[Tile((x * self.tile_width, y * self.tile_height), (self.tile_width, self.tile_height), self.surface) for y in range(size_in_tiles[1])] for x in range(size_in_tiles[0])]
        self.viewport_position = initial_viewport_position
        self.viewport_size = viewport_size
        self.viewport = pygame.Surface(viewport_size)
        self.render()

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

    def _get_current_hovered_tile(self, position):
        x = position[0] / self.tile_width
        y = position[1] / self.tile_width
        return self.tiles[x][y]

    def render(self):
        self._render_viewport()
        pygame.display.get_surface().blit(self.viewport, (0, 0))

    def _render_viewport(self):
        self.viewport.blit(self.surface, (0, 0), (self.viewport_position, self.viewport_size))

class Tile(object):

    def __init__(self, position, size, surface):
        self.surface = surface
        self.position = position
        self.size = size
        self.border = 2
        self.inner_position = (self.position[0] + self.border, self.position[1] + self.border)
        self.inner_size = (self.size[0] - 2 * self.border, self.size[1] - 2 * self.border)
        self.font_position = (self.position[0] + 4 * self.border, self.position[1] + 4 * self.border)
        self._hover = False
        self.color = (190, 190, 190)
        self.hover_color = (200, 200, 200)
        self.background_color = (255, 255, 255)
        self.background_hover_color = (255, 0, 0)
        self.render()

    def toggle_hover(self):
        self._hover = not self._hover
        self.render()

    def render(self):
        self.surface.fill(self.background_color if not self._hover else self.background_hover_color,
                          pygame.Rect(self.position, self.size))
        self.surface.fill(self.color if not self._hover else self.hover_color,
                          pygame.Rect(self.inner_position, self.inner_size))
        font = pygame.font.Font(None, 14)

        font_surface = font.render(str(self.position), True, pygame.Color("black"))
        self.surface.blit(font_surface, self.font_position)


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
            self.map.render()
            pygame.display.flip()
        sys.exit()


if __name__ == '__main__':
    Game().run()
