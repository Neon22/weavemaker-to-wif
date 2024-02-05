#weavemaker

from struct import unpack, calcsize

# https://weavemaker.com/downloads/


# Format for wmdf file is:
# 2 byte BE offset jumps past Color 'Q' info, to remaining chunks of data.
#  - possibly no Q at all (Just B-warp, W-weft)
# for each chunk:
#  - read 2byte BE Int of length of chunk in entities
#  - read single char of chunk identifier
#  - read single byte of size of entity in bytes
#   (use this times length to calc dist to next chunk)
# parses neatly into byte length of entire file.

# Colors in 'Q' field are:
#  - rgb screen and rgb print (range 65535)
#  - a datestamp - followed by text lables for those colors.
#  - a lot of unused(by us) data about plies etc.
#  No more than 40 individual color chips in a draft.

# A Colorway is a single line of color chips (maj,min,acc)x2 for warp and weft.
#  - max 14 chips in a warp and weft combined row, (16 including default B(warp) and W(weft))
#  - a max of 5 colorways
# The colorway field 'C' defines:
#  - the color counts in warp and weft sections
#  - the mapping between the color index (say in warp_colors ('s'))
#    and the color palette defined in 'Q'


# All segments available in the file format.
#  - True indicates we parse some aspect of the segment for wif conversion.
known = {"C": [True, " - Colorway",],
         "M": [True, " - Colorway",],  # unused
         "A": [True, " - Major/Minor/Accent ",],  # unused
         "Q": [True, " - ColorPalette (newest)",],
         "D": [True, " - file format code - Typically tracks the software version code from the plist",  ],
         "g": [True, " - Author's name, or Controls",  ],   # unused
         "n": [True, " - Name (file name)",  ],
         "p": [True, " - Pegplan", ],
         "q": [True, " - Weft colors",],
         "r": [True, " - Treadling",  ],
         "s": [True, " - Warp colors",],
         "t": [True, " - Threading",  ],
         "h": [False, " - Threading",  ],  # need examples
         "u": [True, " - Tieup", ],
         "Y": [True, " - Remarks (public, see also *)",],
         "*": [True, " - Remarks (private, see also Y)", ],
         "R": [False, " - Tromp type",],
         "T": [False, " - Color tromp",],
         # nice to have maybe ?
         "e": [False, " - Ends per inch",],  # not really EPI
         "f": [False, " - Picks per inch",],  # not really PPI
         "E": [False, " - reed",],
         "K": [False, " - Denting",],
         "L": [False, " - Selvages",],
         "P": [False, " - Colorway (newer)",],  # need examples
         "c": [False, " - Colorway (old)",],  # need examples
         # probably ignore these
         "9": [False, " - User's name ('user' segment)"],
         "b": [False, " !!unknown!!",],
         "B": [False, " - Print options",],
         "d": [False, " - Stop motion",],
         "J": [False, " - Fabric size",],
         "k": [False, " - Dobby pick number",],
         "m": [False, " - Palette mask",],
         "N": [False, " - Beaming (see also S)",],
         "a": [False, " - Repeats",],
         "S": [False, " - Beaming (see also N)",],
         "U": [False, " - Color tieup",],
         "v": [False, " - Production",],
         "V": [False, " - Cost",],
         "x": [False, " - Pixels (fabric)",],
         "8": [False, " - File creation date",]
         }

def build_wif_header(title, threading, liftplan=False, need_warpcolor=True, need_weftcolor=True):
    tieup_liftplan = "LIFTPLAN=true\n" if liftplan else "TIEUP=true\nTREADLING=true\n"
    warpcolors = "WARP COLORS=true\n" if need_warpcolor else ""
    weftcolors = "WEFT COLORS=true\n" if need_weftcolor else ""
    return f"""[WIF]\nVersion=1.1\nDate=April 20, 1997\nDevelopers=wif@mhsoft.com\nSource Program=ISOweave online
Source Version=1.0\n\n[CONTENTS]\nCOLOR PALETTE=true\nTEXT=true\nWEAVING=true\nWARP=true\nWEFT=true
COLOR TABLE=true\nTHREADING=true\nNOTES=true\n{warpcolors}{weftcolors}{tieup_liftplan}\n[TEXT]\nTitle={title}\n\n[THREADING]\n{threading}\n"""

