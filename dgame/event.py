# coding=utf-8
import pygame
# import logging

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
            # logging.warning('Unhandled event: ' + str(event))
            return True

    def _mouse(self, event):
        for m in self.mouse_actors:
            if not m.active: continue
            if m.handle_mouse(event): return
        # logging.warning('Unhandled event: ' + str(event))

    def _key(self, event):
        for k in self.key_actors:
            if not k.active: continue
            if k.handle_key(event): return
        # logging.warning('Unhandled event: ' + str(event))
