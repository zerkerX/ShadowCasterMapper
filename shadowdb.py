#!/usr/bin/python3
# Copyright 2012,2021 Ryan Armstrong
#
# This file is part of Shadow Caster Isometric Mapper.
#
# Shadow Caster Isometric Mapper is free software: you can redistribute
# it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Shadow Caster Isometric Mapper is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with Shadow Caster Isometric Mapper.
# If not, see <http://www.gnu.org/licenses/>.
#
# DroidSans.ttf is included with Shadow Caster Isometric Mapper under
# the terms of the Apache License, Version 2.0, which can be obtained at
#  http://www.apache.org/licenses/LICENSE-2.0

""" Module containing a variety of Shadow Caster wall, floor and sprite-type classes.
Also includes the wall/floor/sprite database class.
"""

import sys, pdb

from PIL import Image, ImageOps, ImageDraw, ImageFont

import shadowmap

class tile(object):
    """ Base tile class, which is expanded by all subsequent floor/wall
    tiles. This class has no meaning on its own, but it does define
    a number of common methods for handling height placement that are
    used by all tile subclasses.
    """

    def __init__(self, image):
        """ Initializes this tile by storing the provided tile image."""
        if image != None:
            self.image = image.convert("RGBA")
        else:
            self.image = None

    @staticmethod
    def leftskew(image):
        """ Skews the image to the left for isometric walls.
        For UP and DOWN (i.e. y axis) directions.
        """
        return image.transform((image.size[0],int(image.size[1]+image.size[0]/2)),
            Image.AFFINE, (1, 0, 0, -0.5, 1, 0), Image.BICUBIC)

    @staticmethod
    def rightskew(image):
        """ Skews the image to the right for isometric wals.
        For LEFT and RIGHT (i.e. x axis) directions.
        """
        return image.transform((image.size[0],int(image.size[1]+image.size[0]/2)),
            Image.AFFINE, (1, 0, 0, 0.5, 1, -image.size[0]/2), Image.BICUBIC)


class emptytile(tile):
    """ Empty tile subclass to mark a blank spot on the map."""
    pass

class walltile(tile):
    """ Standard wall tile type to mark a solid wall on the map."""
    def __init__(self, image):
        """ Initializes this wall with the specified wall image. """
        super(walltile, self).__init__(image)
        self.faces = {}
        self.masks = {}

    def prepare_size(self, spot, direction=None):
        """ Calculates several parameters related to the current wall
        to be drawn. Generates it if needed, then returns a tuple
        for the key index of this wall and the proper top position.

        The parameters are as follows:
        spot -- an instance of isomap.MapSpot that corresponds to the
                current tile being drawn.
        direction -- the orientation of the wall being generated, in
                     order to obtain the correct wall origin. If this
                     is not specified, the wall origin layer is not
                     checked, and this function assumes the wall
                     starts at the floor (i.e. for Door tiles)
        """
        if direction==None:
            wallorigin = spot.floordepth
        else:
            wallorigin = spot.wallorigins[direction]

        key = (wallorigin<<20)+(spot.ceildepth<<10)+spot.floordepth

        wallimgtop = wallorigin - self.image.size[1]
        walltop = max(wallimgtop, spot.ceildepth)


        if key not in self.faces:
            croptop = max(spot.ceildepth - wallimgtop, 0)
            cropimage = self.image.crop( (0, croptop, 64,
                spot.floordepth - wallimgtop) )
            self.generate_isometric(key, cropimage)

        return (key, walltop)


    def generate_isometric(self, key, fullimage):
        """ Generates isometric views for this tile at the specified
        map height. Creates skewed wall images facing in each direction,
        populating the faces and masks member variables.

        Parameters:
        key -- the key value corresponding to the current floor/ceiling
               varient of this wall.
        fullimage -- the image used as the isometric basis for this wall.
                     The image should already be cropped according to
                     the floor/ceiling heights.
        """

        self.faces[key] = [[None, None], [None, None]]
        self.masks[key] = [[None, None], [None, None]]

        # Darken the original image for the back walls (make 50% composite with black)
        backimage = ImageOps.mirror(Image.composite(fullimage,
            Image.new("RGBA", fullimage.size, (0,0,0)),
            Image.new("L", fullimage.size, (128))))

        # Make back walls 62.5% transparent
        backmask = Image.new("L", fullimage.size, (96))

        self.faces[key][shadowmap.WEST][0]  = self.rightskew(fullimage)
        self.faces[key][shadowmap.NORTH][0] = self.leftskew(fullimage)
        self.faces[key][shadowmap.WEST][1]  = self.rightskew(backimage)
        self.faces[key][shadowmap.NORTH][1] = self.leftskew(backimage)
        self.masks[key][shadowmap.WEST][0]  = self.rightskew(fullimage)
        self.masks[key][shadowmap.NORTH][0] = self.leftskew(fullimage)
        self.masks[key][shadowmap.WEST][1]  = self.rightskew(backmask)
        self.masks[key][shadowmap.NORTH][1] = self.leftskew(backmask)

    def draw(self, mapimage, pen, direction, spot):
        """ Draws this wall into the specified map location at the
        specified orientation. The parameters are as follows:

        mapimage -- the work-in-progress PIL Image object to draw onto
        pen -- a PIL ImageDraw instance for drawing additional markup
        direction -- the orientation of this wall
        spot -- an instance of isomap.MapSpot that corresponds to the
                current tile being drawn.
        """
        (key, walltop) = self.prepare_size(spot, direction)

        # Offsets are in the order as in direction enum (NORTH, WEST):
        walloffs = [(0,0), (-64,0)]
        lineoffs = [(0,0,63,31), (-64,31,0,0)] #x1,y1,x2,y2

        mapimage.paste(self.faces[key][direction][spot.solid],
            (spot.isox +walloffs[direction][0], spot.isoy +walloffs[direction][1] +walltop),
            self.masks[key][direction][spot.solid])
        pen.line([(spot.isox +lineoffs[direction][0],spot.isoy +lineoffs[direction][1] +walltop),
            (spot.isox +lineoffs[direction][2], spot.isoy +lineoffs[direction][3] +walltop)],
            fill=(192,192,192))