def build_wif_tie_treadle(tieup, treadling):
    """
    only called if these are needed
    I.e. not liftplan
    """
    return f"[TIEUP]\n{tieup}\n[TREADLING]\n{treadling}\n"

def build_wif_liftplan(liftplan):
    """
    only called if needed
    """
    return f"\n[LIFTPLAN]\n{liftplan}\n"

def build_wif_notes(notes_list):
    text = [f"{i+1}={n}\n" for i,n in enumerate(notes_list)]
    notes = "\n[NOTES]\n" + "".join(text) + "\n"
    return notes

def build_wif_colors(need_warpcolor, warp_colors,
                     need_weftcolor, weft_colors, palette):
    """
    Warp Colors, Weft Colors, Color Table, Color Palette
    """
    # [COLOR TABLE]\n1=255,255,255\n2=0,0,0\n\n[COLOR PALETTE]\nRange=0,255\nEntries=2\n
    # [WARP COLORS] WEFT COLORS
    result = ""
    if need_warpcolor:
        result += f"[WARP COLORS]\n{warp_colors}\n"
    if need_weftcolor:
        result += f"[WEFT COLORS]\n{weft_colors}\n"
    result += f"\n[COLOR PALETTE]\nRange=0,255\nEntries={len(palette)}\n"
    result += "\n[COLOR TABLE]\n"
    for [i,c] in palette:
        result += f"{i}={','.join([str(a) for a in c])}\n"
    #print("Colors:",result)
    return result

def build_wif_weaving(warp_frequent, weft_frequent, num_treadles, num_shafts, num_threads, num_wefts):
    """
    Weaving, Warp, Weft
    """
    #"[WEAVING]\nRising Shed=true\nTreadles=",{self.width}"\nShafts=",{self.height}"\n\n
    #[WARP]\nUnits=centimeters\nColor=0\nThreads=",{self.height}"\nSpacing=0.212\nThickness=0.212\n\n
    #[WEFT]\nUnits=centimeters\nColor=1\nThreads=",{self.width}"\nSpacing=0.212\nThickness=0.212\n\n
    result = f"\n[WEAVING]\nRising Shed=true\nTreadles={num_treadles}\nShafts={num_shafts}\n\n"
    result += f"\n[WARP]\nUnits=centimeters\nColor={warp_frequent}\nThreads={num_threads}\nSpacing=0.212\nThickness=0.212\n\n"
    result += f"\n[WEFT]\nUnits=centimeters\nColor={weft_frequent}\nThreads={num_wefts}\nSpacing=0.212\nThickness=0.212\n\n"
    return result


