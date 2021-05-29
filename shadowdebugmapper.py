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

"""Simple Debug Mapper for Shadow Caster maps
This creates an HTML output of the Shadow Caster data for debugging purposes.
"""
import sys, os

import shadowmap, shadowlib

class debugmapper:
    """Debug Mapper to generate HTML debug maps"""
    def __init__(self, level):
        self.level = level

    def savemap(self, outpath):
        """Saves the current level as an HTML debug map"""
        outfile = open(os.path.join(outpath, "{}.html".format(self.level.name)), 'w')
        outfile.write("""<html><head>
<title>{}</title>
<style>
.solid {{background-color: #BBB}}
.layer0 {{color: red}}
.layer1 {{color: green}}
.layer2 {{color: blue}}
.layer3 {{color: teal}}
.layer4 {{color: orange}}
.layer5 {{color: orchid}}
.layer6 {{color: indigo}}
.layer7 {{color: brown}}
.index {{font-size: 0.8em}}
</style></head><body>
<table>""".format(self.level.name))

        for y in range(32):
            outfile.write('<tr>')
            for x in range(32):
                index = y*32 + x
                # Decide which colour (via class attribute) to draw based
                # on solid wall, floor or empty space
                # Print index and wall id, as applicable
                if self.level.maplump.layers[0][index] == 1:
                    outfile.write('<td class="solid">')
                else:
                    outfile.write('<td>')

                outfile.write('<span class="index">{}</span><br>'.format(index))

                for layernum, layer in enumerate(self.level.maplump.layers):
                    if layer[index] > 0:
                        outfile.write('<span class="layer{}">{}:{:03}</span> '.format(layernum, layernum, layer[index]))

                outfile.write('</td>')

            outfile.write('</tr>\n')

        outfile.write("</table></body></html>\n")
        outfile.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""Usage: python shadowdebugmapper.py [LIB FILE]...

Generates a debug HTML file for each level in the specified LIB file.
Each index in the map is output into a cell in an HTML table
containing the following information:
The map index
the value for each of the map layers, in order
...
""")
    else:

        for filename in sys.argv[1:]:
            lib = shadowlib.LibFile(filename)

            maps = shadowmap.MapSet(lib)

            outpath = filename.replace('.', ' ') + ' DEBUG'
            if not os.path.exists(outpath):
                os.mkdir(outpath)

            for level in maps.maps:
                mapper = debugmapper(level)
                mapper.savemap(outpath)

            lib.close()