class thintile(walltile):
    """ Thin wall tile type to mark a door on the map,
    which is typically drawn in the middle of a given space.
    """

    def generate_isometric(self, key, fullimage):
        """ Generates isometric views for this tile at the specified
        map height. Creates skewed wall images facing in each direction,
        populating the faces and masks member variables.

        Parameters:
        key -- the key value corresponding to the current floor/ceiling
               varient of this wall.
        fullimage -- the image used as the isometric basis for this wall.
                     The image should already be cropped according to
                     the floor/ceiling heights.
        """
        self.faces[key] = [None]*2
        self.masks[key] = [None]*2

        self.faces[key][shadowmap.NORTH] = self.leftskew(fullimage)
        self.faces[key][shadowmap.WEST]  = self.rightskew(ImageOps.mirror(fullimage))
        self.masks[key][shadowmap.NORTH] = self.leftskew(fullimage)
        self.masks[key][shadowmap.WEST]  = self.rightskew(ImageOps.mirror(fullimage))

    def draw(self, mapimage, doorinfo, spot):
        """ Draws this door into the specified map location based on
        the door parameters. The parameters are as follows:

        mapimage -- the work-in-progress PIL Image object to draw onto
        doorinfo -- a Door instance describing the door to draw, including
                    the desired orientation.
        spot -- an instance of isomap.MapSpot that corresponds to the
                current tile being drawn.
        """
        (key, walltop) = self.prepare_size(spot)

        mapimage.paste(self.faces[key][doorinfo.orientation],
            (spot.isox-32, spot.isoy+16 +walltop),
            self.masks[key][doorinfo.orientation])

class floortile(tile):
    """ A floor tile """

    @staticmethod
    def floorskew(image):
        """ Skews an image to display on the floor """
        return image.transform((128,128), Image.AFFINE,
            (0.5, 0.5, -32, -0.5, 0.5, 32), Image.NEAREST).transform(
            (128,64), Image.AFFINE, (1, 0, 0, 0, 2, 0), Image.NEAREST)

    def __init__(self, image):
        """ Initializes this floor with the specified floor image. """
        super(floortile, self).__init__(image)
        self.floor = self.floorskew(self.image)

    def draw(self, mapimage, spot):
        """ Draws this floor into the specified map location. The
        parameters are as follows:

        mapimage -- the work-in-progress PIL Image object to draw onto
        spot -- an instance of isomap.MapSpot that corresponds to the
                current tile being drawn.
        """
        mapimage.paste(self.floor,
            (spot.isox-64, spot.isoy + spot.floordepth),
            self.floor)


