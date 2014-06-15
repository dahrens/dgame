# coding=utf-8
'''The event module handles the incoming input and dispatches it to the actors'''
import pygame
from collections import namedtuple, OrderedDict, _itemgetter, deque


class EventDispatcher(object):

    def __init__(self, controls = {}, actors = {}):
        '''
        Initialize this dispatcher.

        Create commands for all configured controls as OneWayComands here.
        Those commands may create and Queue other commands on their own, like the Player class is doing.

        '''
        self.actors = actors
        self.commands = {}
        self.keydown_events = {}
        for actor_name, actor_controls in controls.iteritems():
            for method_name, key_bindings in actor_controls.iteritems():
                command_name = actor_name + '_' + method_name
                self.commands[command_name] = OneWayCommand(command_name, getattr(self.actors[actor_name], method_name))
                for k in key_bindings:
                    if not getattr(pygame, k) in self.keydown_events:
                        self.keydown_events[getattr(pygame, k)] = []
                    self.keydown_events[getattr(pygame, k)].append(command_name)

    def dispatch(self, event):
        '''
        Dispatch incoming events from pygame.

        Currently only KEYDOWN and QUIT were handled at all.

        '''
        if event.type == pygame.MOUSEMOTION:
            return True
        elif event.type == pygame.MOUSEBUTTONUP or event.type == pygame.MOUSEBUTTONDOWN:
            return True
        elif event.type == pygame.KEYDOWN:
            if event.key in self.keydown_events:
                for cmd in self.keydown_events[event.key]:
                    if self.commands[cmd].do(): return True
            return True
        elif event.type == pygame.KEYUP:
            return True
        elif event.type == pygame.QUIT:
            return False
        else:
            return True


class CommandQueue(deque):
    '''Use this class to manage commands that can be undone.'''

    def add(self, cmd):
        '''Executes a command and adds it to the queue.'''
        if isinstance(cmd, UndoCommand):
            cmd.do()
        self.append(cmd)

    def undo(self):
        '''Undo the last done command and forget about it.'''
        if len(self) > 0:
            cmd = self.pop()
            if isinstance(cmd, UndoCommand):
                cmd.undo()

    def flush(self):
        '''Clear the queue. TODO: handle execution of the FlushCommand.'''
        while len(self) > 0:
            cmd = self.popleft()
            if isinstance(cmd, FlushCommand):
                cmd.do()


OneWayCommand = namedtuple('OneWayCommand', ['name', 'do'])
FlushCommand = OneWayCommand
'''FlushCommands are special OneWayCommands that will be executed when a CommandQueue gets flushed.'''
UndoCommand = namedtuple('UndoCommand', ['name', 'do', 'undo'])
