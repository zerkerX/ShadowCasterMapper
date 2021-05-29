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
""" Module containing a catelog of all maps to export, with additional optional
markup and modifications.
"""
import pdb
import shadowmap
from shadowmap import Map
from PIL import Image, ImageOps, ImageDraw, ImageFont

markupfont = ImageFont.truetype("DroidSans.ttf", 14)

class markuptext(object):
    """ Class for providing general text markup."""

    def __init__(self, text, textpos, linestart = None, lineheight = 0):
        """ Initializes using the following information:

        text -- the text string to use for markup
        textpos -- the x,y coordiantes (relative to the isometric
                   tile origin) where the top-left corner of the text
                   label starts from.

        Optional named parameters:
        linestart -- the x,y coordinates (relative to the isometric
                     tile origin) where the top of the line starts from.
        lineheight -- the height in pixels above the tile's floor height
                      to stop drawing the line.
        """
        self.text = text
        self.textpos = textpos
        self.linestart = linestart
        self.lineheight = lineheight

    def draw(self, mapimage, pen, spot):
        """ Draws this text label into the specified map location
        with optional indicator line. The parameters are as follows:

        mapimage -- the work-in-progress PIL Image object to draw onto
        pen -- a PIL ImageDraw instance for drawing additional markup
        spot -- an instance of isomap.MapSpot that corresponds to the
                current tile being drawn.
        """
        if self.linestart != None:
            pen.line([(spot.isox +self.linestart[0],
                spot.isoy +self.linestart[1]),
                (spot.isox +self.linestart[0],
                spot.isoy +spot.floordepth -self.lineheight +32)],
                fill=(240,240,240))
            pen.line([(spot.isox+self.linestart[0] +1,
                spot.isoy+self.linestart[1]),
                (spot.isox +self.linestart[0] +1,
                spot.isoy +spot.floordepth -self.lineheight +32)],
                fill=(190,190,190))

        # Draw the text 5 times to create an outline
        # (4 x black then 1 x white)
        for offset, colour in [( (-1,-1), (0,0,0) ),
                ( (-1,1), (0,0,0) ),
                ( (1,-1), (0,0,0) ),
                ( (1,1), (0,0,0) ),
                ( (0,0), (255,255,255) )]:
            pen.text((spot.isox + self.textpos[0] + offset[0],
                spot.isoy + self.textpos[1] + offset[1]),
                self.text, font=markupfont, fill=colour)

class markupimage(object):
    """ Class for providing an image markup."""

    def __init__(self, image, pos, linestart = None, lineheight = 0, scale=1):
        """ Initializes using the following information:

        image -- the PIL Image to use for markup
        pos -- the x,y coordiantes (relative to the isometric
               tile origin) where the top-middle position of the
               image starts from.

        Optional named parameters:
        linestart -- the x,y coordinates (relative to the isometric
                     tile origin) where the top of the line starts from.
        lineheight -- the height in pixels above the tile's floor height
                      to stop drawing the line.

        """
        if scale != 1:
            self.image = image.transform((image.size[0]*scale,image.size[1]*scale),
                Image.AFFINE, (1.0/scale, 0, 0, 0, 1.0/scale, 0), Image.NEAREST)
        else:
            self.image = image
        self.pos = pos
        self.linestart = linestart
        self.lineheight = lineheight

    def draw(self, mapimage, pen, spot):
        """ Draws this image into the specified map location
        with optional indicator line. The parameters are as follows:

        mapimage -- the work-in-progress PIL Image object to draw onto
        pen -- a PIL ImageDraw instance for drawing additional markup
        spot -- an instance of isomap.MapSpot that corresponds to the
                current tile being drawn.
        """
        if self.linestart != None:
            pen.line([(spot.isox +self.linestart[0],
                spot.isoy +self.linestart[1]),
                (spot.isox +self.linestart[0],
                spot.isoy +spot.floordepth -self.lineheight +32)],
                fill=(240,240,240))
            pen.line([(spot.isox +self.linestart[0] +1,
                spot.isoy +self.linestart[1]),
                (spot.isox +self.linestart[0] +1,
                spot.isoy +spot.floordepth -self.lineheight +32)],
                fill=(190,190,190))

        mapimage.paste(self.image,
            (spot.isox -self.image.size[0]/2 +self.pos[0],
            spot.isoy +self.pos[1]),
            self.image)

