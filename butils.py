from const import *
from utils import zlog

import pdb
import copy
from pprint import pprint
import random
from array import array

tbl64To8x8 = [(x%8,x/8) for x in xrange(64)]
tbl8x8To64 = [ [f + r*8 for r in xrange(8)] for f in xrange(8) ]

EmptyBoard = MultiDimList((8,8))

def CreateBoard(number):
    return number

def _bitCount(num):
    count = 0
    mask = 0b0001
    for i in xrange(64):
        if num & mask << i:
            count += 1
    return count

popCountOfByte = MultiDimList((256,))
for i in xrange(0,256):
    popCountOfByte[i] = _bitCount(i)
popCountOfByte = array('B', popCountOfByte)

def bitCount(number):
    if number == 0: return 0
    _n = number
    count = 0
    mask = 0xff
    for i in xrange(8):
        count += popCountOfByte[number & mask]
        number = number >> 8
    if count != _bitCount(_n):
        pdb.set_trace()
    return count
         
def To64(coord):
    return tbl8x8To64[coord[0]][coord[1]]

def To8x8(index64):
    return tbl64To8x8[index64]

#inefficient
def ToSquares(bboard):
    """
        Arguments:
            A bit board
        Returns:
            A list of position tuples that correspond to positions that are true in the bitboard
    """
    pos = [] 
    mask = 1
    if not bboard:
        return pos
    for i in xrange(64):
        _r = bboard & BoardBitmasksTable[i]
        if _r:
            pos.append(tbl64To8x8[i])
    return pos

def ToCoords(bboard):
    return ToSquares(bboard)

def ToBBoard(squares): #inefficient
    """
        Arguments:
            squares         --  a list of position tuples
        Returns:
            a bitboard with all of the square positions set to True
    """
    
    bboard = 0
    for s in squares:
        if s[0] < 0 or s[1] < 0:
            print s
            pdb.set_trace()
        bboard = setBitBy8x8(bboard, s, 1)
    return bboard

def setBitBy8x8(bboard, pos, boolean):
    assert pos[0] in xrange(8) and pos[1] in xrange(8)
    return setBit (bboard, pos[1] * 8 + pos[0], boolean)

BoardBitmasksTable = MultiDimList((64,))
for i in xrange(0,64):
    BoardBitmasksTable[i] = 1 << i

def setBit(number, i, boolean):
    if i < 0: pdb.set_trace()
    
    if boolean:
        return number | BoardBitmasksTable[i]
    else:
        return number & ~BoardBitmasksTable[i]
    return number

#of the form e3 to (4, 2)
def CoordStringToCoord(strCoord):
    strCoord = strCoord.strip()
    return (FileStrToFile[strCoord[0]], RankStrToRank[strCoord[1]])

def IsLegalCoord(pos):
    return pos[0] >= 0 and pos[0] < 8 and pos[1] >= 0 and pos[1] < 8

DiagSquares = [ [None for r in xrange(8)] for f in xrange(8)]
for f, r in itertools.product(xrange(8), xrange(8)):
    #delta = range(-7, 8)
    l = []
    for d in xrange(-7, 8):
        pos = (f+d,r+d)
        if IsLegalCoord(pos):
            l.append(pos)
    DiagSquares[f][r] = l

AntiDiagSquares = [ [None for r in xrange(8)] for f in xrange(8)]
for f, r in itertools.product(xrange(8), xrange(8)):
    #delta = xrange(-7, 8)
    l = []
    for d in xrange(-7, 8):
        pos = (f+d,r-d)
        if IsLegalCoord(pos):
            l.append(pos)
    AntiDiagSquares[f][r] = l
    #if f == 4 and r == 2:
    #    pdb.set_trace()
    #    print ''

#FileSquares[3] gives all coords in the D file
FileSquares = [ map(lambda x: (f, x), xrange(8)) for f in xrange(0,8)]
RankSquares = [ map(lambda x: (x, r), xrange(8)) for r in xrange(0,8)]

def _generate_knight_movemap():
    relMoves = filter(lambda x: abs(x[0]) != abs(x[1]), list(itertools.product([-2,-1, 1, 2], [-2,-1, 1, 2])))
    kBoards = MultiDimList((8,8))
    
    for f, r in itertools.product(xrange(8), xrange(8)):
        coords = []
        for relMove in relMoves:
            coord = (f + relMove[0], r + relMove[1])
            if IsLegalCoord(coord):
                coords.append(coord)

        kBoards[f][r] = ToBBoard(coords)
    return kBoards
knight_map = _generate_knight_movemap()

def _generate_file_bitboards():
    #Indexed by file, each bitboard stores occupancy in each file.
    bboard = 0x0101010101010101
    bboards = [bboard]
    for f in xrange(1,8):
        bboard = bboard << 1
        bboards.append(bboard)
    return bboards

