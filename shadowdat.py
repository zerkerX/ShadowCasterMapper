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

""" Module for processing Shadow Caster dat files.

Also dumps the complete contents of the dat file to disk if run directly.
Only tested for SHADOW.DAT and SHADOW2.DAT.
"""
import pdb
import struct, sys, os.path, traceback
import csv

from PIL import Image, ImageOps

class DatFile:
    """ Dat file main class. Represents the contents of a Shadow Caster
    dat file. Note that RLE encoding is not currently supported.

    Public member variables:
    db -- dictionary of lumps, keyed by lump name.
    data -- lumps. First keyed by group, then by name, then by index after
            the name.
    idxdata -- lumps. First keyed by group, then index.
    """

    datheader = '<HL'

    def __init__(self, filename):
        """ Initializes the current DAT instance by loading from
        the specified file. Will populate the lists of lumps, but will
        not load them yet.
        """
        self.filedata = open(filename, 'rb')
        filesize = os.path.getsize(filename)

        (self.numlumps, self.infotable) = struct.unpack(self.datheader,
            self.filedata.read(struct.calcsize(self.datheader)))

        self.filedata.seek(self.infotable)

        self.data = {}
        self.idxdata = {}
        self.filename = filename
        block = 'General'
        group = 'Unnamed'
        namenum = 0
        inmonsters = False

        for lumpnum in range(self.numlumps):
            templump = Lump(self.filedata)
            tempname = self.loadname(templump)
            #print "{},{}".format(tempname, templump.size)
            if tempname != None:
                if templump.size == 0:
                    group = 'Unnamed'

                    if 'end' in tempname and not inmonsters or \
                            tempname == 'endmonsters':
                        block = 'General'
                        inmonsters = False
                    elif not inmonsters and 'start' in tempname:
                        if tempname == 'startmonsters':
                            inmonsters = True
                        block = tempname.replace('start', '')
                    elif tempname == 'newcursors':
                        block = tempname
                else:
                    group = tempname
            if templump.size > 0:
                if not block in self.data:
                    self.data[block] = {}
                    self.idxdata[block] = []
                if not group in self.data[block]:
                    self.data[block][group] = []
                self.data[block][group].append(templump)
                self.idxdata[block].append(templump)

        # Until we find the palette, load it from a screenshot:
        palimage = Image.open('sample.png')
        self.palette = palimage.getpalette()

    def loadname(self, lump):
        """ Loads the name for the current lump, which is located elsewhere
        in the file, """
        if lump.nameoffs > 0:
            prevpos = self.filedata.tell()
            self.filedata.seek(self.infotable + lump.nameoffs)

            tempname = ''
            namelen = 0
            tempchar= self.filedata.read(1)
            # Read up to the null character
            while ord(tempchar) != 0 and namelen < 60:
                tempname = tempname + tempchar
                tempchar = self.filedata.read(1)
                namelen = namelen + 1

            self.filedata.seek(prevpos)
            return tempname.lower()
        else:
            return None

    def listing(self, listfile):
        """ Creates a directory listing file of the contents of this
        dat file, grouped by section. Saves to the specified file name.
        """
        listing = open(listfile, 'w')

        for block in list(self.data.keys()):
            listing.write("\n{}\n============================\n".format(block))
            for group in list(self.data[block].keys()):
                listing.write("\n{}\n----------------------------\n".format(group))
                for lump in self.data[block][group]:
                    listing.write('{:X}\t{}\t{:X}\n'.format(
                    lump.pos, lump.size, lump.flags))

        listing.close()

    def loadall(self):
        """ Loads and processes all data from the dat file."""
        for block in list(self.data.keys()):
            for group in list(self.data[block].keys()):
                for lumpnum, lump in enumerate(self.data[block][group]):
                    try:
                        if block == 'walls':
                            lump.__class__ = WallLump
                            masked = 'door' in group
                            lump.load(self.palette, masked)
                        elif block == 'flats':
                            lump.__class__ = FlatLump
                            lump.load(self.palette)
                        elif block in ['sprites', 'bursts', 'flame',
                                'greeneye', 'monsters', 'wolf', 'spell'] or \
                                block == 'item' and group.endswith('f') or \
                                block == 'General' and group in ['animateobelisk',
                                    'bombexplode', 'boomarang', 'boomhit']:
                            lump.__class__ = SpriteLump
                            lump.load(self.palette)
                        elif (block in ['item', 'cursor',
                                'handicons', 'newcursors'] or
                                block == 'General' and group not in
                                ['view', 'greymask', 'brownmask',
                                'greenmask', 'goldmask', 'fontdisk',
                                'shadowpage']) and lump.flags == 0:
                            lump.__class__ = GUILump
                            lump.load(self.palette)
                        else:
                            lump.load()
                    except:
                        print("Problem with {}.{}[{}]".format(block, group, lumpnum))
                        traceback.print_exc()

                        # Re-load as raw
                        lump.__class__ = Lump
                        lump.load()

    @staticmethod
    def createpath(pathname):
        """ Simple utility method for creating a path only if it does
        not already exist.
        """
        if not os.path.exists(pathname):
            os.mkdir(pathname)

    def dumpcontents(self, outpath):
        """ Dumps the complete contents of this DAT file to disk in
        the specified folder.
        """
        for block in list(self.data.keys()):
            for group in list(self.data[block].keys()):
                writepath = os.path.join(outpath, block)
                self.createpath(writepath)
                for index, lump in enumerate(self.data[block][group]):
                    try:
                        lump.save(os.path.join(writepath,
                            '{}-{:02}'.format(group, index)))
                    except:
                        print("Problem saving {}.{}[{}]".format(block, group, index))
                        traceback.print_exc()



    def close(self):
        """ Closes the dat file."""
        self.filedata.close()