class Mapentry:
    """ Class for cataloging all markup, changes and supplementary
    (i.e. manually determined) information for a given Shadow Caster map.
    """
    def __init__(self, mapname, mapnum, suffix = '', bgcolour = (32, 32, 32),
            markup = [], changes = None, replacements = None):
        """ Initializes this map entry according to the following parameters:
        mapname -- The base name of this map (sans extension)
        mapnum -- the number of this map according to the ingame automap

        Optional named parameters:
        suffix -- A suffix to add to the end of the map name when generating.
                  Used for varients of a map.
        bgcolour -- the background colour for this map.
        markup -- a list of markuptext and markupimage objects to be
                  drawn for this map.
        changes -- a 9-element list of dictionaries defining explicit
                   manual changes to this map, each corresponding to a
                   map layer. The dictionary is keyed by the map index
                   to modify, with the value being the new layer value
                   in that location.
        replacements -- a 9-element list of dictionaries defining
                   manual layer value replacements to this map, each
                   corresponding to a map layer. The dictionary is
                   keyed by the original layer value to search for,
                   with the value being the new layer value to replace
                   with.
        """
        self.mapname = mapname
        self.fullname = mapname + suffix
        self.mapnum = mapnum
        self.bgcolour = bgcolour
        self.markup = markup
        self.changes = changes
        self.replacements = replacements

    def applymods(self, layervals, index):
        """ Applies the changes and replacements lists to this location
        in the map. Checks if either list contains a match, and modifies
        this location if it does. If not, the location is unmodified.
        Returns the modified (or unmodified) copy of the input
        layervals list.

        Parameters:
        layervals -- a 9-element list of each layer value at the current
                     location in the map.
        index -- the index in the map that is being modified.
        """
        outlayers = list(layervals)
        for layernum, layerval in enumerate(layervals):
            if self.changes != None and index in self.changes[layernum]:
                outlayers[layernum] = self.changes[layernum][index]
            if self.replacements != None and layerval in self.replacements[layernum]:
                outlayers[layernum] = self.replacements[layernum][layerval]
        return outlayers


