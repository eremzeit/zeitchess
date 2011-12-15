from const import *
from utils import zlog
from butils import *
from moves import MoveInfo
import array

from pprint import pprint


"""
 - - - - - - - -
 - - - - - - - -
 - - - - - - - -
 - - - - - - - -
 - - - - - - - -
 - - - - - - - -
 - - - - - - - -
 - - - - - - - -
"""
PiecetypeToString = ['P', 'N', 'B', 'R', 'Q', 'K', 'p', 'n', 'b', 'r', 'q', 'k', ]
PiececlassToString = ['P', 'N', 'B', 'R', 'Q', 'K']
PieceStringToClass =  {'P':PAWN, 'N':KNIGHT, 'B':BISHOP, 'R':ROOK, 'Q':QUEEN, 'K':KING}

def validateCoordList(coords):
    #coordSet = set(coords)
    #if len(coords) != len(coordSet): raise Exception ("Duplicate squares")

    for coord in coords:
        if not IsLegalCoord(coord):
            raise Exception("Invalid coord: %s" % str(coord))
    return True
    
def BoardSquaresToString(squares, caption=None):
    s = ''
    if caption:
        s += '   ' + caption + '\n'
    for r in range(7,-1,-1):
        rStr = '%s  ' % str(r + 1)
        for f in range(0,8):
            if squares[f][r] == EMPTY:
                rStr += '- '
                continue
            rStr += PiecetypeToString[squares[f][r]] + ' '
        s += rStr + '\n'
    s += '\n   ' + 'A B C D E F G H'
    return s + "\n"

def CoordListToString(coords, caption=None):
    assert validateCoordList(coords)
    s = ''
    if caption:
        s += '   ' + caption + '\n'
    squares = [[ None for a in range(8)] for b in range(8)]
    for coord in coords:
        squares[coord[0]][coord[1]] = 3
    for r in range(7,-1,-1):
        rStr = '%s  ' % str(r + 1)
        for f in range(0,8):
            if squares[f][r] == None:
                rStr += '- '
            else:
                rStr += 'X '
        s += rStr + '\n'
    s += '\n   ' + 'A B C D E F G H'
    return s + "\n\n\n"

def MoveListToString(moves, caption=None):
    dests = [ MoveInfo.FromInt32(move).dest8x8 for move in moves]
    return CoordListToString(dests, caption=caption)


def BBoardToString(bboard, caption=None):
    return CoordListToString(ToSquares(bboard), caption)

def ZBoardBitboardsToString(zboard):
    rows = []
    for color in [WHITE, BLACK]:
        bStrings = [] 
        for pclass in PieceClasses:
            cap = ColorStringDict[color] + ' ' + PieceStringDict[pclass]
            s = BBoardToString(zboard.pieceBoards[color][pclass], caption=cap)
            bStrings.append(s)
        rows.append(bStrings)
    return MakeColumns(rows[WHITE], col_width=20) + '\n\n' + MakeColumns(rows[BLACK], col_width=20)

def MakeColumns(text_streams, col_width=25, colDivText=' | '):
    maxScreenWidth = 160
    
    colsCount = len(text_streams)
    if colsCount * col_width > maxScreenWidth:
        raise Exception('Max col width exceeded: %s' % str(colsCount * col_width))
    
    for streamI in xrange(len(text_streams)):
        lines = text_streams[streamI].split('\n')
        for lineI in xrange(len(lines)):
            line = lines[lineI] 
            
            cutLine = ''
            while len(line) > col_width:
                cutLine += line[:col_width] + colDivText + '\n'
                line = line[col_width:]
            cutLine += line
            lines[lineI] = cutLine
        text_streams[streamI] = '\n'.join(lines)

    max_lines = 0
    for stream in text_streams:
        count = len(stream.split('\n'))
        if count > max_lines:
            max_lines = count
     
    #buf = [[' '] * (col_width * colsCount + colsCount * len(colDivText)) ] * max_lines
    buf = MultiDimList((max_lines,col_width * colsCount + colsCount * len(colDivText)), lambda: ' ')
    #write into larger list buffer
    offset = 0
    for strIdx in xrange(len(text_streams)):
        offset = strIdx * col_width + strIdx * len(colDivText)
        lines = text_streams[strIdx].split('\n')
        for lIdx in xrange(len(lines)):
            line = lines[lIdx]
            for cIdx in xrange(len(line)):
                buf[lIdx][cIdx + offset] = line[cIdx]
   
    s = ''
    #now process buffer
    for line in buf:
        s += ''.join(line) + '\n'
        #s += ' | '.join(buf[y]) + '\n'

    return s

#coordPGNMapping = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
#def CoordToPGN(coord):
#    return coordPGNMapping[coord[0]] + str(coord[1] + 1)
def CoordToPGN(coord):
    return MoveInfo.CoordToPGN(coord)