FileBitboards = _generate_file_bitboards()
def _generate_rank_bitboards():
    #Indexed by rank, each bitboard stores occupancy in each rank.
    bboard = 0xFF
    bboards = [bboard]
    for f in xrange(1,8):
        bboard = bboard << 8
        bboards.append(bboard)
    return bboards
RankBitboards = _generate_rank_bitboards()

def _generate_line_movemap():
    attackMap = MultiDimList((8,8), 0)
    for f, r in itertools.product(range(8), range(8)):
        attackMap[f][r] = setBitBy8x8(_fileBitboards[f] & _rankBitboards[r], (f,r), 0)
    return attackMap

def _generate_diag_movemap():
    pass

#
#   CASTLING
#
BetweenQSCastlePositions = [
    [   [1,0],
        [2,0],
        [3,0]
    ],
    [
        [1,7],
        [2,7],
        [3,7]
    ]
]   

BetweenKSCastlePositions = [
    [   [5,0],
        [6,0],
    ],
    [
        [5,7],
        [6,7],
    ]
]

BetweenQSCastleBBoards = [
    0b111 << 1,
    0b111 << 57
]

BetweenKSCastleBBoards = [
    0b11 << 5,
    0b11 << 61
]

#bindexes
QSCastleKingSourceDest = (
    (4, 2), (60, 58)
)

KSCastleKingSourceDest = (
    (4, 6), (60, 62)
)

QSCastleRookSourceDest = (
    (0, 4), (56, 59)
)

KSCastleRookSourceDest = (
    (7, 5), (63, 61)
)

#coords
QSCastleKingSourceDestCoord = (
    ((4,0), (2,0)), ((4,7), (2,7))
)

KSCastleKingSourceDestCoord = (
    ((4,0), (6,0)), ((4,7), (6,7))
)

QSCastleRookSourceDestCoord = (
    ((0,0), (3,0)), ((0,7), (3,7))
)

KSCastleRookSourceDestCoord = (
    ((7,0), (5,0)), ((7,7), (5,7))
)

StartingPawnsBBoards = [65280, 71776119061217280]
StartingPawnsPositions = [ ToSquares(StartingPawnsBBoards[WHITE]), ToSquares(StartingPawnsBBoards[BLACK])]

PawnCapturingTable = MultiDimList((2,8,8))
PawnPushTable = MultiDimList((2,8,8))
PawnDoublePushTable = MultiDimList((2,8,8))

for color in [WHITE, BLACK]:
    adv = 1 if color == WHITE else -1
    adv2 = adv * 2
    #backRank = 7 if color == WHITE else 0
    for f,r in itertools.product(range(8), range(8)):
        if r + adv not in range(0,8):
            PawnCapturingTable[color][f][r] = -1
            PawnPushTable[color][f][r] = -1
            PawnDoublePushTable[color][f][r] = -1
            continue
        
        #attacking 
        if f == 0:
            pos = [(f+1,r+adv)]
        elif f == 7:
            pos = [(f-1, r+adv)]
        else:
            pos = [(f+1,r+adv), (f-1, r+adv)]
        PawnCapturingTable[color][f][r] = ToBBoard(pos)
        
        #pushing
        pos = [(f, r+adv)]
        PawnPushTable[color][f][r] = ToBBoard(pos)
        
        #double pushing
        if r == 1 and color == WHITE or color == BLACK and r == 6:
            pos = [(f, r+adv2)]
            PawnDoublePushTable[color][f][r] = ToBBoard(pos)
        else:
            PawnDoublePushTable[color][f][r] = 0

CanEnPassantTable = MultiDimList((2,8)) #indexed by color, file
for color in [WHITE, BLACK]:
    rank = 4 - color #if white 4, if black 3
    for f in xrange(0,8):
        coords = filter(lambda coord: coord[0] in range(0,8), [(f-1, rank),(f+1, rank)])
        CanEnPassantTable[color][f] = ToBBoard(coords)

#############################
#   ZOBRIST HASHING         
#############################

#One number for each piece at each square
#One number to indicate the side to move is black
#Four numbers to indicate the castling rights, though usually 16 (2^4) are used for speed
#Eight numbers to indicate the file of a valid En passant square, if any

ZHash_Pieces = MultiDimList((64 * 12,), lambda: random.randint(0,2**64))
ZHash_Color = random.randint(0,2**64)
ZHash_Castling = MultiDimList((16,), lambda: random.randint(0,2**64))
ZHash_EnPassant = MultiDimList((8,), lambda: random.randint(0,2**64))

def GetPieceZHash(pos64, pType):
    return ZHash_Pieces[pos64 * 12 + pType]