class MapList:
    """ Contains a list of MapEntry objects for all known maps. Dictates
    which maps are generated by isomap.py.

    Public member variables:
    maplist -- the list of MapEntry objects
    """

    @staticmethod
    def erase(modlist, index):
        """ Utility method for erasing a region in an in-process mod list """
        modlist[shadowmap.FLOOR][index] = 1
        modlist[shadowmap.NORTHWALL][index] = 0
        modlist[shadowmap.WESTWALL][index] = 0

    def __init__(self, cddat, hddat):
        """ Initializes the MapList according to the manually determined
        list of maps and markup using the following parameters:

        cddat -- a shadowdat.DatFile instance corresponding to 'cd_castr.dat'
        hddat -- a shadowdat.DatFile instance corresponding to 'hd_castr.dat'
        """

        # Some notes:
        # Text rough sizing: 20 pixels per row, 6 pixels per character
        # Images are based on the morphing animations, since those are
        # not RLE encoded. Some have black in them, so them need to be
        # converted back to RGB to undo the masking.
        self.maplist = []


        self.maplist.append(Mapentry('ruinsa', 1,
            markup = [
            (Map.mapindex(1,6), markuptext('Start', (-15, 0), (0, 40)) ),
            (Map.mapindex(1,6), markupimage(hddat.data['General']['catfacemorph'][0].data, (0, 20)) ),
            (Map.mapindex(3,2), markuptext('Maorin Form', (-40, 0)) ),
            (Map.mapindex(3,2), markupimage(hddat.data['General']['catfacemorph'][29].data, (0, 20)) ),
            (Map.mapindex(7,1), markuptext('to A', (-8, 0), (0, 20)) ),
            (Map.mapindex(1,9), markuptext('A', (-3, 0), (0, 20)) ),
            (Map.mapindex(0,18), markuptext('Exit to Level 4', (-40, 0), (0, 40)) ),
            (Map.mapindex(0,18), markuptext('(RuinsB)', (-20, 20)) ),
            (Map.mapindex(13,26), markuptext('Place Silver Triangle Key', (-50, 0)) ),
            (Map.mapindex(13,26), markuptext('for Exit to Level 2', (-40, 20)) ),
            (Map.mapindex(13,26), markuptext('(RuinAdrn)', (-20, 40)) ),
            (Map.mapindex(14,27), markupimage(hddat.data['item']['19i'][0].data, (0, 20), (0, 30), 96, scale=2) )] ))


        # Prepare the RuinADRN/WAT modifications.
        # All modifications are 9 item lists of dictionaries, one for each layer
        ruinadrn_wet_mods = [{}, {}, {}, {}, {}, {}, {} ,{}, {}]
        ruinadrn_dry_mods = [{}, {}, {}, {}, {}, {}, {} ,{}, {}]
        ruinawat_mods = [{}, {}, {}, {}, {}, {}, {} ,{}, {}]

        # Erase the inaccessible extra squares from the map
        for index in range(512, 32*32):
            self.erase(ruinadrn_wet_mods, index)
            self.erase(ruinadrn_dry_mods, index)
            self.erase(ruinawat_mods, index)

        # Erase the inaccessible areas when the map is still wet:
        for x in range(16, 29):
            for y in range(4, 12):
                self.erase(ruinadrn_wet_mods, Map.mapindex(x, y))

        for x in range(9, 23):
            for y in range(10, 16):
                self.erase(ruinadrn_wet_mods, Map.mapindex(x, y))

        ruinadrn_wet_mods[shadowmap.WESTWALL][115] = 0
        ruinadrn_wet_mods[shadowmap.FLOOR][115] = 1
        ruinadrn_wet_mods[shadowmap.WESTWALL][116] = 0

        # Open up the walls that change when the water drains
        ruinadrn_dry_mods[shadowmap.NORTHWALL][410] = 0
        ruinadrn_dry_mods[shadowmap.NORTHWALL][115] = 0

        self.maplist.append(Mapentry('ruinadrn', 2, suffix='_full',
            markup = [
            (Map.mapindex(12,8), markuptext('Start', (-15, 0), (0, 20)) )],
            #(Map.mapindex(30,1), markuptext('Pull Chain to Drain water', (-72, 0)) ),
            changes = ruinadrn_wet_mods ))

        self.maplist.append(Mapentry('ruinadrn', 2, suffix='_drained',
            markup = [
            #(Map.mapindex(25,4), markuptext('Place Skull to Continue', (-66, 0)) ),
            (Map.mapindex(21,14), markuptext('Exit to Level 1', (-40, 0), (0, 40)) ),
            (Map.mapindex(21,14), markuptext('(RuinsA)', (-20, 20)) )],
            changes = ruinadrn_dry_mods,
            replacements = [{15: 14, 16: 14, 17: 14}, {172: 52}, {}, {},
            {}, {}, {} ,{}, {}] ))

        self.maplist.append(Mapentry('ruinawat', 3, bgcolour = (0, 0, 48),
            changes = ruinawat_mods))


        self.maplist.append(Mapentry('ruinsb', 4, bgcolour = (96, 96, 96),
            markup = [
            (Map.mapindex(29,18), markuptext('Start', (-15, 0), (0, 20)) ),
            (Map.mapindex(30,18), markuptext('Exit to Level 1', (-40, 0), (0, 40)) ),
            (Map.mapindex(30,18), markuptext('(RuinsA)', (-20, 20)) ),
            (Map.mapindex(25,4), markuptext('Place Stone Heads', (-48, -40)) ),
            (Map.mapindex(25,4), markuptext('for Exit to Level 6', (-44, -20)) ),
            (Map.mapindex(25,4), markuptext('(RuinBtem)', (-20, 0)) ),
            (Map.mapindex(15,28), markupimage(hddat.data['item']['25i'][0].data, (0, 20), (0, 35), 32, scale=2) )] ))

        self.maplist.append(Mapentry('ruinbwat', 5, bgcolour = (0, 0, 48) ))


        # Erase the inaccessible extra squares in the lower-left corner
        # of several levels
        cornermods = [{}, {}, {}, {}, {}, {}, {} ,{}, {}]
        for index in range(992, 1020):
            self.erase(cornermods, index)

        self.maplist.append(Mapentry('ruinbtem', 6,
            markup = [
            (Map.mapindex(15,25), markuptext('Start', (-15, 0), (0, 20)) ),
            (Map.mapindex(6,25), markupimage(hddat.data['item']['44i'][0].data, (-15, 20), (-15, 40), 32, scale=2) ),
            (Map.mapindex(6,25), markupimage(hddat.data['item']['46i'][0].data, (15, 20), (15, 40), 32, scale=2) ),
            (Map.mapindex(11,9), markupimage(hddat.data['item']['34i'][0].data, (0, 20), (0, 35), 32, scale=2) ),
            (Map.mapindex(15,5), markuptext('Caun Form', (-46, -17)) ),
            (Map.mapindex(15,5), markupimage(hddat.data['General']['pixiefacemorph'][29].data, (-13, 3)) ),
            (Map.mapindex(15,2), markuptext('Exit to Level 7', (-40, 0)) ),
            (Map.mapindex(15,2), markuptext('(Temple)', (-20, 20)) )],
            changes = cornermods))


        self.maplist.append(Mapentry('temple', 7,
            markup = [
            (Map.mapindex(16,29), markuptext('Start', (-15, 0), (0, 20)) ),
            (Map.mapindex(21,4), markuptext('Start (Second visit)', (-60, 0), (0, 20)) ),
            (Map.mapindex(21,29), markuptext('Start (Third visit)', (-55, 0), (0, 20)) ),
            (Map.mapindex(11,6), markuptext('Start (Fourth visit)', (-55, 0), (0, 20)) ),
            (Map.mapindex(2,26), markuptext('Start (Fifth visit)', (-55, 0), (0, 20)) ),
            (Map.mapindex(13,3), markuptext('Exit to Level 11', (-37, -25)) ),
            (Map.mapindex(13,3), markuptext('(CastWine)', (-20, -5)), ),
            (Map.mapindex(13,3), markuptext('(Opens on first visit)', (-55, 15)), ),
            (Map.mapindex(13,5), markuptext('Exit to Level 14', (-37, -25)) ),
            (Map.mapindex(13,5), markuptext('(UndrMine)', (-20, -5)), ),
            (Map.mapindex(13,5), markuptext('(Opens on second visit)', (-60, 15)), ),
            (Map.mapindex(19,3), markuptext('Exit to Level 16', (-37, -25)) ),
            (Map.mapindex(19,3), markuptext('(WaterAci)', (-20, -5)), ),
            (Map.mapindex(19,3), markuptext('(Opens on third visit)', (-55, 15)), ),
            (Map.mapindex(19,5), markuptext('Exit to Level 20', (-37, -25)) ),
            (Map.mapindex(19,5), markuptext('(LavaMud)', (-20, -5)), ),
            (Map.mapindex(19,5), markuptext('(Opens on fourth visit)', (-55, 15)), ),
            (Map.mapindex(16,4), markuptext('Exit to Level 22', (-40, -25), (0, 35)) ),
            (Map.mapindex(16,4), markuptext('(VesteTst)', (-28, -5)), ),
            (Map.mapindex(16,4), markuptext('(Opens on fifth visit)', (-55, 15)), )] ))


        self.maplist.append(Mapentry('castwine', 11,
            markup = [
            (Map.mapindex(25,8), markuptext('Start', (-15, 0), (0, 20)) ),
            (Map.mapindex(15,13), markuptext('Exit to Level 13', (-37, 0)) ),
            (Map.mapindex(15,13), markuptext('(CastMoon)', (-20, 20)) ),
            (Map.mapindex(25,13), markuptext('Exit to Level 12', (-37, 0)) ),
            (Map.mapindex(25,13), markuptext('(CastThrn)', (-20, 20)) )],
            changes = cornermods ))


        self.maplist.append(Mapentry('castthrn', 12,
            markup = [
            (Map.mapindex(30,5), markuptext('Start', (-15, 20), (0, 40)) ),
            (Map.mapindex(15,21), markuptext('A: to B', (-15, 20), (0, 40)) ),
            (Map.mapindex(15,23), markuptext('B: to A', (-15, 80), (0, 100)) ),
            (Map.mapindex(3,7), markuptext('Exit to Level 13', (-37, 0)) ),
            (Map.mapindex(3,7), markuptext('(CastMoon)', (-20, 20)) ),
            (Map.mapindex(29,5), markuptext('Exit to Level 11', (-37, 0)) ),
            (Map.mapindex(29,5), markuptext('(CastWine)', (-20, 20)) )],
            changes = cornermods ))


        self.maplist.append(Mapentry('castmoon', 13,
            markup = [
            (Map.mapindex(2,3), markuptext('Start', (-15, 20), (0, 40)) ),
            (Map.mapindex(1,3), markuptext('Exit to Level 11', (-37, 0)) ),
            (Map.mapindex(1,3), markuptext('(CastWine)', (-20, 20)) ),
            (Map.mapindex(28,30), markuptext('Start', (-15, 20), (0, 40)) ),
            (Map.mapindex(28,29), markuptext('Exit to Level 12', (-37, 0)) ),
            (Map.mapindex(28,29), markuptext('(CastThrn)', (-20, 20)) ),
            (Map.mapindex(16,14), markuptext('Exit to Level 7', (-40, 0), (0, 40)) ),
            (Map.mapindex(16,14), markuptext('(Temple)', (-20, 20)) ),
            (Map.mapindex(13,20), markuptext('Opsis Form', (-38, -5)) ),
            (Map.mapindex(13,20), markupimage(hddat.data['General']['eyefacemorph'][29].data, (-1, 15)) ),
            (Map.mapindex(13,2), markupimage(hddat.data['item']['51i'][0].data, (0, 20), (0, 35), 32, scale=2) ),
            (Map.mapindex(16,21), markupimage(hddat.data['item']['64i'][0].data, (-15, 0), (-15, 15), 72, scale=2) ),
            (Map.mapindex(16,21), markupimage(hddat.data['item']['10i'][0].data, (15, 0), (15, 15), 72, scale=2) ),
            (Map.mapindex(10,28), markupimage(hddat.data['item']['9i'][0].data, (-15, 0), (-15, 15), 32, scale=2) ),
            (Map.mapindex(10,28), markupimage(hddat.data['item']['3i'][0].data, (15, 0), (15, 15), 32, scale=2) )] ))


        # Erase the inaccessible extra squares from the map
        uppercornermods = [{}, {}, {}, {}, {}, {}, {} ,{}, {}]
        for y in range(0, 4):
            self.erase(uppercornermods, Map.mapindex(0,y))

        self.maplist.append(Mapentry('undrmine', 14,
            markup = [
            (Map.mapindex(27,30), markuptext('Start', (-15, 0), (0, 20)) ),
            (Map.mapindex(28,8), markupimage(hddat.data['item']['18i'][0].data, (0, 20), (0, 35), 72, scale=2) ),
            (Map.mapindex(28,3), markupimage(hddat.data['item']['61i'][0].data, (-15, -40), scale=2) ),
            (Map.mapindex(28,3), markupimage(hddat.data['item']['61i'][0].data, (15, -41), scale=2) ),
            (Map.mapindex(28,3), markupimage(hddat.data['item']['62i'][0].data, (-15, 0), (-15, 15), 32, scale=2) ),
            (Map.mapindex(28,3), markupimage(hddat.data['item']['62i'][0].data, (15, 0), (15, 15), 32, scale=2) ),
            (Map.mapindex(28,1), markuptext('Exit to Level 15', (-53, 0), (0, 60)) ),
            (Map.mapindex(28,1), markuptext('(UnderSpi)', (-35, 20)) ),
            (Map.mapindex(28,1), markuptext('(After watering plant)', (-70, 40)) ) ],
            changes = uppercornermods ))


        underspi_mods = [{}, {}, {}, {}, {}, {}, {} ,{}, {}]
        self.erase(underspi_mods, Map.mapindex(10,31))
        self.erase(underspi_mods, Map.mapindex(11,31))

        self.maplist.append(Mapentry('underspi', 15,
            markup = [
            (Map.mapindex(1,4), markuptext('Start', (-15, 0), (0, 20)) ),
            (Map.mapindex(26,3), markuptext('Exit to Level 7', (-40, 0), (0, 40)) ),
            (Map.mapindex(26,3), markuptext('(Temple)', (-20, 20)) ),
            (Map.mapindex(28,1), markuptext('Kahpa Form', (-33, -45)) ),
            (Map.mapindex(28,1), markupimage(hddat.data['General']['swimmerfacemorph'][29].data, (4, -25)) )],
            changes = underspi_mods ))


        self.maplist.append(Mapentry('wateraci', 16,
            markup = [
            (Map.mapindex(28,30), markuptext('Start', (-15, 0), (0, 20)) ),
            (Map.mapindex(12,23), markupimage(hddat.data['item']['30i'][0].data, (0, 0), (0, 15), 32, scale=2) )] ))

        self.maplist.append(Mapentry('watercan', 17, bgcolour = (0, 0, 48),
            markup = [
            (Map.mapindex(30,4), markupimage(hddat.data['item']['45i'][0].data, (-15, 0), (-15, 15), 32, scale=2) ),
            (Map.mapindex(30,4), markupimage(hddat.data['item']['24i'][0].data, (15, 0), (15, 15), 32, scale=2) ),
            (Map.mapindex(1,13), markuptext('Exit to Level 18', (-37, -40)) ),
            (Map.mapindex(1,13), markuptext('(WaterDra)', (-20, -20), (0, 0)) )] ))


        self.maplist.append(Mapentry('waterdra', 18,
            markup = [(Map.mapindex(28,2), markuptext('Start', (-15, 0), (0, 20)) ),
            (Map.mapindex(12,9), markuptext('Exit to Level 7', (-40, 0), (0, 40)) ),
            (Map.mapindex(12,9), markuptext('(Temple)', (-20, 20)) ),
            (Map.mapindex(28,1), markuptext('Exit to Level 17', (-40, 0), (0, 40)) ),
            (Map.mapindex(28,1), markuptext('(WaterCan)', (-20, 20)) ),
            (Map.mapindex(12,6), markuptext('Ssair Form', (-36, 15)) ),
            (Map.mapindex(12,6), markupimage(hddat.data['General']['dragonfacemorph'][29].data, (1, 35)) )],
            changes=uppercornermods ))

        waterobe_mods = [{}, {}, {}, {}, {}, {}, {} ,{}, {}]
        self.erase(waterobe_mods, Map.mapindex(5, 5))
        self.erase(waterobe_mods, Map.mapindex(5, 6))
        self.erase(waterobe_mods, Map.mapindex(6, 5))

        self.maplist.append(Mapentry('waterobe', 19, bgcolour = (0, 0, 48),
            markup = [
            (Map.mapindex(28,30), markuptext('Start', (-15, 0), (0, 20)) )],
            changes = waterobe_mods ))


        lavamud_mods = [{}, {}, {}, {}, {}, {}, {} ,{}, {}]
        for x in range(11, 15):
            for y in range(0, 2):
                self.erase(lavamud_mods, Map.mapindex(x, y))

        self.maplist.append(Mapentry('lavamud', 20,
            markup = [
            (Map.mapindex(6,30), markuptext('Start', (-15, 0), (0, 20)) ),
            (Map.mapindex(30,30), markuptext('Exit to Level 21', (-40, 0), (0, 40)) ),
            (Map.mapindex(30,30), markuptext('(LavaMine)', (-25, 20)) )],
            changes=lavamud_mods ))


        lavamine_mods = [{}, {}, {}, {}, {}, {}, {} ,{}, {}]
        for x in range(0, 2):
            for y in range(8, 11):
                self.erase(lavamine_mods, Map.mapindex(x, y))
        self.erase(lavamine_mods, Map.mapindex(30, 22))
        self.erase(lavamine_mods, Map.mapindex(31, 22))
        self.erase(lavamine_mods, Map.mapindex(31, 23))
        self.erase(lavamine_mods, Map.mapindex(27, 31))

        self.maplist.append(Mapentry('lavamine', 21,
            markup = [
            (Map.mapindex(2,1), markuptext('Start', (-15, 0), (0, 20)) ),
            (Map.mapindex(3,30), markuptext('Hourglass Panel', (-46, 10)) ),
            (Map.mapindex(1,1), markuptext('Exit to Level 20', (-40, 0), (0, 40)) ),
            (Map.mapindex(1,1), markuptext('(LavaMud)', (-20, 20)) ),
            (Map.mapindex(30,27), markuptext('Exit to Level 7', (-38, 0), (0, 40)) ),
            (Map.mapindex(30,27), markuptext('(Temple)', (-20, 20)) ),
            (Map.mapindex(1,14), markuptext('Grost Form', (-39, -45)) ),
            (Map.mapindex(1,14), markuptext('(Teleports around Hourglass room)', (-112, -15)) ),
            (Map.mapindex(1,14), markupimage(hddat.data['General']['golemfacemorph'][29].data, (-2, 5)) )],

            changes=lavamine_mods ))


        vestetst_mods = [{}, {}, {}, {}, {}, {}, {} ,{}, {}]
        self.erase(vestetst_mods, Map.mapindex(1, 30))
        self.erase(vestetst_mods, Map.mapindex(2, 30))
        self.erase(vestetst_mods, Map.mapindex(1, 31))

        self.maplist.append(Mapentry('vestetst', 22,
            markup = [
            (Map.mapindex(15,23), markuptext('Start', (-15, 0), (0, 20)) ),
            (Map.mapindex(4,10), markupimage(hddat.data['item']['60i'][0].data, (0, -10), (0, 5), 112, scale=2) ),
            (Map.mapindex(22,28), markupimage(hddat.data['item']['12i'][0].data, (0, -40), (0, -25), 32, scale=2) ),
            (Map.mapindex(22,28), markupimage(hddat.data['item']['45i'][0].data, (-15, 0), (-15, 15), 32, scale=2) ),
            (Map.mapindex(22,28), markupimage(hddat.data['item']['46i'][0].data, (15, 0), (15, 15), 32, scale=2) ),
            (Map.mapindex(19,23), markuptext('Exit to Level 24', (-44, -40), (0, 20)) ),
            (Map.mapindex(19,23), markuptext('(Vest2Tst)', (-25, -20)) ),
            (Map.mapindex(19,23), markuptext('(After placing Crystals)', (-72, 0)) )],
            changes=vestetst_mods ))

        self.maplist.append(Mapentry('vestebld', 23, bgcolour = (48, 0, 0) ))


        vest2tst_mods = [{}, {}, {}, {}, {}, {}, {} ,{}, {}]
        for x in range(8, 11):
            self.erase(vest2tst_mods, Map.mapindex(x, 31))
        for y in range(27, 30):
            self.erase(vest2tst_mods, Map.mapindex(31, y))

        self.maplist.append(Mapentry('vest2tst', 24,
            markup = [
            (Map.mapindex(15,18), markuptext('Exit to Level 25', (-44, 0), (0, 40)) ),
            (Map.mapindex(15,18), markuptext('(VesteMaz)', (-28, 20)) ),
            (Map.mapindex(16,4), markuptext('Start', (-15, 0), (0, 20)) )],
            changes = vest2tst_mods ))


        vestemaz_mods = [{}, {}, {}, {}, {}, {}, {} ,{}, {}]
        for x in range(12, 23):
            self.erase(vestemaz_mods, Map.mapindex(x, 0))
        for y in range(1, 10):
            self.erase(vestemaz_mods, Map.mapindex(0, y))

        # Possible markup for vestemaz:
        # First bend: projectile traps
        # First Mana: Acid Pit
        # Second Mana: Lava Pit
        # Third Mana: Mana Drain trap
        # Last sidepath before final room: Electric floor trap

        self.maplist.append(Mapentry('vestemaz', 25,
            markup = [
            (Map.mapindex(15,18), markuptext('Exit to Level 24', (-44, 0), (0, 40)) ),
            (Map.mapindex(15,18), markuptext('(Vest2Tst)', (-28, 20)) ),
            (Map.mapindex(30,30), markuptext('Exit to Level 26', (-44, 0), (0, 40)) ),
            (Map.mapindex(30,30), markuptext('(VesteFin)', (-28, 20)) ),
            (Map.mapindex(14,18), markuptext('Start', (-15, 0), (0, 20)) )],
            changes = vestemaz_mods, bgcolour = (24, 48, 0)))


        vestefin_mods = [{}, {}, {}, {}, {}, {}, {} ,{}, {}]
        for x in range(0, 3):
            for y in range(0, 3):
                self.erase(vestefin_mods, Map.mapindex(x, y))

        self.maplist.append(Mapentry('vestefin', 26,
            markup = [
            (Map.mapindex(16,7), markuptext('Start', (-15, 0), (0, 20)) ),
            (Map.mapindex(25,20), markuptext("Veste's Various Forms", (-5, 20)) )],
            changes=vestefin_mods ))
