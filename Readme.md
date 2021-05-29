# About and Dependencies

This is a series of Python scripts to generate Isometric views of 
Shadow Caster maps, as well as extract most of the Shadow Caster 
Resources. These scripts require [the Python Imaging Library 
(PIL)][pil] and [Python 2.x][py] (tested with Python 2.7.3). PIL 
unfortunately does not yet support Python 3, which prevents these 
scripts from being forward-compatible at this time.

Windows users should be able to download Python and PIL from the above
links. Most Linux/Unix varients should be able to install Python and PIL
via your package manager of choice; Ubuntu users can install the
**python** and **python-imaging** libraries. OSX users should already
have Python, but you may need to compile PIL yourself via the source
download at the PIL website.

The scripts also obviously require **Shadow Caster (CD version)**, which
can be a bit hard to find nowadays. Purchasing a used copy on eBay or
other used game source appears to be the only option.

Special thanks to the [SLADE Editor][slade] and everyone on the 
[ShadowCaster modding thread at Doomworld][doomworld]. Both sources 
were instrumental in the development of these tools.

Please note the **sample.png** image file is used to obtain the Shadow
Caster colour palette and is required for this tool to work.

[pil]: http://www.pythonware.com/products/pil/index.htm
[py]: http://python.org/
[slade]: http://slade.mancubus.net/
[doomworld]: http://www.doomworld.com/vb/everything-else/43927-shadowcaster-modding/

# Usage

There are three scripts included in the package that are intended to be
executed directly. **isomap.py** is the main isometric mapper script,
**shadowdat.py** is a script to extract the contents of a Shadow Caster
.dat file, and **shadowlib.py** is a script to extract the contents of a
Shadow Caster .lib file. In addition to the three scripts above, several
supplimentary scripts can be run to gather debug outputs of one form or
another, and are listed under the **Other Scripts** heading.

## isomap.py

**Usage: python isomap.py \[LIB FILE\] \[cd\_castr.dat\]
\[hd\_castr.dat\]**

Generates a isometric map for each level in the specified Shadow Caster
LIB file (typically shadow.lib). The DAT files are used for image data.

## shadowdat.py

**Usage: python shadowdat.py \[DAT FILE\]**

Extracts the complete contents of a give Shadowcaster dat file. Does not
support the cutscene dat files from the CD version, only cd\_castr.dat
and hd\_castr.dat. The .dat file from the floppy version may also work,
although it is unknown how frequently the floppy version uses the RLE
flag.

## shadowlib.py

**Usage: python shadowlib.py \[LIB FILE\]**

Extracts the complete contents of a given Shadowcaster lib file.
Resources are not interpreted and are written as-is.

## Other Scripts

### shadowdebugmapper.py

**Usage: python shadowdebugmapper.py \[LIB FILE\]\...**

Generates a debug HTML file for each level in the specified LIB file.
Each index in the map is output into a cell in an HTML table containing
the following information:\
The map index\
the value for each of the map layers, in order

### shadowsimplemapper.py

**Usage: python shadowsimplemapper.py \[LIB FILE\]\...**

Generates a debug HTML file for each level in the specified LIB file.
Each index in the map is output into a cell in an HTML table with lines
representing walls.

### shadowmap.py

I didn\'t even write any usage instructions for this, but this can
generate image files for each layer of each map in a given lib file, as
well as CSV files for the data from each supplementary data file.

# Notes

As before, all maps were generated using a Python map generator I wrote.
The map generator for Shadow Caster is a bit improved from the ROTT
version. I am sure it will improve further for the next game. The map
generator decodes all floor/wall/ceiling information, as well as
monster/object/item placement. For any other information, manual markup
has been added. The manual markup has been kept at a minimum; mostly for
area transitions, items dropped by enemies or chests, teleporters, and
identifying obelisks. Some potential markup I excluded include
identifying traps, marking locked doors, and identifying key puzzles.
Some puzzles are identified, but only when they impact something that I
already marked, such as a level transition, or the obelisk in LavaMine.
Underwater transitions are also not exactly marked, but typically if
there is water (or a water-like substince in VesteTst and Vest2Tst), you
can dive under. The under water area is always the very next map number.

If anyone would prefer more markup, please let me know and I can create
an alternate version of the maps for this purpose.

The maps are identified with their exact filename inside of shadow.lib.
Some of the map names are fairly easy to decode, and I could have
expanded them to their "full" name, but I chose not to. Other maps, such
as WaterObe are a bit more cryptic (Water Obelisk?).

Many maps contain inaccessible regions outside the map, suspected to be
used for scripting. In almost all cases, I have blanked out these
regions for the purposes of displaying only the portions of the maps
intended to be viewed in-game. The only exception is the last level,
VesteFin, contains a room where all of Veste's shapeshifting forms
"wait" until he changes into each one. I kept this room in order to
display all of the forms he uses.

RuinADrn is a bit special, as I actually produced two versions of this
map. The first version has the water present, and blanks out any rooms
that are inaccessible in this state. The second version reflects how the
map appears once the water is drained and the level opens up. RuinAWet
is the underwater version of this map. Although technically only a
portion of the map is accessible, the whole map is still included.

I have no idea why there is no map 8, 9 or 10. The above maps reflect
every .map file inside of shadow.lib. The numbers are based on the
number allocated by the in-game automap. As far as I can tell, these
maps simple do not exist.

Note that these maps were generated from the CD version. Vest2Tst and
VesteMaz are exclusive to this version. In the floppy version, the exit
from VesteTst leads directly to VesteFin.
