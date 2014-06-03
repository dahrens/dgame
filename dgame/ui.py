import sys, pygame
import logging

class Element(object):

    def __init__(self, rect, parent, z_index = 0):
        self.rect = rect
        self.parent = parent
        self.z_index = z_index
        self.el = pygame.Surface(rect.size)

    def render(self):
        self.parent.blit(self.el, self.rect.topleft)


class Sprite(Element):

    def __init__(self, rect, parent, sprite_size, sprite_pos):
        self.sprite_pos = sprite_pos
        self.sprite = pygame.Surface(sprite_size)
        super(Sprite, self).__init__(rect, parent)

    def render(self):
        self.el.blit(self.sprite, self.rect, (self.sprite_pos, self.rect.size))
        super(Sprite, self).render()


class UiMixin():

    _ui_class = Element

    _ui_kwargs = {}

    def __init__(self, **kwargs):
        self.ui = self.setup_ui(kwargs)

    def setup_ui(self, **kwargs):
        k = self._ui_class(**kwargs)
        k.render()
        return k
