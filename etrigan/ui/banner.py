"""ETRIGAN startup banner: an original horned-demon face + block-letter wordmark.
Colours are a hellfire palette (gold, ember red, cape blue). Falls back to plain text."""
import shutil

PALETTE = {"gold": "#f2c230", "ember": "#d6301f", "cape": "#2a6fdb", "ash": "#8a8f98"}

# Face: 20 columns x 11 rows.  # skin  K brow  R glowing eye  W fang  B collar
FACE = [
    "   ##          ##   ",
    "  ###          ###  ",
    "  ################  ",
    " ################## ",
    " ##KKKKK####KKKKK## ",
    " ##KRRRK####KRRRK## ",
    " ###KKKK####KKKK### ",
    "  #######KK#######  ",
    "   ###W######W###   ",
    "    ####KKKK####    ",
    "  BBBBBB####BBBBBB  ",
]
FACE_COLOR = {"#": "gold", "K": "ember", "R": "ember", "W": "ash", "B": "cape"}
FACE_GLYPH = {"#": "█", "K": "▓", "R": "░", "W": "▼", "B": "█"}

LETTERS = {
 "e": ["    ","    ",".##.","#..#","####","#...",".###","    ","    "],
 "t": [".#..",".#..","####",".#..",".#..",".#.#","..#.","    ","    "],
 "r": ["    ","    ","#.##","##..","#...","#...","#...","    ","    "],
 "i": ["#"," ","#","#","#","#","#"," "," "],
 "g": ["    ","    ",".###","#..#","#..#",".###","...#","#..#",".##."],
 "a": ["    ","    ",".##.","...#",".###","#..#",".###","    ","    "],
 "n": ["    ","    ","###.","#..#","#..#","#..#","#..#","    ","    "],
}

def wordmark_rows(word="etrigan"):
    rows = []
    for r in range(9):
        line = ""
        for ch in word:
            line += "".join("██" if c == "#" else "  " for c in LETTERS[ch][r]) + "  "
        rows.append(line.rstrip())
    return rows

def face_rows(color=True):
    out = []
    for row in FACE:
        s = ""
        for c in row:
            if c == " ":
                s += " "
            elif color:
                s += f"[{PALETTE[FACE_COLOR[c]]}]{FACE_GLYPH[c]}[/]"
            else:
                s += FACE_GLYPH[c]
        out.append(s)
    return out

def render(width=None, color=True):
    """Wide terminals (>= 92 cols): face beside wordmark. Narrow: wordmark only."""
    width = width or shutil.get_terminal_size((80, 24)).columns
    word = wordmark_rows()
    if color:
        word = [f"[{PALETTE['gold']}]{w}[/]" for w in word]
    if width >= 92:
        face = face_rows(color)
        pad = [""] * ((len(face) - len(word)) // 2 + 1)
        word = pad + word + [""] * (len(face) - len(word) - len(pad))
        return "\n".join(f + "   " + w for f, w in zip(face, word))
    return "\n".join(word)

# Original rhyming taglines in the character's spirit (written for ETRIGAN).
TAGLINES = [
    "Small laptop, big flame - no cloud to blame.",
    "Local and lean, the fastest you've seen.",
    "Offline we run, and the work gets done.",
]

if __name__ == "__main__":
    print(render(width=100, color=False))