class WMDF(object):
    """
    Given the contents of the file as a bytearray:
    - extract as much info as possible,
    - report,
    - save as a wif file.
    """
    def __init__(self, data, colors, filename, verbose=False):
        self.data = data
        self.colors = colors
        self.filename = filename
        self.wif = None  # wif will go here
        self.wif_filename = None  # new wif filename will go here
        self.conversion_notes = []
        self.warnings = []  # if it didn't go right - add a note in here.
        #
        self.treadle_count = 0   # might not be any
        #self.weft_count = 0      # might not be any
        self.tieup_treadles = 0  # might not be any
        self.pegplan_width = 0   # might not be any
        self.pegplan_height = 0  # might not be any
        self.tieup_height = 0    # might not be any
        
        # Threading first
        self.shaft_count, self.threading = self.parse_sequence('t')
        if verbose:
            print(f"Threading: {self.shaft_count} shafts, {len(self.threading)} warp threads")
        # Tromp as writ ?
        self.taw = self.parse_text('R')
        if self.taw:  # n=normal, v = tabby/overshot (nope)
            self.trompaswrit = True
            self.conversion_notes.append("Tromp-as-writ selected. Warp copied to Weft")
            if self.taw != 'n':
                self.warnings.extend(["Tromp-as-writ was selected with special tabby or overshot option.",
                                      "Alas cannot support this - so have simply repeated weft.",
                                      "The result is NOT as defined in the original file."])
            # replicate threading in treadling
            self.weft_count, self.treadling = self.shaft_count, self.threading
            self.treadle_count = len(self.threading)
        else:  # no taw
            # Load Treadling as usual
            treadling = self.parse_sequence('r')
            if treadling:
                self.treadle_count, self.treadling = treadling
                self.weft_count = len(self.treadling)
                if verbose:
                    print(f"Treadling: {self.treadle_count} treadles, {len(self.treadling)} weft threads")
        #
        tieup = self.parse_sequence('u')
        if tieup:
            self.tieup_treadles, self.tieup = tieup
            self.tieup_height = len(self.tieup)
            if verbose:
                print(f"Tieup: {tieup[0]} treadles, {self.tieup_height} shafts")
        # Pegplan
        pegplan = self.parse_sequence('p')
        if pegplan:
            self.pegplan_width, self.pegplan = pegplan
            self.weft_count = len(self.pegplan)
            if verbose:
                print(f"Pegplan: {self.pegplan_width} treadles, {len(self.pegplan)} weft threads")
        #
        self.liftplan = True if pegplan else False
        #! logic to test all dimensions agree but we don't really need to maybe for wif ??
        # if verbose:
        #print("Check:\n - shafts=",self.shaft_count, "tieup_height =:",self.tieup_height, "weftcount:",self.weft_count)
        #print(" - treadles=", self.treadle_count, "pegplan=", self.pegplan_width, "tieup_treadles =",self.tieup_treadles)
        #
        self.name = self.parse_text('n')
        self.version = self.parse_text('D')
        self.comments = self.parse_text('Y')
        self.remarks = self.parse_text('*')
        if self.remarks == "---no launch string found---":
            self.remarks = ""
        #print(self.remarks)
        self.username = self.parse_text('g')
        # warp colors, weft colors
        self.warp_colors = self.parse_index('s')
        self.warp_c_indices = list(set(self.warp_colors))
        # do we have color trmp as writ set
        self.color_taw = self.parse_text('T')
        if self.color_taw:
            # color tromp as writ is set
            # there is no weft color - copy warp
            self.weft_colors = self.warp_colors
            self.weft_c_indices = self.warp_c_indices
            self.conversion_notes.append("Color tromp-as-writ selected. Warp colors copied to weft colors.")
        else:
            # load weft colors as usual
            self.weft_colors = self.parse_index('q') # if weft missing - copy warps (taw color)
            self.weft_c_indices = list(set(self.weft_colors))
        #self.majminacc = self.parse_index('A')  # unused
        self.colorway = self.parse_index('C')
        self.c_mapping = self.setup_colorC(self.colorway, self.colors)
        # self.lookup_ColorM(self.parse_index('M'), self.colors)  # unused
        # EPI, PPI
        # print(self.parse_EPI_PPI('e'))
        # print(self.parse_EPI_PPI('f'))
        # a = self.parse_sequence('e')
        # b = self.parse_sequence('f')
        # print(a)
        # print(b)
        # reed, beaming, denting,
        
        

    def __repr__(self):
        mode = "Liftplan" if self.liftplan else "Tieup"
        threads = f"{len(self.threading)} warps,"
        wefts = f"{self.weft_count} wefts,"
        colorways = f"{len(self.c_mapping)} colorways,"
        warp_map,weft_map = self.c_mapping[0]
        colors_used = len(warp_map) + len(weft_map)
        colors = f"{colors_used} colors used from {len(self.colors)} defined"
        return f"<Wmdf: {self.filename}, {mode} {threads}  {wefts} {colorways} {colors}>"

    def report_warning(self):
        """
        What went wrong.
        """
        msg = []
        msg.append("Warning:")
        msg.append("The following problems with conversion were found:")
        msg.append("\n".join(self.warnings))
        return msg

    def report_conversion_notes(self):
        """
        Processing notes about choices made.
        """
        msg = []
        msg.append("Conversion notes:")
        msg.append("\n".join(self.conversion_notes))
        return msg

    def report_summary(self):
        """
        What did we find overall.
        """
        msg = []
        version = f"(version {self.version})" if self.version else "(no version)"
        msg.append(f"For: {self.filename} {version}")
        mode = "Liftplan" if self.liftplan else "Tieup"
        msg.append(f"Has a {mode}.")
        msg.append(f"Contains {len(self.threading)} warps, and {self.weft_count} wefts.")
        if len(self.c_mapping) == 1:
            msg.append(f"A single colorway is specified,")
        else:
            msg.append(f"{len(self.c_mapping)} colorways are specified,")
        warp_map,weft_map = self.c_mapping[0]
        msg.append(f"{len(warp_map) + len(weft_map)} colors are used from {len(self.colors)} defined.")
        if self.remarks:
            msg.append(f"Remarks: {self.remarks}")
        if self.comments:
            msg.append(f"Remarks: {self.comments}")
        return msg

    def report_fstructure(self):
        """
        What do we have in this file
        """
        msg = []
        msg.append("File Structure:")
        msg.append(f"Report: {len(self.data)} segments found")
        msg.append(f" - {list(self.data.keys())}")
        for id in self.data:
            size = self.data[id][0]
            chunk = self.data[id][1]
            length = len(chunk)
            entity_count = int(length/size)
            supported = "OK" if known[id][0] else "unparsed"
            msg.append(f" - {id}  {entity_count:>3} entities.  ({supported})  (size:{size}  bytes:{length}) {known[id][1]}")
        return msg

    def most_common_color(self, color_indices):
        """
        Which color in indices is used most, and its count.
        - indices are ints (self.warp_color or self.weft_color)
        """
        color_ids = list(set(color_indices))  # which colors referenced
        frequencies = [color_indices.count(i) for i in color_ids]
        max_freq = max(frequencies)
        color_most_used = color_ids[frequencies.index(max_freq)]
        # print(f"colors used:{color_ids}, max_freq:{max_freq} on color {color_most_used}")
        return color_most_used, max_freq

    def build_wif_palette(self, colorway=0):
        """
        amalgamate the list of color and the mapping suitable for a wif.
        - return [id, [r,g,b]] sequences for warp and weft
        #! needs to fill in missing gaps using full palette
        """
        colorgroup = self.c_mapping[colorway]
        warp_group = [p for p in colorgroup[0]]
        weft_group = [p for p in colorgroup[1]]
        #print("Palette:",warp_group)
        warp_palette = [[i[0],i[-1][0]] for i in warp_group]
        weft_palette = [[i[0],i[-1][0]] for i in weft_group]
        #print(f"Warp palette: {warp_palette}\nWeft palette: {weft_palette}")
        # combine
        warp_palette.extend(weft_palette)
        warp_palette.sort()
        #print(warp_palette)
        # however we need to fill in numeric gaps with colors from palette
        new_palette = []
        palette_dict = dict(warp_palette)
        for i in range(1,len(self.colors)):  #! wrong we need to start from 0 but number from 1 and so all indices in warp/wef_color need to be increased by 1 (when writiing)
            if i in palette_dict:
                new_palette.append([i,palette_dict[i]])
            else: # insert one from palette
                new_palette.append([i,self.colors[i][0]])
        #! also wrong
        new_palette.append([len(self.colors),[0,0,0]])
        #print(new_palette)
        return new_palette #warp_palette

    def make_wif(self, colorway=0):
        """
        Need to create:
        - label, make_threading
        - make_tieup, make_treadling/liftplan
        - num_treadles, num_shafts, warp_threadcount, weft_threadcount
        """
        # collect all useful fields for printing
        dirpos = self.filename.rfind('/')
        if dirpos >= 0:
            label = self.filename[dirpos+1:]
        else:
            label = self.filename
        threading = ""
        for i,t in enumerate(self.threading):
            threading += f"{i+1}={t.find('1')+1}\n"
        threading = threading[:-1]
        # Liftplan
        liftplan, treadling, tieup = "","",""
        if self.liftplan:
            for i,p in enumerate(self.pegplan):
                actives = [f"{i+1}" for i in range(len(p)) if p[i]=='1']
                liftplan += f'{i+1}={",".join(actives)}\n'
        else:  # tieup and treadling
            for i,t in enumerate(self.treadling):
                actives = [f"{i+1}" for i in range(len(t)) if t[i]=='1']
                treadling += f'{i+1}={",".join(actives)}\n'
            # swap from rows to columns
            tieup_as_cols = []
            for i in range(self.tieup_treadles):  # traverse treadles not shafts
                tieup_as_cols.append("".join([self.tieup[h][i] for h in range(self.tieup_height)])) 
            # print(tieup_as_cols) 
            for i,t in enumerate(tieup_as_cols):
                actives = [f"{i+1}" for i in range(len(t)) if t[i]=='1']
                tieup += f'{i+1}={",".join(actives)}\n'
        # color info
        # get counts for most frequent
        warp_color_most_used, warp_freq = self.most_common_color(self.warp_colors)
        need_warpcolor = True if warp_freq != len(self.warp_colors) else False
        weft_color_most_used, weft_freq = self.most_common_color(self.weft_colors)
        need_weftcolor = True if weft_freq != len(self.weft_colors) else False
        warp_colors = ""
        if need_warpcolor:
            for i,c in enumerate(self.warp_colors):
                if c != warp_color_most_used:
                    warp_colors += f"{i+2}={c}\n"
            warp_colors = warp_colors[:-1]
            # print(warp_colors, warp_color_most_used)
        weft_colors = ""
        if need_weftcolor:
            for i,c in enumerate(self.weft_colors):
                if c != weft_color_most_used:
                    weft_colors += f"{i+2}={c}\n"
            weft_colors = weft_colors[:-1]
        palette = self.build_wif_palette(colorway)
        notes = [f"From: {self.filename} Weavemaker version = {self.version if self.version else '(version unknown)'}"]
        if self.comments:
            c = self.comments.splitlines()
            notes.append("Comments:")
            notes.extend(c)
        if self.remarks:
            c = self.remarks.splitlines()
            notes.append("Remarks:")
            notes.extend(c)
        #
        # Got everything ready. So:
        # Build the filestring
        wif = build_wif_header(label, threading, self.liftplan, need_warpcolor, need_weftcolor)
        wif += build_wif_notes(notes)
        if self.liftplan:
            wif += build_wif_liftplan(liftplan)
        else:
            wif += build_wif_tie_treadle(tieup, treadling)
            # print("Tieup:",tieup)
        # colors, palette, table
        wif += build_wif_colors(need_warpcolor, warp_colors,
                                need_weftcolor, weft_colors, palette)
        # weaving, warp, weft
        if self.liftplan:
            wif += build_wif_weaving(warp_color_most_used, weft_color_most_used,
                                 self.shaft_count, self.shaft_count, len(self.threading), self.weft_count)
        else:
            wif += build_wif_weaving(warp_color_most_used, weft_color_most_used,
                                 self.tieup_treadles, self.shaft_count, len(self.threading), self.weft_count)
        self.wif = wif
        self.wif_filename = self.calc_wif_filename(self.filename, colorway)

    def calc_wif_filename(self,filename, colorway):
        """ make new filename """
        dotpos = filename.rfind(".")
        cway = f"_colorway{colorway+1}"
        if dotpos > -1:
            newfilename = filename[:dotpos]+cway+".wif"
        else:
            newfilename = filename+cway+".wif"
        return newfilename

    def save_wif(self):
        with open(self.wif_filename, 'w') as f:
            f.write(self.wif) 

    def parse_text(self, id, verbose=False):
        """
        Contents are text
        - e.g. n,g,D,*,Y
        """
        if verbose:
            print("Parsing:",id, known[id][1])
        if id in self.data:
            size = self.data[id][0]
            chunk = self.data[id][1]
            length = len(chunk)
            count = len(chunk)
            name = unpack(f"{count}s", chunk)[0]
            if verbose:
                print(f"    - {str(name, 'utf-8')}")
            return str(name, 'utf-8')

    def parse_index(self, id, verbose=False):
        """
        Contents are bytes as integers
        - e.g. q,s,A,M,C
        """
        if verbose:
            print("Parsing:",id, known[id][1])
        if id in self.data:
            size = self.data[id][0]
            chunk = self.data[id][1]
            length = len(chunk)
            count = int(len(chunk) / size)
            result = []
            for i in range(count):
                start = i*size
                value = unpack(f">b", chunk[start:start+size])[0]
                if verbose:
                    print("    -",i,value)
                result.append(value)
            return result

    def parse_EPI_PPI(self, id, verbose=False):  # unused
        """
        Contents are 4 entities size 8
        - i.e. e,f
        """
        if verbose:
            print("Parsing:",id, known[id][1])
        if id in self.data:
            result = []
            size = self.data[id][0]
            chunk = self.data[id][1]
            length = len(chunk)
            count = int(len(chunk) / size)
            if verbose:
                print(f" - entity size,count = {size},{count}, (bytes={length})")
            for i in range(count):
                start = i*size
                value = unpack(f">4H", chunk[start:start+size])[0]
                print(value)
                result.append(value)
            return result

    def parse_h(self, segments, verbose=False):  # unused (no ref file)
        " old threading "
        id = 'h'
        if verbose:
            print("Parsing:",id, known[id][1])
        if id in segments:
            size = segments[id][0]
            chunk = segments[id][1]
            length = len(chunk)
            if len(chunk) != 1:
                print("!!Unexpected old style threading file. unsupported")
                # no test data yet
                print(chunk, len(chunk))
            return None

    def parse_sequence(self, id, verbose=False):
        """
        Parse Threading, treadling,pegplan,tieup.
        - auto determine bytes structure. Max is 32 or 150 (depending on structure).
        - clip to max referenced size
        """
        if verbose:
            print("Parsing:",id, known[id][1])
        if id in self.data:
            size = self.data[id][0]
            chunk = self.data[id][1]
            length = len(chunk)
            count = int(len(chunk) / size)
            if verbose:
                print(f" - entity size,count = {size},{count}, (bytes={length})")
            # usually 4, 80 byteslong, 20 wide(4*8=32)
            # 28 560 20 for 36,40,42,120 high (28*8=224) (max=150)
            values = []
            for i in range(count):
                start = i*size
                value = unpack(f">{size//4}I", chunk[start:start+size])
                # print("    -",i,value)
                # usually 32 or under - so a single I (4 bytes)
                # but if over 32 then use 7x I (28 bytes) to hold data up to 150
                if len(value) == 1:
                    value_str = f"{bin(value[0])[2:]:>032}"  # pack leading zeroes
                else:  # over 32 (so 28x B bytes)
                    value = unpack(f">{size}B", chunk[start:start+size])
                    # print("    -",i,value)
                    value_str = ""
                    for v in value[::-1]:  # reverse
                        binary = f"{bin(v)[2:]:>08}"  # pack leading zeroes
                        value_str += binary
                    # print("    -",i,value_str, len(value_str))#, bin(value)[2:])
                values.append(value_str)
            # Find max bits needed to encode this pattern
            max_used = max(c.rfind('1') for c in values) + 1
            # clip values to max_used
            for i,col in enumerate(values):
                values[i] = col[:max_used]
                if verbose:
                    print(values[i])
            # print("shafts=:",max_used)
            return [max_used, values]   

    def setup_colorC(self, table, colors, verbose=False):
        """
        C mapping: mapping the weft_color to the color palette
        - chips in a colorway cannot exceed 16
        - no more than 5 colorways
        """
        if verbose:
            print("C mapping")
            print(f"  {len(colors)} colors found: {[colors[i][1] for i in range(len(colors))]}")
        num_colorways = table[0]  # how many colorways in the file
        colorway_sizing = table[1:7]
        colorway_chipcount = sum(colorway_sizing)  # how many chips in colorway
        warp_count = sum(colorway_sizing[:3])  # how many on warp side (Maj/Min/Acc)
        weft_count = sum(colorway_sizing[3:])  # how many on weft side
        if verbose:
            print(f"{num_colorways} Colorways found. With {warp_count} warp and {weft_count} weft colors")
        # print(num_colorways, colorway_chipcount, warp_count, weft_count)
        # print(colorway_sizing)
        # maps for each colorway
        colorway_maps = [table[s:s+colorway_chipcount] for s in range(7,len(table),colorway_chipcount)]
        # print(colorway_maps)
        max_chips = sum(colorway_sizing)
        if verbose:
            print("Warp indices:", self.warp_c_indices)
            print("Weft indices:", self.weft_c_indices)
        mappings = []
        for j,cway in enumerate(colorway_maps):
            warp_map = []
            weft_map = []
            for i,idx in enumerate(self.warp_c_indices):
                # note we use i not idx as the index here
                #print(colorway_maps[j][:warp_count],i, idx)
                ind = colorway_maps[j][:warp_count][i]
                warpcolor = colors[ind]
                warp_map.append([idx,warpcolor])
                if verbose:
                    print("  warp",i,idx,"maps to", ind,"(", warpcolor,")")
            for i,idx in enumerate(self.weft_c_indices):
                #print(colorway_maps[j][-weft_count:],i, idx)
                ind = colorway_maps[j][-weft_count:][i]
                weftcolor = colors[ind]
                weft_map.append([idx,weftcolor])
                if verbose:
                    print("  weft",i,idx,"maps to", ind,"(", weftcolor,")")
            mappings.append([warp_map, weft_map])
        #
        if verbose:
            for m in mappings:
                print(m)
        return mappings

    # def lookup_ColorM(self, table, colors):
        # """
        # M mapping
        # - colors is palette
        # """
        # print("M mapping:")
        # print(f"  {len(colors)} colors found: {[colors[i][1] for i in range(len(colors))]}")
        # table = [t for t in table if t != -1]
        # print(" ", len(table), table)