class Lump(object):
    """ Class for a lump entry in the DAT file. This is the basic lump
    type that can only load RAW data.

    Public member variables:
    size -- the file size of this lump
    flags -- If true, then this lump is RLE encoded (not supported)
    data -- the decoded data for this lump as a Raw byte array.
    """
    direntry = '<LLHH'

    def __init__(self, filedata):
        """ Initializes the basic information about a lump described
        at the current position in the file.

        filedata -- a file handle open for the dat file. The file handle
                    needs to be at the position to read a lump header.
        """
        (self.pos, self.size, self.nameoffs, self.flags) = struct.unpack(self.direntry,
            filedata.read(struct.calcsize(self.direntry)))

        # Cache file handle for future reads. Note that this will be invalid
        # if the DAT file itself is closed.
        self.filedata = filedata

    def load(self):
        """ Loads this lump as basic raw data. No processing. """
        self.filedata.seek(self.pos, 0)
        self.data = self.filedata.read(self.size)

    def save(self, filename):
        """ Saves this lump to the specified filename. Note that the
        filename should not contain an extension.
        """
        tempfile = open(filename, 'wb')
        tempfile.write(self.data)
        tempfile.close()

class WallLump(Lump):
    """ Wall type lump.

    Public member variables:
    size -- the file size of this lump
    flags -- If true, then this lump is RLE encoded (not supported)
    data -- the decoded data for this lump as a PIL Image object.
    """

    @staticmethod
    def maskimage(inimage):
        """ Masks colour 0 in the given image, turning those pixels
        transparent. Returns the resulting RGBA image.
        """
        tempmask = Image.new('L', inimage.size, 255)
        maskdata = list(tempmask.getdata())
        outimage = inimage.convert("RGBA")

        for pos, value in enumerate(inimage.getdata()):
            if value == 0:
                maskdata[pos] = 0

        tempmask.putdata(maskdata)
        outimage.putalpha(tempmask)
        return outimage

    def load(self, palette, processmask=False):
        """ Loads and decodes a WALL lump, storing the resulting data
        as a PIL Image object.

        palette -- a PIL-compatible colour palette
        processmask -- if true, assume colour 0 is transparent
        """
        self.filedata.seek(self.pos, 0)

        width = 64
        (qheight,) = struct.unpack('<H', self.filedata.read(2))
        coloffs = struct.unpack('<64H', self.filedata.read(128)) # Discard; Not needed

        tempimage = Image.fromstring("P", (qheight*4, width),
            self.filedata.read(self.size-130))
        tempimage.putpalette(palette)

        if processmask:
            tempimage = self.maskimage(tempimage)

        self.data = ImageOps.mirror(tempimage.rotate(-90))

    def save(self, filename):
        """ Saves this lump to the specified filename. Note that the
        filename should not contain an extension; .png will be added
        automatically.
        """
        self.data.save(filename + '.png')


