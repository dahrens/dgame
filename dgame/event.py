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
                    self.keydown_events[getattr(pygame, k)] = command_name

    def dispatch(self, event):
        '''
        Dispatch incoming events from pygame.

        Currently only KEYDOWN and QUIT were handled at all.

        '''
        if event.type == pygame.MOUSEMOTION or event.type == pygame.MOUSEBUTTONUP or event.type == pygame.MOUSEBUTTONDOWN:
            return True
        elif event.type == pygame.KEYDOWN:
            if event.key in self.keydown_events:
                self.commands[self.keydown_events[event.key]].do()
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
class OneWayCommand(tuple):
    'OneWayCommand(name, do, undo)'

    __slots__ = ()

    _fields = ('name', 'do')

    def __new__(cls, name, do):
        'Create a new instance of OneWayCommand(name, do)'
        return tuple.__new__(cls, (name, do))

    @classmethod
    def _make(cls, iterable, new = tuple.__new__):
        'Make a new Point object from a sequence or iterable'
        result = new(cls, iterable)
        if len(result) != 2:
            raise TypeError('Expected 2 arguments, got %d' % len(result))
        return result

    def __repr__(self):
        'Return a nicely formatted representation string'
        return 'Command(name=%r, do=%r)' % self

    def _asdict(self):
        'Return a new OrderedDict which maps field names to their values'
        return OrderedDict(zip(self._fields, self))

    def _replace(self, **kwds):
        'Return a new Point object replacing specified fields with new values'
        result = self._make(map(kwds.pop, ('name', 'do'), self))
        if kwds:
            raise ValueError('Got unexpected field names: %r' % kwds.keys())
        return result

    def __getnewargs__(self):
        'Return self as a plain tuple. Used by copy and pickle.'
        return tuple(self)

    __dict__ = property(_asdict)

    name = property(_itemgetter(0), doc = 'The name of the command')

    do = property(_itemgetter(1), doc = 'Execute the command')


FlushCommand = OneWayCommand
'''FlushCommands are special OneWayCommands that will be executed when a CommandQueue gets flushed.'''


UndoCommand = namedtuple('UndoCommand', ['name', 'do', 'undo'])
class UndoCommand(tuple):
    'UndoCommand(name, do, undo)'

    __slots__ = ()

    _fields = ('name', 'do', 'undo')

    def __new__(cls, name, do, undo):
        'Create a new instance of UndoCommand(name, do, undo)'
        return tuple.__new__(cls, (name, do, undo))

    @classmethod
    def _make(cls, iterable, new = tuple.__new__):
        'Make a new UndoCommand object from a sequence or iterable'
        result = new(cls, iterable)
        if len(result) != 3:
            raise TypeError('Expected 3 arguments, got %d' % len(result))
        return result

    def __repr__(self):
        'Return a nicely formatted representation string'
        return 'UndoCommand(name=%r, do=%r, undo=%r)' % self

    def _asdict(self):
        'Return a new OrderedDict which maps field names to their values'
        return OrderedDict(zip(self._fields, self))

    def _replace(self, **kwds):
        'Return a new Point object replacing specified fields with new values'
        result = self._make(map(kwds.pop, ('name', 'do', 'undo'), self))
        if kwds:
            raise ValueError('Got unexpected field names: %r' % kwds.keys())
        return result

    def __getnewargs__(self):
        'Return self as a plain tuple. Used by copy and pickle.'
        return tuple(self)

    __dict__ = property(_asdict)

    name = property(_itemgetter(0), doc = 'The name of the UndoCommand')

    do = property(_itemgetter(1), doc = 'Execute the UndoCommand')

    undo = property(_itemgetter(2), doc = 'Undo the UndoCommand after execution.')
