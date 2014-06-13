# coding=utf-8
import pygame
import os, random

class SpriteDict(dict):
    '''
    Load a folder with images into itself.

    You can access them like this:
        sd = SpriteDict(*path)
        sd['filenamewithoutextension']

    '''

    def __init__(self, path, image_format = 'png', zoom_levels = []):
        self.folder = os.path.join(*path)
        for f in os.listdir(self.folder):
            if f.endswith('.' + image_format):
                img = pygame.image.load(os.path.join(*[self.folder, f])).convert()
                name = f.split('.')[0]
                self[name] = {}
                for zl in zoom_levels:
                    z_size = (int(img.get_rect().width * zl), int(img.get_rect().height * zl))
                    self[name][zl] = pygame.transform.scale(img, z_size)


class Biome(object):
    '''A Biome is colletion of images, that are abstracted to their use'''

    def __init__(self, name, config, zoom_levels):
        self._name = name
        self._config = config
        self._config['_all'] = []
        for imgs in self._config.itervalues():
            self._config['_all'].extend(imgs)
        self._sheet = SpriteDict(['data', 'sprites', 'biomes', name], zoom_levels = zoom_levels)

    @property
    def unpassable(self):
        return self._sheet[self._config['unpassable'][random.randrange(0, len(self._config['unpassable']))]]

    @property
    def passable(self):
        return self._sheet[self._config['passable'][random.randrange(0, len(self._config['passable']))]]

    @property
    def wall(self):
        return self._sheet[self._config['wall'][random.randrange(0, len(self._config['wall']))]]

    @property
    def rand(self):
        return self._sheet[self._config['_all'][random.randrange(0, len(self._config['_all']))]]


class CreatureSheet(object):

    def __init__(self, name, config, zoom_levels):
        self._name = name
        self._config = config
        self._sheet = SpriteDict(['data', 'sprites', 'creatures', name], zoom_levels = zoom_levels)
        super(CreatureSheet, self).__init__()

    @property
    def static(self):
        return self._sheet[self._config['static'][0]]
