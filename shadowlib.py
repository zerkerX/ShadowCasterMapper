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

""" Module for processing Shadow Caster lib files.

Also dumps the complete contents of the lib file to disk if run directly.
Only tested for SHADOW.LIB and SHADOw2.LIB.
"""
import pdb
import struct, sys, os.path

# from PIL import Image, ImageOps

class LibFile:
    """ Lib file main class. Represents the contents of a Shadow Caster
    lib file.

    Public member variables:
    db -- dictionary of lumps, keyed by lump name.
    filename -- the filename for this lib file
    """

    def __init__(self, filename):
        """ Initializes the current LIB instance by loading from
        the specified file. Will populate the lists of lumps, but will
        not load them yet.
        """
        self.filedata = open(filename, 'rb')
        filesize = os.path.getsize(filename)

        # Read number of lumps (last word in file):
        self.filedata.seek(filesize - 2)
        (numlumps,) = struct.unpack('<h', self.filedata.read(2))

        self.db = {}
        self.filename = filename

        # Load the lump table of contents
        self.filedata.seek(filesize -2 -(Lump.direntrysize() * numlumps) )

        for i in range(numlumps):
            templump = Lump(self.filedata)
            self.db[templump.name] = templump

    def listing(self, listfile):
        """ Creates a directory listing file of the contents of this
        lib file, grouped by section. Saves to the specified file name.
        """
        listing = open(listfile, 'w')

        for lump in list(self.db.values()):
            listing.write('{}\t{}\n'.format(lump.name, lump.size))

        listing.close()

    def loadall(self):
        """ Loads and processes all data from the lib file."""
        for lump in list(self.db.values()):
            lump.load()

    @staticmethod
    def createpath(pathname):
        """ Simple utility method for creating a path only if it does
        not already exist.
        """
        if not os.path.exists(pathname):
            os.mkdir(pathname)

    def dumpcontents(self, outpath):
        """ Dumps the complete contents of this LIB file to disk in
        the specified folder.
        """
        self.createpath(outpath)

        for lump in list(self.db.values()):
            lump.save(os.path.join(outpath, lump.name))

    def close(self):
        """ Closes the lib file."""
        self.filedata.close()


class Lump(object):
    """ Class for a lump entry in the LIB file. Only handles RAW data.

    Public member variables:
    name -- the directory listing name for this lump
    size -- the file size of this lump
    data -- the decoded data for this lump as a Raw byte array.
    """

    # 4 bytes size of lump, little-endian
    # 4 bytes absolute offset, little-endian
    # 13 bytes DOS name, zero-padded (e.g., 8 characters + extension)
    # + room for 1 byte null terminator
    direntry = '<ll13s'

    @staticmethod
    def direntrysize():
        """Returns the size of a single record in the LIB table of contents."""
        return struct.calcsize(Lump.direntry)

    def __init__(self, filedata):
        """ Initializes the basic information about a lump described
        at the current position in the file.

        filedata -- a file handle open for the lib file. The file handle
                    needs to be at the position to read a lump header.
        """
        (self.size, self.pos, tempname) = struct.unpack(self.direntry,
            filedata.read(self.direntrysize()))
        self.name = tempname.rstrip(b'\0').decode()

        # Cache file handle for future reads. Note that this will be invalid
        # if the LIB file itself is closed.
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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""Usage: python shadowlib.py [LIB FILE]

Extracts the complete contents of a given Shadowcaster lib file.
Resources are not interpreted and are written as-is.
""")
    else:
        for filename in sys.argv[1:]:
            lib = LibFile(filename)

            outdir = filename + "_output"
            if not os.path.exists(outdir):
                os.mkdir(outdir)

            lib.listing(os.path.join(outdir, 'listing.txt'))
            lib.loadall()
            lib.dumpcontents(outdir)

            lib.close()
