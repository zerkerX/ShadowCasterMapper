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

""" Module for dealing with Shadow Caster maps as a combined set of lumps."""
import pdb
import struct, sys, os.path, csv

from PIL import Image

import shadowlib

# Directional constants. Ordered Counter-clockwise so that first
# two entries match how walls are drawn
(NORTH, WEST, SOUTH, EAST) = list(range(4))

# Layer Enum:
(FLOOR, FLOORHEIGHT, CEILING, CEILINGHEIGHT, NORTHWALL, NORTHWALLHEIGHT, WESTWALL,
    WESTWALLHEIGHT, UNKNOWN) = list(range(9))

class MapSet:
    """ A set of ShadowCaster map files.
    Public members variables:
    maps -- a dictionary of all maps present in this set,
            keyed by map name (sans extension)
    """

    def __init__(self, libfile):
        """ Loads map data for every map found in the specified lib."""
        self.maps = {}

        for filename, lump in list(libfile.db.items()):
            if filename.endswith('.map'):
                lump.__class__ = MapLump
                lump.load()
                mapdata = Map(lump)
                self.maps[mapdata.name] = mapdata

                # Add related lumps
                for (extension, classtype, membername) in [
                        ('.dor', DoorLump, 'doorlump'),
                        ('.itm', ItemLump, 'itemlump'),
                        ('.ojt', ObjectLump, 'objectlump'),
                        ('.crt', CreatureLump, 'creaturelump'),
                        ('.arc', ActorLump, 'actorlump') ]:
                    if mapdata.name + extension in libfile.db:
                        templump = libfile.db[mapdata.name + extension]
                        templump.__class__ = classtype
                        templump.load()
                        mapdata.__dict__[membername] = templump


    @staticmethod
    def createpath(pathname):
        """ Simple utility method for creating a path only if it does
        not already exist.
        """
        if not os.path.exists(pathname):
            os.mkdir(pathname)

    def dumpcontents(self, outpath):
        """ Debug method for creating debug image and csv files for every
        map in this map set.
        """
        self.createpath(outpath)

        for shmap in list(self.maps.values()):
            shmap.debugpics(outpath)

class Map(object):
    """ Class for collecting all data relevant to a given level.

    Public member variables:
    name -- map name (sans extension)
    maplump -- the lump representing the raw map data
    doorlump -- the lump representing the door data
    itemlump -- the lump representing the item (pickup) data
    objectlump -- the lump representing the object (static sprite) data
    creaturelump -- the lump representing the creature (monster placement) data
    actorlump -- the lump representing the actor (monster definition) data
    """

    @staticmethod
    def mapindex(x, y):
        """ Calculates the linear map index for a given x, y coordinate."""
        return y*32 + x

    def __init__(self, maplump):
        """ Initializes the map. Stores the individual lumps for now."""
        self.maplump = maplump
        self.name = maplump.name.replace('.map', '')

        # Placeholders for other lump types:
        self.doorlump = None
        self.itemlump = None
        self.objectlump = None
        self.creaturelump = None
        self.actorlump = None

    def debugpics(self, outpath):
        """ Generates debug pictures for each layer in the map."""
        for layernum, layer in enumerate(self.maplump.layers):
            mappicture = Image.new("L", (32, 32))
            mappicture.putdata(layer)
            mappicture.save(os.path.join(outpath, "{}-{}.png".format(self.name, layernum)))

        self.doorlump.dumpcsv(os.path.join(outpath, "{}-doors.csv".format(self.name)))
        self.itemlump.dumpcsv(os.path.join(outpath, "{}-items.csv".format(self.name)))
        self.objectlump.dumpcsv(os.path.join(outpath, "{}-objects.csv".format(self.name)))
        self.creaturelump.dumpcsv(os.path.join(outpath, "{}-creatures.csv".format(self.name)))
        self.actorlump.dumpcsv(os.path.join(outpath, "{}-actors.csv".format(self.name)))

class MapLump(shadowlib.Lump):
    """ Class representing a lump of map data.

    Public member variables:
    layers -- a 2D array of all the raw map data. The first index is the
              map layer (see enumeration at the top of this file). The
              second index is the map index into that layer.
    """
    def load(self):
        """ Loads this lump as map data. """
        self.filedata.seek(self.pos, 0)

        self.layers = []

        self.layers.append(struct.unpack('<1024H', self.filedata.read(0x800))) #0x000
        self.layers.append(struct.unpack('<1024B', self.filedata.read(0x400))) #0x800
        self.layers.append(struct.unpack('<1024H', self.filedata.read(0x800))) #0xC00
        self.layers.append(struct.unpack('<1024B', self.filedata.read(0x400))) #0x1400
        self.layers.append(struct.unpack('<1024H', self.filedata.read(0x800))) #0x1800
        self.layers.append(struct.unpack('<1024B', self.filedata.read(0x400))) #0x2000
        self.layers.append(struct.unpack('<1024H', self.filedata.read(0x800))) #0x2400
        self.layers.append(struct.unpack('<1024B', self.filedata.read(0x400))) #0x2C00
        self.layers.append(struct.unpack('<1024B', self.filedata.read(0x400))) #0x3000

