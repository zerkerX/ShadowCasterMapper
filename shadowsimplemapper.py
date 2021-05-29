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

"""Simple Mapper for Shadow Caster maps
This creates an HTML output of the Shadow Caster data for debugging purposes.
The map format displays basic floors and walls with overall map X, Y coordinates
"""
import sys, os

import shadowmap, shadowlib

class debugmapper:
    """Simple Mapper to generate HTML maps"""
    def __init__(self, level):
        self.level = level

    def savemap(self, outpath):
        """Saves the current level as an HTML map"""
        outfile = open(os.path.join(outpath, "{}.html".format(self.level.name)), 'w')
        outfile.write("""<html><head>
<title>{}</title>
<style>
.solid {{background-color: #EEE}}
table {{border-spacing: 0 }}
td {{
    border: 0.5mm solid #EEE;
    width: 6mm;
    height: 6mm;
}}
.northwall {{border-top: 0.5mm solid black}}
.westwall {{border-left: 0.5mm solid black}}
</style></head><body>
<table>""".format(self.level.name))

        outfile.write("<tr><th></th><th>{}</th></tr>".format("</th><th>".join([str(x) for x in range(32)])) )

        for y in range(32):
            outfile.write('<tr><th>{}</th>'.format(y))
            for x in range(32):
                index = y*32 + x
                # Use class list to decide whether this tile has a floor,
                # a north wall, and/or a western wall
                classes = []

                if self.level.maplump.layers[shadowmap.FLOOR][index] == 1:
                    classes.append("solid")
                if self.level.maplump.layers[shadowmap.NORTHWALL][index] > 0:
                    classes.append("northwall")
                if self.level.maplump.layers[shadowmap.WESTWALL][index] > 0:
                    classes.append("westwall")

                if self.level.maplump.layers[8][index] > 0:
                    content = self.level.maplump.layers[8][index]
                else:
                    content = '&nbsp;'

                outfile.write('<td class="{}">{}</td>'.format(' '.join(classes), content))

            outfile.write('</tr>\n')

        outfile.write("</table></body></html>\n")
        outfile.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""Usage: python shadowsimplemapper.py [LIB FILE]...

Generates a debug HTML file for each level in the specified LIB file.
Each index in the map is output into a cell in an HTML table
with lines representing walls.
...
""")
    else:

        filename = sys.argv[1]
        lib = shadowlib.LibFile(filename)

        maps = shadowmap.MapSet(lib)

        outpath = filename.replace('.', ' ') + ' SIMPLE'
        if not os.path.exists(outpath):
            os.mkdir(outpath)

        for level in maps.maps:
            mapper = debugmapper(level)
            mapper.savemap(outpath)

        lib.close()