#
def read_weavemaker(filename):
    """
    Get contents of the file as bytestream
    """
    with open(filename, mode="rb") as inf:
        contents = inf.read() 
    return contents

def read_segment(contents, idx):
    """
    Expect to read a segment starting at idx
    - len is a BE 16bit Int - counting in entities to end of segment
    - id is a single char label identifier
    - size is a byte of entity length
    """
    seg_len = unpack('>H', contents[idx:idx+2])[0]
    id = unpack('s', contents[idx+2:idx+3])[0]
    size = unpack('b', contents[idx+3:idx+4])[0]
    try:
        label = str(id, 'UTF-8')
    except:
        label = "nope"
        print("!!!Unexpected", label)
    return seg_len, label, size

def read_colors(block, verbose=False):
    """
    Color block starts at 3rd byte in file.
    - rgb screen colors in 'a' and print in 'b'
    - description in following structure: 'd','e'
    Values are defined in 65535 space
    - rest ignored.
    """
    assert('Q' == chr(block[0]))  # followed by a half of dubious value?
    # fixed (a6,b6,c12), (n12,05,p5,q5,o5,s12,t12,u12,v12)
    # +bytecount = (d,e,f,g,h,i)
    colors = [[[255,255,255],"WHITE"], [[0,0,0],"BLACK"]]
    parts = {'a':[6],'b':[6],'c':[12],  # screen color, print color, creation date
             # defghi = names of variable length
             'j':[12],'k':[12],'l':[12],'m':[12],  # 12 bit floats
             'n':[12],  # n is a float
             'o':[5],'p':[5],'q':[5],'r':[5],  # ints
             's':[12],'t':[12],'u':[12],'v':[12]}  # sizes
    start = 3 # 'a'
    if start == len(block):
        # nothing here
        return colors
    collection = []
    # print(len(block),start)#chr(block[start])
    assert('a' == chr(block[start]))
    while start < len(block):
        abc = []
        for id in ['a','b','c']:
            size = parts[id][0]
            if id == 'c':  # a date
                value = unpack(f"{size}s", block[start+1:start+1+size])[0]
                abc.append(str(value, 'utf-8'))
            else: # color = 3 H (unisigned ints)
                abc.append(unpack(f'>3H', block[start+1:start+1+size]))
            start += 1 + size
        # print("abc:",abc)
        # now unpack the variable length text fields
        defghi = []
        for id in ['d','e','f','g','h','i']:
            # print(chr(block[start]))
            assert(id == chr(block[start]))
            size = unpack('b', block[start+1:start+2])[0]
            if id in ['d','e']:
                value = unpack(f'{size}s', block[start+2:start+2+size])[0]
                value = str(value, 'utf-8')
            else:
                value = unpack(f'{size}b', block[start+2:start+2+size])
            #print(id,size,value)
            defghi.append(value)
            start += 2 + size
        # print("defghi:",defghi)
        # now unpack the remaining fixed length fields
        n_to_v = []
        for id in ['n','o','p','q','r','s','t','u','v']:
            size = parts[id][0]
            if size == 5:
                value = unpack(f"{size}s", block[start+1:start+1+size])[0]
                n_to_v.append(str(value, 'utf-8'))
            else:  # size=12
                n_to_v.append(unpack(f'>12s', block[start+1:start+1+size]))
            start += 1 + size
        # print("n_to_v:",n_to_v)
        collection.append([abc,defghi,n_to_v])
    # print("collection:")
    # for c in collection: print("  ",c)
    # Create rgb colors
    for i,c in enumerate(collection):
        rgb = [int(val/65536*256) for val in c[0][0]]
        name = c[1][0] + c[1][1]
        colors.append([rgb, name])
        if verbose:
            print(f"{i+1}: {rgb}  {name}")
    return colors
    

