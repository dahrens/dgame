import sys, pygame
import logging

class Sprite(object):

    def __init__(self, rect, parent, sprite = None):
        self.rect = rect
        self.parent = parent
        self.sprite = pygame.Surface(rect.size) if sprite == None else sprite
        self.render()

    def render(self):
        self._render()
        self.parent.blit(self.sprite, self.rect.topleft)

    def _render(self):
        pass


class ViewportSprite(Sprite):

    def __init__(self, rect, parent, sprite_size, viewport_position):
        self.viewport_position = viewport_position
        sprite = pygame.Surface(sprite_size)
        self.viewport = pygame.Surface(rect.size)
        super(ViewportSprite, self).__init__(rect, parent, sprite)

    def render(self):
        self.viewport.blit(self.sprite, self.rect, (self.viewport_position, self.rect.size))
        self._render()
        self.parent.blit(self.viewport, self.rect.topleft)