class sprite(object):
    """ Sprite class. This is used by the various objects, items and
    monsters in the game.
    """
    def __init__(self, image, floatimage=None, height=0):
        """ Initializes the current sprite based on the provided data:

        image -- A PIL image for this sprite
        floatimage -- a PIL image that corresponds to a more visible
                    image that should be rendered at double-size over
                    the position of this item.
        height -- the height off the ground that this is drawn at.
        """
        self.image = image
        if floatimage != None:
            self.floatimage = self.double_scale(floatimage)
        else:
            self.floatimage = None
        self.height=height

    @staticmethod
    def double_scale(image):
        """ Simply doubles the size of the specified PIL Image"""
        return image.transform((image.size[0]*2,image.size[1]*2),
            Image.AFFINE, (0.5, 0, 0, 0, 0.5, 0), Image.NEAREST)

    def draw(self, mapimage, pen, objdata, spot):
        """ Draws this sprite into the specified map location. The
        parameters are as follows:

        mapimage -- the work-in-progress PIL Image object to draw onto
        pen -- a PIL ImageDraw instance for drawing additional markup
        objdata -- the Item, ShObject or Creature object describing
                   the sprite that is being drawn. Used to obtain
                   sub-tile positioning information.
        spot -- an instance of isomap.MapSpot that corresponds to the
                current tile being drawn.
        """
        subisox = objdata.subx-objdata.suby
        subisoy = (objdata.subx+objdata.suby)/2

        if self.floatimage != None:
            pen.line([(spot.isox-subisox,spot.isoy),
                (spot.isox-subisox,
                spot.isoy +spot.floordepth -self.height + subisoy -5)],
                fill=(240,240,240))
            pen.line([(spot.isox+1-subisox,spot.isoy),
                (spot.isox+1-subisox,
                spot.isoy +spot.floordepth -self.height + subisoy -5)],
                fill=(190,190,190))
            mapimage.paste(self.floatimage,
                (spot.isox-self.floatimage.size[0]/2-subisox,
                spot.isoy -self.floatimage.size[1]),
                self.floatimage)

        if self.height < 0:
            # Height < 0 means ceiling object:
            mapimage.paste(self.image,
                (spot.isox-self.image.size[0]/2-subisox,
                spot.isoy +spot.ceildepth + subisoy),
                self.image)

        else:
            # Do not allow enemies to float through the ceiling
            height = min(self.height, (spot.floordepth - spot.ceildepth) - self.image.size[1])

            mapimage.paste(self.image,
                (spot.isox-self.image.size[0]/2-subisox,
                spot.isoy +spot.floordepth -height + subisoy -self.image.size[1]),
                self.image)


# Global debug font.
debugfont = ImageFont.truetype("DroidSans.ttf", 24)

