# coding=utf-8
import pygame


class EventDispatcher(object):

    def __init__(self, controls = {}, actors = {}):
        self.actors = actors
        self.commands = {}
        self.keydown_events = {}
        for actor_name, actor_controls in controls.iteritems():
            for method_name, key_bindings in actor_controls.iteritems():
                command_name = actor_name + '_' + method_name
                self.commands[command_name] = getattr(self.actors[actor_name], method_name)
                for k in key_bindings:
                    self.keydown_events[getattr(pygame, k)] = command_name

    def dispatch(self, event):
        if event.type == pygame.MOUSEMOTION or event.type == pygame.MOUSEBUTTONUP or event.type == pygame.MOUSEBUTTONDOWN:
            return True
        elif event.type == pygame.KEYDOWN:
            if event.key in self.keydown_events:
                self.commands[self.keydown_events[event.key]]()
            return True
        elif event.type == pygame.KEYUP:
            return True
        elif event.type == pygame.QUIT:
            return False
        else:
            return True