def parse_wmdf(contents, verbose=False):
    """
    Given the bytearray of the file:
    - extract all the segments into a dictionary
    - data[id] = [entity bytesize, array_of_entities]
    """
    datastart = unpack('>H', contents[0:2])[0]
    colors = read_colors(contents[2:datastart+4])
    i = datastart + 4
    data = {}
    while i < len(contents):
        seg_len, label, step = read_segment(contents, i)
        if label in known:
            if verbose:
                print(i, seg_len, "-", label)
                print("       -", contents[i:i+10])
            next = i+4+ (seg_len * step)
            data[label] = [step, contents[i+4:next]]
            i = next
        else:
            print(f"!!FAIL: {i} {seg_len} - '{label}'")
            i += 1
    return data, colors


if __name__ == "__main__":
    # filename = "./WMDF_WIF/W-24point+8borderH-waves.wmdf" # no treadling
    filename = "./WMDF_WIF/W-24point+8borderH-waves_ctest.wmdf"
    # filename = "./WMDF_WIF/col-01.wmdf"
    # filename = "./WMDF_WIF/col-02.wmdf"
    # filename = "./WMDF_WIF/col-03.wmdf"
    # filename = "./WMDF_WIF/straight8-pointTreadle.wmdf"  # tieup u
    # filename = "./WMDF_WIF/0-doubleweave.wmdf"  # no treadling
    # filename = "./WMDF_WIF/0-doubleweave_col.wmdf"  # no treadling
    # filename = "./WMDF_WIF/AVL 1080x210 80 EPI-2.wmd"
    # filename = "./WMDF_WIF/French Twill 14x14.wmdf"
    # filename = "./WMDF_WIF/Peter Straus Request.wmdf"
    # filename = "./WMDF_WIF/plainweave.wmdf"
    # filename = "./WMDF_WIF/Untitled-3.wmdf"  # treadling r
    # filename = "./WMDF_WIF/colortest.wmdf"
    # filename = "./WMDF_WIF/colortest2.wmdf"  #fail 8x8 = 8x9
    # filename = "./WMDF_WIF/morethan32-01.wmdf"
    # filename = "./WMDF_WIF/morethan32-02-40.wmdf"
    # filename = "./WMDF_WIF/morethan32-03-36.wmdf"
    # filename = "./WMDF_WIF/morethan32-04-120.wmdf"
    # filename = "./WMDF_WIF/taw-normal.wmd"
    # filename = "./WMDF_WIF/taw-color.wmd"
    # filename = "./WMDF_WIF/epi_ppi.wmd"
    contents = read_weavemaker(filename)
    data, colors = parse_wmdf(contents)
    w = WMDF(data, colors, filename)
    print()
    print("\n".join(w.report_fstructure()))
    print("\n".join(w.report_summary()))
    if w.conversion_notes:
        print("\n".join(w.report_conversion_notes()))
    if w.warnings:
        print("\n".join(w.report_warning()))
    print(w)
    # make wif
    w.make_wif(0)  # choose first colorway
    w.save_wif()   # colorway index

# Note:
# - get rest of colors into palette
# - report