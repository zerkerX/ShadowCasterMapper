#!/usr/bin/python
# Copyright 2012 Ryan Armstrong
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

""" Module for storing information needed to generate an isometric map"""

import sys, os, pdb
from operator import attrgetter

from PIL import Image, ImageOps, ImageDraw, ImageFont

import shadowlib, shadowmap, shadowdat, shadowdb, mapcatelog

class isomap(object):
    """ Class for generating an Isometric Map of a single Shadow Caster map."""
    def __init__(self, mapdata, database, catelogentry):
        """Initializes this map generator using the following information:

        mapdata -- an instance of the shadowmap.Map class which describes
                   the map to generate.
        database -- an instance of shadowdb.db that describes the
                    wall/floor/object/etc. definitions and images for
                    Shadow Caster.
        catelogentry -- an instance of mapcatelog.Mapentry that describes
                        supplementary display and markup information
                        when drawing this map.
        """
        self.maxceil = max(mapdata.maplump.layers[shadowmap.CEILINGHEIGHT])
        self.minfloor = min(mapdata.maplump.layers[shadowmap.FLOORHEIGHT])

        # Isomap primarily contains a list of MapSpot objects for each
        # location on the map, each of which contains enough information
        # to draw itself. Create the basic list with the information from
        # each layer at the corresponding position.
        self.data = [MapSpot(i, [layer[i] for layer in mapdata.maplump.layers],
            database, self.maxceil, catelogentry) for i in range(32*32)]

        # Populate the door, item, object, creature, markup  objects
        # at their corresponding locations when present.
        for index, door in mapdata.doorlump.data.items():
            self.data[index].adddoor(door, database)
        for index, items in mapdata.itemlump.data.items():
            self.data[index].additems(items, database)
        for index, shobjects in mapdata.objectlump.data.items():
            self.data[index].addobjects(shobjects, database)

        database.loadcreatures(mapdata.actorlump.data)
        for index, creature in mapdata.creaturelump.data.items():
            self.data[index].addcreature(creature, database)

        for index, markupitem in catelogentry.markup:
            self.data[index].addmarkup(markupitem)

        self.name = catelogentry.fullname
        self.number = catelogentry.mapnum
        self.bgcolour = catelogentry.bgcolour

    def generate(self):
        """ Internally generates an Isometric image of the current map."""
        self.mappicture = Image.new("RGB", (32*64*2, 32*64+self.maxceil-self.minfloor), self.bgcolour)
        self.pen = ImageDraw.Draw(self.mappicture)

        self.minx = self.mappicture.size[0]
        self.maxx = 0
        self.miny = self.mappicture.size[1]
        self.maxy = 0

        for spot in self.data:
            if spot.draw(self.mappicture, self.pen):
                # Update the map boundaries if the current tile needed to be drawn
                self.minx = min(self.minx, spot.isox-64)
                self.maxx = max(self.maxx, spot.isox+64)
                self.miny = min(self.miny, spot.isoy-64)
                self.maxy = max(self.maxy, spot.isoy+self.maxceil-self.minfloor+64)

    def save(self, outpath):
        """ Crops and saves the generated Isometric Map to disk at the
        specified path. The path should point to a directory, as the
        filename will be added by this function based on the map name.
        Must be run after generate.
        """
        self.minx=max(self.minx, 0)
        self.miny=max(self.miny, 0)

        self.mappicture.crop((self.minx, self.miny, self.maxx, self.maxy)).save(
            os.path.join(outpath, '{:02} - {}.png'.format(self.number, self.name)))


