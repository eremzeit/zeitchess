import itertools
from utils import zlog
from pprint import pprint
import pdb
import copy

def MultiDimList(sizes, func=lambda: None,_i=0):
    if _i < len(sizes) - 1:
        item = MultiDimList(sizes, func, _i+1)
    else:
        item = func()
    return [ copy.deepcopy(item) for x in xrange(sizes[_i]) ]

pdb.set_trace()

#
#   Colors
#
WHITE = 0
BLACK = 1

ColorStringDict = {WHITE: 'White', BLACK: 'Black'}

###################
#   Piece classes and types
###################

#There are six piece classes
PAWN = 0x00
KNIGHT = 0x01
BISHOP = 0x02
ROOK = 0x03
QUEEN = 0x04
KING = 0x05
EMPTY = 0XF

W_PAWN, W_KNIGHT, W_BISHOP, W_ROOK, W_QUEEN, W_KING = tuple(range(0,6))
B_PAWN, B_KNIGHT, B_BISHOP, B_ROOK, B_QUEEN, B_KING = tuple(range(6,12))

PieceStringDict = {PAWN: 'PAWN', KNIGHT:'KNIGHT', BISHOP:'BISHOP', ROOK:'ROOK', QUEEN:'QUEEN', KING:'KING', EMPTY:'EMPTY'}
PiecePGNStringDict = {PAWN: 'P', KNIGHT:'N', BISHOP:'B', ROOK:'R', QUEEN:'Q', KING:'K'}

PieceClasses = [PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING]
PieceColorClassTuples = list(itertools.product([WHITE, BLACK], PieceClasses))
#PieceColorClassTuples = MultiDimList((2,15))
#PieceColorClassTuples[WHITE][:7] = 

#and 12 pieceTypes...
TypeToTupleColorClass = MultiDimList((16,))
for i in range(0,12):
    TypeToTupleColorClass[i] = (i/6, i%6)
TypeToTupleColorClass[EMPTY] = (-1, EMPTY)

TupleColorClassToType = [[ 6 * color + piece for piece in PieceClasses ] for color in [WHITE, BLACK]]


def TypeToColor(pieceType):
    if pieceType <= 5: return WHITE
    return BLACK

###############################
#   Castling availability
###############################
W_OOO = 0b0001
W_OO = 0b0010
B_OOO = 0b0100
B_OO = 0b1000

FEN_starting = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

#
#   CHESS VARIANTS
#
STANDARD_CHESS = 0
CHESS_960 = 1


############################
#       coords
############################

FileStrToFile = {
    'a': 0,
    'b': 1,
    'c': 2,
    'd': 3,
    'e': 4,
    'f': 5,
    'g': 6,
    'h': 7
}

RankStrToRank = {
    '1': 0,
    '2': 1,
    '3': 2,
    '4': 3,
    '5': 4,
    '6': 5,
    '7': 6,
    '8': 7,
}