class db:
    """ Database of all known index to floor/wall/door/sprite mappings.

    Public member variables:
    walls -- a list of wall tiles, indexed by the wall id.
    floors -- a list of floor tiles, indexed by floor id.
    doors -- a dictionary of doors (thintiles), keyed by the door name
    objects -- a dictionary of objects (sprites), keyed by the sprite name
    items -- a dictionary of pickup items (sprites), keyed by the item id
    creatures -- a dictionary of creature definitions, keyed by the
                 creature id. This is dynamically re-loaded for each map,
                 as each map has its own set of definitions.
    """
    @staticmethod
    def debugimage(colour, text):
        """ Creates a 64x64 debug image for unknown walls/floors/items:

        colour -- the background colour for the image.
        text -- the text to display
        """
        tempimage = Image.new("RGBA", (64, 64), colour)
        pen = ImageDraw.Draw(tempimage)
        pen.text((16, 16), text, font=debugfont)
        return tempimage

    def __init__(self, cddat, hddat):
        """ Populates the various lists and dictionaries of mappings
        via the image data provided in the Shadow Caster DAT files.

        cddat -- cd_castr.dat data
        hddat -- hd_castr.dat data
        """
        self.walls = [None] * 256
        self.floors = [None] * 256
        self.doors = {}
        self.objects = {}
        self.items = [None] * 256

        # Cache dat files for later use:
        self.cddat = cddat
        self.hddat = hddat

        # Initialize with items:
        for i in range(256):
            self.items[i] = sprite(self.debugimage((95,96,255), str(i)),
                floatimage=self.debugimage((95,96,255), str(i)))

        self.loadwalls()
        self.loadfloors()
        self.loaddoors()
        self.loaditems()
        self.loadobjects()

        self.walls[0] = emptytile(None)
        self.floors[1] = emptytile(None)
        self.items[0] = emptytile(None)


    def loadwalls(self):
        """ Populates the list of valid wall tiles. """
        for index, lump in enumerate(self.cddat.idxdata['walls']):
            self.walls[index+1] = walltile(lump.data)

    def loadfloors(self):
        """ Populates the list of valid floor tiles. """
        for index, lump in enumerate(self.cddat.idxdata['flats']):
            self.floors[index+1] = floortile(lump.data)

    def loaddoors(self):
        """ Populates the dictionary of door tiles. """
        for group in list(self.cddat.data['walls'].keys()):
            if 'door' in group or \
                    group in ['wanim_eyes1', 'wanim_eyes2']:
                self.doors[group] = thintile(self.cddat.data['walls'][group][0].data)
                self.doors['door1'] = thintile(self.cddat.data['walls']['firstdoor'][0].data)

    def loadobjects(self):
        """ Populates the dictionary of objects. """
        for groupname, group in list(self.cddat.data['sprites'].items()):
            # Ideal index and height for most objects
            objectprefs = {'skelstatue' : (7, 0),
                'tipobelisk': (1, 0),
                'ceilingball': (0, -1),
                'ceilinghook': (0, -1),
                'chain': (0, -1),
                'chandelier': (0, -1),
                'chandelierdark': (0, -1)}
            offset = 0
            height = 0
            if groupname in objectprefs:
                (offset, height) = objectprefs[groupname]
            self.objects[groupname] = sprite(group[offset].data, height=height)
        # Manually add other "objects" (like dead monsters):
        # TODO: How is this used??
        self.objects['reddragondth'] = sprite(self.cddat.data['monsters']['reddragondth'][3].data)


    def loaditems(self):
        """ Populates the list of valid item definitions. """

        # These are manually determined. Although the pickup image matches
        # the item id, there doesn't appear to be any obvious correlation
        # for the floor image.
        self.items[1] = sprite(self.hddat.data['item']['5f'][0].data,
            floatimage=self.hddat.data['item']['1i'][0].data) # Ice Wand
        self.items[2] = sprite(self.hddat.data['item']['5f'][0].data,
            floatimage=self.hddat.data['item']['2i'][0].data) # Fire Wand
        self.items[4] = sprite(self.hddat.data['item']['51f'][0].data,
            floatimage=self.hddat.data['item']['4i'][0].data) # Fire Wand
        self.items[7] = sprite(self.hddat.data['item']['3f'][0].data,
            floatimage=self.hddat.data['item']['7i'][0].data) # Water Tablet
        self.items[13] = sprite(self.hddat.data['item']['4f'][0].data,
            floatimage=self.hddat.data['item']['13i'][0].data) # Silver Sword
        self.items[14] = sprite(self.hddat.data['item']['4f'][0].data,
            floatimage=self.hddat.data['item']['14i'][0].data) # Magical Sword
        self.items[15] = sprite(self.hddat.data['item']['24f'][0].data,
            floatimage=self.hddat.data['item']['15i'][0].data) # Trident of Might
        self.items[17] = sprite(self.hddat.data['item']['41f'][0].data,
            floatimage=self.hddat.data['item']['17i'][0].data) # Hourglass
        self.items[18] = sprite(self.hddat.data['item']['9f'][0].data,
            floatimage=self.hddat.data['item']['18i'][0].data) # Amulet of Defence
        self.items[21] = sprite(self.hddat.data['item']['49f'][0].data,
            floatimage=self.hddat.data['item']['21i'][0].data) # Tri-Wand
        self.items[22] = sprite(self.hddat.data['item']['49f'][0].data,
            floatimage=self.hddat.data['item']['22i'][0].data) # Frost Wand
        self.items[24] = sprite(self.hddat.data['item']['49f'][0].data,
            floatimage=self.hddat.data['item']['24i'][0].data) # Lightning Wand
        self.items[26] = sprite(self.hddat.data['item']['31f'][0].data,
            floatimage=self.hddat.data['item']['26i'][0].data) # Shurkien
        self.items[27] = sprite(self.hddat.data['item']['42f'][0].data,
            floatimage=self.hddat.data['item']['27i'][0].data) # Stone Head
        self.items[29] = sprite(self.hddat.data['item']['32f'][0].data,
            floatimage=self.hddat.data['item']['29i'][0].data, height=32) # Skull
        self.items[31] = sprite(self.hddat.data['item']['12f'][0].data,
            floatimage=self.hddat.data['item']['31i'][0].data) # Red Crystal
        self.items[32] = sprite(self.hddat.data['item']['13f'][0].data,
            floatimage=self.hddat.data['item']['32i'][0].data) # Blue Crystal
        self.items[33] = sprite(self.hddat.data['item']['14f'][0].data,
            floatimage=self.hddat.data['item']['33i'][0].data) # Green Crystal
        self.items[38] = sprite(self.hddat.data['item']['2f'][0].data,
            floatimage=self.hddat.data['item']['38i'][0].data) # Chalice of Power
        self.items[41] = sprite(self.hddat.data['item']['15f'][0].data,
            floatimage=self.hddat.data['item']['41i'][0].data) # Red Bomb
        self.items[42] = sprite(self.hddat.data['item']['16f'][0].data,
            floatimage=self.hddat.data['item']['42i'][0].data) # Blue Bomb
        self.items[43] = sprite(self.hddat.data['item']['17f'][0].data,
            floatimage=self.hddat.data['item']['43i'][0].data) # Green Bomb
        self.items[55] = sprite(self.hddat.data['item']['35f'][0].data,
            floatimage=self.hddat.data['item']['55i'][0].data) # Silver Armour
        self.items[39] = sprite(self.hddat.data['item']['11f'][0].data,
            floatimage=self.hddat.data['item']['39i'][0].data) # Key
        self.items[35] = sprite(self.hddat.data['item']['45f'][0].data,
            floatimage=self.hddat.data['item']['35i'][0].data) # Boulder
        self.items[40] = sprite(self.hddat.data['item']['26f'][0].data,
            floatimage=self.hddat.data['item']['40i'][0].data) # Flesh Crystal
        self.items[45] = sprite(self.hddat.data['item']['19f'][0].data,
            floatimage=self.hddat.data['item']['45i'][0].data) # Health Vial
        self.items[46] = sprite(self.hddat.data['item']['20f'][0].data,
            floatimage=self.hddat.data['item']['46i'][0].data) # Mana Vial
        self.items[50] = sprite(self.hddat.data['item']['27f'][0].data,
            floatimage=self.hddat.data['item']['50i'][0].data) # Bone Crystal
        self.items[52] = sprite(self.hddat.data['item']['1f'][0].data,
            floatimage=self.hddat.data['item']['52i'][0].data) # Royal Book (i.e. Credits)
        self.items[54] = sprite(self.hddat.data['item']['1f'][0].data,
            floatimage=self.hddat.data['item']['54i'][0].data) # Book of Leffar
        self.items[56] = sprite(self.hddat.data['item']['34f'][0].data,
            floatimage=self.hddat.data['item']['56i'][0].data) # Maorin Armour
        self.items[58] = sprite(self.hddat.data['item']['28f'][0].data,
            floatimage=self.hddat.data['item']['58i'][0].data) # Shock Horn
        self.items[59] = sprite(self.hddat.data['item']['29f'][0].data,
            floatimage=self.hddat.data['item']['59i'][0].data) # Horn of the Caun
        self.items[63] = sprite(self.hddat.data['item']['49f'][0].data,
            floatimage=self.hddat.data['item']['63i'][0].data) # Cane of Force
        self.items[64] = sprite(self.hddat.data['item']['46f'][0].data,
            floatimage=self.hddat.data['item']['64i'][0].data) # Obelisk Tip
        self.items[65] = sprite(self.hddat.data['item']['11f'][0].data,
            floatimage=self.hddat.data['item']['65i'][0].data) # Gate Key

    def loadcreatures(self, actors):
        """ Populates the list of valid creature definitions based on
        the actor list in a given level.
        """
        self.creatures = {}

        # Ideal orientation index for most monsters.
        monsterprefs = {'superjumpy': 7,
            'fish1': 2,
            'cleric': 5,
            'lobster1': 7,
            'gieser': 3,
            'flames': 0,
            'mushroomguy': 0,
            'ropeofice': 0,
            'chainofwoe': 0
             }

        for actor in actors:
            offset = 1
            if actor.sprite in monsterprefs:
                offset = monsterprefs[actor.sprite]
            self.creatures[actor.actorid] = sprite(self.cddat.data['monsters'][actor.sprite][offset].data,
                height = actor.height)