class MapSpot(object):
    """ An individual tile in a map. Contains everythign needed to draw
    this tile in an isometric map.
    """
    def __init__(self, index, layervals, database, maxceil, catelogentry):
        """Initializes this location on the map according to the
        provided information:

        index -- the linear index in the map that this location
                 corresponds to. This should be between 0 and 32*32, and
                 will be converted internally to x, y coordinates.
        layervals -- a 9-element list, where each element corresponds to
                     a single layer value at this spot in the map.
        database -- an instance of shadowdb.db that describes the
                    wall/floor/object/etc. definitions and images for
                    Shadow Caster.
        maxceil -- the maximum ceiling height found in the map.
        catelogentry -- an instance of mapcatelog.Mapentry that describes
                        supplementary display and markup information
                        when drawing this map.
        """
        layervals = catelogentry.applymods(layervals, index)

        self.floor = database.floors[layervals[shadowmap.FLOOR]]
        self.wall = [database.walls[layervals[shadowmap.NORTHWALL]],
            database.walls[layervals[shadowmap.WESTWALL]]]

        # Convert to depth for easier calculations
        self.floordepth = maxceil - layervals[shadowmap.FLOORHEIGHT]
        self.ceildepth = maxceil - layervals[shadowmap.CEILINGHEIGHT]
        self.wallorigins = [maxceil - layervals[shadowmap.NORTHWALLHEIGHT],
            maxceil - layervals[shadowmap.WESTWALLHEIGHT]]

        self.solid = (type(self.floor) is shadowdb.emptytile)

        self.index = index
        self.x = index % 32
        self.y = index / 32

        # Coordinates of the top point of the isometric tile in the output
        # Map is rotated clockwise for easier drawing
        self.isox = 32*64+(self.x-self.y)*64
        self.isoy = (self.x+self.y)*32

        # Placeholder members to be added later:
        self.door = None
        self.items = []
        self.itemdata = []
        self.creature = None
        self.objects = []
        self.objectdata = []
        self.markupdata = []

    def adddoor(self, door, database):
        """ Adds a given door instance to this location on the map.
        door -- an instance of shadowmap.Door describing this door.
        database -- an instance of shadowdb.db that describes the
                    wall/floor/object/etc. definitions and images for
                    Shadow Caster.
        """
        self.doordata = door
        self.door = database.doors[door.name]

    def additems(self, items, database):
        """ Adds a list of item instances to this location on the map.
        items -- a list of instances of shadowmap.Item for each item
                 that appears in this tile.
        database -- an instance of shadowdb.db that describes the
                    wall/floor/object/etc. definitions and images for
                    Shadow Caster.
        """
        for item in sorted(items, key=attrgetter('subx')):
            self.itemdata.append(item)
            self.items.append(database.items[item.itemtype])

    def addcreature(self, creature, database):
        """ Adds a given creature (monster) instance to this location
        on the map.
        creature -- an instance of shadowmap.Creature describing this
                    creature.
        database -- an instance of shadowdb.db that describes the
                    wall/floor/object/etc. definitions and images for
                    Shadow Caster.
        """
        self.creaturedata = creature
        self.creature = database.creatures[creature.crtype]

    def addobjects(self, shobjects, database):
        """ Adds a list of objects (static background sprite) instances
        to this location on the map.
        shobjects -- a list of instances of shadowmap.ShObject for each
                     object that appears in this tile.
        database -- an instance of shadowdb.db that describes the
                    wall/floor/object/etc. definitions and images for
                    Shadow Caster.
        """
        # TODO: This is limited. See if a better x + y sort is needed.
        for shobject in sorted(shobjects, key=attrgetter('subx')):
            self.objectdata.append(shobject)
            self.objects.append(database.objects[shobject.name])

    def addmarkup(self, markupitem):
        """ Adds the given markup entry to this location on the map.
        This will be manually drawn in this square after the rest
        of the level data.
        """
        self.markupdata.append(markupitem)

    def draw(self, mapimage, pen):
        """ Draws the data for this individual tile of the isometric
        map to the work-in-progress image using to the following:

        mapimage -- the work-in-progress PIL Image object to draw onto
        pen -- a PIL ImageDraw instance for drawing additional markup
        """
        drawn = False

        # Walls
        for direction in [shadowmap.NORTH, shadowmap.WEST]:
            if type(self.wall[direction]) is shadowdb.walltile:
                self.wall[direction].draw(mapimage, pen, direction, self)
                drawn = True

        # Floor
        if not self.solid:
            self.floor.draw(mapimage, self)
            drawn = True

        # Hide any objects outside the map:
        if not self.solid:
            # Door
            if self.door != None:
                self.door.draw(mapimage, self.doordata, self)
                drawn = True

            # Items
            for itm, itmdata in zip(self.items, self.itemdata):
                itm.draw(mapimage, pen, itmdata, self)

            # Objects
            for obj, objdata in zip(self.objects, self.objectdata):
                obj.draw(mapimage, pen, objdata, self)

            # Creatures
            if self.creature != None:
                self.creature.draw(mapimage, pen, self.creaturedata, self)

        # Manual markup
        for markupitem in self.markupdata:
            markupitem.draw(mapimage, pen, self)

        return drawn


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print """Usage: python isomap.py [LIB FILE] [cd_castr.dat] [hd_castr.dat]

Generates a isometric map for each level in the specified Shadow Caster
LIB file (typically shadow.lib). The DAT files are used for image data.
"""
    else:
        (libname, cddatname, hddatname) = sys.argv[1:4]

        lib = shadowlib.LibFile(libname)
        maps = shadowmap.MapSet(lib)
        cddat = shadowdat.DatFile(cddatname)
        hddat = shadowdat.DatFile(hddatname)

        cddat.loadall()
        hddat.loadall()
        database = shadowdb.db(cddat, hddat)
        catelog = mapcatelog.MapList(cddat, hddat)

        outpath = libname.replace('.', ' ') + ' OUT'
        if not os.path.exists(outpath):
            os.mkdir(outpath)

        for levelentry in catelog.maplist:
            print "Initializing Map '{}'".format(levelentry.fullname)
            mapper = isomap(maps.maps[levelentry.mapname], database, levelentry)
            print "Generating Map '{}'".format(levelentry.fullname)
            mapper.generate()
            print "Saving Map '{}'".format(levelentry.fullname)
            mapper.save(outpath)

        lib.close()
        cddat.close()
        hddat.close()