class FlatLump(WallLump):
    """ Flat-type (floor) lump

    Public member variables:
    size -- the file size of this lump
    flags -- If true, then this lump is RLE encoded (not supported)
    data -- the decoded data for this lump as a PIL Image object.
    """

    def load(self, palette):
        """ Loads and decodes a Flat lump with the given palette data,
        storing the resulting data as a PIL Image object.
        """
        self.filedata.seek(self.pos, 0)

        self.data = Image.fromstring("P", (64, 64),
            self.filedata.read(self.size))
        self.data.putpalette(palette)


class SpriteLump(WallLump):
    """ Sprite lump

    Public member variables:
    size -- the file size of this lump
    flags -- If true, then this lump is RLE encoded (not supported)
    data -- the decoded data for this lump as a PIL Image object.
    """

    header = '<hh'

    def load(self, palette):
        """ Loads a patch lump, storing the resulting data as a PIL
        Image object using the given palette.
        """
        # Load patch header
        self.filedata.seek(self.pos)
        (self.unknown, self.width) = struct.unpack(self.header,
            self.filedata.read(struct.calcsize(self.header)))

        if (self.width > 320 or self.width <= 0):
            return

        maxheight = 0

        tempdata = [0]*(self.width * 320)
        tempmask = [0]*(self.width * 320)

        self.collumnofs = struct.unpack('<{}H'.format(self.width),
            self.filedata.read(self.width * 2))

        # Load the image column-by-column by working through the colummn offset array
        for x, offset in enumerate(self.collumnofs):
            if offset > 0:
                self.filedata.seek(self.pos + offset)
                (yend, ystart) = struct.unpack('<BB',
                    self.filedata.read(2))
                colsize = yend - ystart + 1
                maxheight = max(maxheight, yend)

                coldata = struct.unpack('<{}B'.format(colsize),
                    self.filedata.read(colsize))

                for index, value in enumerate(coldata):
                    tempdata[(yend - index)*self.width + x] = value
                    if value != 0:
                        tempmask[(yend - index)*self.width + x] = 255

        tempimage = Image.new("P", (self.width, 320))
        tempimage.putpalette(palette)
        tempimage.putdata(tempdata)
        tempimage = tempimage.convert("RGBA")

        tempmaskimage = Image.new("L", (self.width, 320))
        tempmaskimage.putdata(tempmask)
        tempimage.putalpha(tempmaskimage)

        self.data = ImageOps.flip(tempimage.crop((0, 0, self.width, maxheight+1)))


class GUILump(WallLump):
    """ GUI image lump

    Public member variables:
    size -- the file size of this lump
    flags -- If true, then this lump is RLE encoded (not supported)
    data -- the decoded data for this lump as a PIL Image object.
    """

    def load(self, palette):
        """ Loads and decodes a GUI image lump using the given palette,
        storing the resulting data as a PIL Image object.
        """
        self.filedata.seek(self.pos, 0)

        width = 64
        (self.width, self.height, w2, h2) = struct.unpack('<HHHH', self.filedata.read(8))

        tempimage = Image.fromstring("P", (self.width, self.height),
            self.filedata.read(self.size-8))
        tempimage.putpalette(palette)

        self.data = self.maskimage(tempimage)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""Usage: python shadowdat.py [DAT FILE]

Extracts the complete contents of a give Shadowcaster dat file.
Does not support the cutscene dat files from the CD version, only
cd_castr.dat and hd_castr.dat. The .dat file from the floppy version may
also work, although it is unknown how frequently the floppy version uses
the RLE flag.
""")
    else:
        for filename in sys.argv[1:]:
            dat = DatFile(filename)

            outdir = filename + "_output"
            if not os.path.exists(outdir):
                os.mkdir(outdir)

            dat.listing(os.path.join(outdir, 'listing.txt'))
            dat.loadall()
            dat.dumpcontents(outdir)

            dat.close()