class DoorLump(shadowlib.Lump):
    """ Class representing a lump of door data.

    Public member variables:
    rawdata -- unidentified list of each record in the file. First index
               is the file record, second index is the field inside the
               record.
    data -- Dictionary of Door objects, one for each record in the
            lump. Keyed by the map index where the Door appears.
    """
    # Door record format
    doordata = '<lllB20slbbblll'

    def load(self):
        """ Loads this lump as door data. """
        self.filedata.seek(self.pos, 0)
        self.rawdata = []
        self.data = {}

        for doornum in range(self.size / struct.calcsize(self.doordata)):
            tempdata = list(struct.unpack(self.doordata,
                self.filedata.read(struct.calcsize(self.doordata))))
            # Remove string content after the null character
            for index, char in enumerate(tempdata[4]):
                if ord(char) == 0:
                    tempdata[4] = tempdata[4][:index].lower()
                    break
            tempdoor = Door(tempdata)
            self.rawdata.append(tempdata)
            self.data[Map.mapindex(tempdoor.x, tempdoor.y)] = tempdoor

    def dumpcsv(self, filename):
        """ Debug method to write the raw door data to a CSV file. """
        with open(filename, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            for datarow in self.rawdata:
                writer.writerow(datarow)

class Door(object):
    """ Class representing a decoded Door record.

    Public member variables:
    orientation -- The directional facing of this Door (East-West or North-South)
    name -- the name for the corresponding Door image
    x, y -- the coordinates where this Door is located
    uniqid, doortype, locked -- provisional field decoding that may or may
                                not be correct. Not currently used.
    """
    def __init__(self, lumpdata):
        self.uniqid = lumpdata[0]
        orientation = lumpdata[3]
        self.name = lumpdata[4]
        self.doortype = lumpdata[5]
        self.locked = lumpdata[7] # TBC
        self.x = lumpdata[9]
        self.y = lumpdata[10]

        if orientation == 0:
            self.orientation = WEST
        else:
            self.orientation = NORTH

class ItemLump(DoorLump):
    """ Class representing a lump of item (pickup) data.

    Public member variables:
    rawdata -- unidentified list of each record in the file. First index
               is the file record, second index is the field inside the
               record.
    data -- Dictionary of lists of Item objects. Keyed by the map index
            where the Item appears. Each entry can contain one or more
            items at the specified location
    """
    # Item record format:
    itemdata = '<9lhl'

    def load(self):
        """ Loads this lump as item data. """
        self.filedata.seek(self.pos, 0)
        self.rawdata = []
        self.data = {}

        for itemnum in range(self.size / struct.calcsize(self.itemdata)):
            tempdata = list(struct.unpack(self.itemdata,
                self.filedata.read(struct.calcsize(self.itemdata))))
            tempitem = Item(tempdata)
            self.rawdata.append(tempdata)
            index = Map.mapindex(tempitem.x, tempitem.y)
            if index not in list(self.data.keys()):
                self.data[index] = []
            self.data[index].append(tempitem)


class Item(object):
    """ Class representing a decoded Item (pickup) record.

    Public member variables:
    itemtype -- the ID of this item
    x, y -- the coordinates where this item is located
    subx, suby -- the coordinates within the tile to place this item.
                  Range is 0 to 63
    uniqid -- provisional field decoding that may or may not be correct.
              Not currently used.
    """
    def __init__(self, lumpdata):
        self.uniqid = lumpdata[0]
        self.x = lumpdata[3]
        self.y = lumpdata[4]
        self.itemtype = lumpdata[6]
        self.subx = lumpdata[9]
        self.suby = lumpdata[9]

class ObjectLump(DoorLump):
    """ Class representing a lump of object (static sprite) data.

    Public member variables:
    rawdata -- unidentified list of each record in the file. First index
               is the file record, second index is the field inside the
               record.
    data -- Dictionary of lists of ShObject objects. Keyed by the map index
            where the object appears. Each entry can contain one or more
            object at the specified location
    """
    # Object record format
    objectdata = '<3lh20s2h3l3B2h'

    def load(self):
        """ Loads this lump as object data. """
        self.filedata.seek(self.pos, 0)
        self.rawdata = []
        self.data = {}

        for objectnum in range(self.size / struct.calcsize(self.objectdata)):
            tempdata = list(struct.unpack(self.objectdata,
                self.filedata.read(struct.calcsize(self.objectdata))))
            # Remove string content after the null character
            for index, char in enumerate(tempdata[4]):
                if ord(char) == 0:
                    tempdata[4] = tempdata[4][:index].lower()
                    break
            tempobject = ShObject(tempdata)
            self.rawdata.append(tempdata)
            index = Map.mapindex(tempobject.x, tempobject.y)
            if index not in list(self.data.keys()):
                self.data[index] = []
            self.data[index].append(tempobject)

class ShObject(object):
    """ Class representing a decoded object (static sprite) record.

    Public member variables:
    name -- the name for this object
    x, y -- the coordinates where this object is located
    subx, suby -- the coordinates within the tile to place this object.
                  Range is 0 to 63
    uniqid, objecttype -- provisional field decoding that may or may not be correct.
                          Not currently used.
    """
    def __init__(self, lumpdata):
        self.uniqid = lumpdata[0]
        self.name = lumpdata[4]
        self.objecttype = lumpdata[5]
        self.x = lumpdata[10]
        self.y = lumpdata[11]
        self.subx = lumpdata[13]
        self.suby = lumpdata[14]

class CreatureLump(DoorLump):
    """ Class representing a lump of Creature (monster instance) data.

    Public member variables:
    rawdata -- unidentified list of each record in the file. First index
               is the file record, second index is the field inside the
               record.
    data -- Dictionary of Creature objects, one for each record in the
            lump. Keyed by the map index where the Creature appears.
    """

    # Creature record structure. Contains a lot of information; only a fraction is decoded
    creaturedata = '<11l6lB2l2hl11l11llhB5lh'

    def load(self):
        """ Loads this lump as creature data. """
        self.filedata.seek(self.pos, 0)
        self.rawdata = []
        self.data = {}

        for creaturenum in range(self.size / struct.calcsize(self.creaturedata)):
            tempdata = list(struct.unpack(self.creaturedata,
                self.filedata.read(struct.calcsize(self.creaturedata))))
            tempcreature = Creature(tempdata)
            self.rawdata.append(tempdata)
            self.data[Map.mapindex(tempcreature.x, tempcreature.y)] = tempcreature

class Creature(object):
    """ Class representing a decoded Creature (monster instance) record.

    Public member variables:
    crtype -- the ID of this Creature
    x, y -- the coordinates where this Creature is located
    subx, suby -- the coordinates within the tile to place this item.
                  Range is 0 to 63. For compatibility only; this is not present
                  in the original record and is hardcoded to 32.
    """
    def __init__(self, lumpdata):
        self.x = lumpdata[20]
        self.y = lumpdata[21]
        self.crtype = lumpdata[3]
        self.subx = 32
        self.suby = 32

class ActorLump(DoorLump):
    """ Class representing a lump of Actor (monster definition) data.

    Public member variables:
    rawdata -- unidentified list of each record in the file. First index
               is the file record, second index is the field inside the
               record.
    data -- List of Actor objects, one for each record in the
            lump.
    """

    # Record for actor data. Only a very small portion is used.
    actordata = '<4l20s20s7l4B2lB104l4B3l4B24l11B112l3B'

    def load(self):
        """ Loads this lump as actor data. """
        self.filedata.seek(self.pos, 0)
        self.rawdata = []
        self.data = []

        for actornum in range(self.size / struct.calcsize(self.actordata)):
            tempdata = list(struct.unpack(self.actordata,
                self.filedata.read(struct.calcsize(self.actordata))))

            # Remove the contents of the string after the null character
            # for names and sprite names.
            for index, char in enumerate(tempdata[4]):
                if ord(char) == 0:
                    tempdata[4] = tempdata[4][:index].lower()
                    break
            for index, char in enumerate(tempdata[5]):
                if ord(char) == 0:
                    tempdata[5] = tempdata[5][:index].lower()
                    break
            tempactor = Actor(tempdata)
            self.rawdata.append(tempdata)
            self.data.append(tempactor)


class Actor(object):
    """ Class representing a decoded Actor (monster definition) record.

    Public member variables:
    actorid -- the ID of this Actor (refered to by Creature objects)
    name -- the name for this actor (not used)
    sprite -- the sprite name for this actor
    height -- the height above the floor for this actor. -1 represents
              ceiling placement.
    """
    def __init__(self, lumpdata):
        self.actorid = lumpdata[0]
        self.name = lumpdata[4]
        self.sprite = lumpdata[5]
        heightdata = lumpdata[13]

        # May be a set of flags? Go by known values for now
        if heightdata == 8:
            # Floating
            self.height = 64
        elif heightdata == 17:
            # Ceiling
            self.height = -1
        else:
            self.height = 0

# Debug main method for printing out raw map data visualization
if __name__ == "__main__":
    for filename in sys.argv[1:]:
        if filename.endswith(".lib"):
            lib = shadowlib.LibFile(filename)

            outdir = filename + "_maps"
            maps = MapSet(lib)
            maps.dumpcontents(outdir)

            lib.close()

