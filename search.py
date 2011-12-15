import sys
from utils import zlog
from const import *
from moves import *
from datetime import datetime, timedelta
import filepipe

MaxInt = sys.maxint
MinInt = -sys.maxint - 1

lastTime = datetime.now()
nodeCount = 0
failHighCount = 0
failLowCount = 0

branchings = []

debug = True
MaxPlayer = -1

HaltOn_pClass = PAWN
HaltOn_dCoord = (7,5)
HaltOn_oCoord = None
#HaltOn_pClass = KNIGHT
#HaltOn_dCoord = (5,4)


def indent(depth):
    return '.   ' * depth

def iprint(s, depth):
    if depth < 3:
        if debug:
            print indent(depth) + s
        else:
            #zlog.log(indent(depth) + s)
            pass

def AlphaBetaSearch(zboard, cutoffDepth):
    global MaxPlayer
    print 'Searching from the perspective of %s' % zboard.color
    MaxPlayer =  zboard.color
    bestRes = minimax_Max(zboard, MinInt, MaxInt, 0, cutoffDepth, [])
    return bestRes

def haltMinimax(move, curDepth = -1):
    if HaltOn_pClass == None and (HaltOn_oCoord == None or HaltOn_dCoord == None):
        return
    if curDepth <= 0:
        mi = MoveInfo.FromInt32(move)
        #if mi.oPiececlass == PAWN and mi.meta & 0b0100 != 0:
        #    pdb.set_trace()
        if (HaltOn_pClass == None or mi.oPiececlass == HaltOn_pClass):
            if HaltOn_oCoord == None or mi.orig8x8 == tuple(HaltOn_oCoord):
                if HaltOn_dCoord == None or mi.dest8x8 == tuple(HaltOn_dCoord):
                    print str(curDepth),'\n', str(mi)
                    pdb.set_trace()
    
    

def minimax_Max(zboard, alpha, beta, curDepth, cutoffDepth, moveList):
    from fen import ZBoardToFen
    assert zboard.color == MaxPlayer
    assert curDepth % 2 == 0

    if isTerminalState(zboard, curDepth, cutoffDepth):
        score = utility(zboard, curDepth)

        res = ResInfo(score, curDepth, moveList, zboard.color)
        zboard.UnmakeMove()
        return res
    
    maxRes = None
    moveGen = MoveGen.GetMoveGen(zboard)
    #iprint ('moves to process: %s' % len(moveGen), curDepth)
    i = 0
    for move in moveGen:
        if curDepth == 0:
            iprint('%s%% done' % str(i * 100 / 30), curDepth)
        haltMinimax(move, curDepth)
        _moveList = moveList[:] + [move]
        zboard.MakeMove(move)
        #iprint ('%s' % (str(i)), curDepth)
        res = minimax_Min(zboard, alpha, beta, curDepth + 1, cutoffDepth, _moveList)
        i += 1
        
        if res == None: continue
        if res.score >= beta: #fail high
            #pdb.set_trace()
            #iprint('fail high: %s' % (str(res)), curDepth)
            res.score = beta 
            zboard.UnmakeMove()
            return res
        if res.score > alpha:
            #iprint('res: ' + str(res), curDepth)
            maxRes = res
            alpha = res.score
    #maxRes.score = alpha
    if curDepth != 0: zboard.UnmakeMove()
    return maxRes

def minimax_Min(zboard, alpha, beta, curDepth, cutoffDepth, moveList):
    from fen import ZBoardToFen
    try:
        assert 1 - zboard.color == MaxPlayer
        assert curDepth % 2 == 1
    except:
        pdb.set_trace()

    if isTerminalState(zboard, curDepth, cutoffDepth):
        score = -utility(zboard, curDepth)
        res = ResInfo(score, curDepth, moveList, zboard.color)
        zboard.UnmakeMove()
        return res
    
    #iprint ('(min: %s)' % (ZBoardToFen(zboard)), curDepth)
    minRes = None
    moveGen = MoveGen.GetMoveGen(zboard)
    #iprint ('moves to process: %s' % len(moveGen), curDepth)
    i = 0
    for move in moveGen:
        haltMinimax(move, curDepth)
        #iprint (MoveInfo.FromInt32(move).ToPGN(), curDepth)
        _moveList = moveList[:] + [move]
        zboard.MakeMove(move)

        #iprint ('%s' % (str(i)), curDepth)
        res = minimax_Max(zboard, alpha, beta, curDepth + 1, cutoffDepth, _moveList)
        i += 1
        if res == None: continue
        if res.score <= alpha:
            #pdb.set_trace()
            res.score = alpha
            zboard.UnmakeMove()
            return res
        if res.score < beta:
            minRes = res
            beta = res.score
    #minRes.score = beta 
    if curDepth != 0: zboard.UnmakeMove()
    return minRes
    
def isTerminalState(zboard, curDepth, cutoffDepth):
    global nodeCount
    global lastTime
    global failHighCount
    global failLowCount
    global branchings
    
    if datetime.now() - lastTime > timedelta(seconds=1):
        diff = datetime.now() - lastTime
        t = float(diff.microseconds) / 1000000.0 + diff.seconds
        rate = nodeCount / t
        zlog.log('%s nodes per second' % str(rate))
        #zlog.log('ave branching = %s' % str(sum(branchings) / (len(branchings) + 1)))
        #branchings = []
        lastTime = datetime.now()
        nodeCount = 0
    else:
        nodeCount += 1
    if curDepth > cutoffDepth:
        return True
    if zboard.kings[0] == 0 or zboard.kings[1] == 0:
        return True
    return False
    
"""Is the state of the alpha-beta search that is passed down recursively"""
#does the movelist include the move that was made to invoke the calculation of this result?
class ResInfo():
    def __init__(self, score=-1, termDepth=-1, moveList=[], toMove=-1):
        self.score = score
        self.moveList = moveList
        self.termDepth = termDepth
        if len(moveList) % 2 == 0:
            self.firstMoveColor = toMove
        else:
            self.firstMoveColor = 1 - toMove
    def __str__(self):
        s = ''
        color = self.firstMoveColor
        for move in self.moveList:
            s += MoveInfo.FromInt32(move).ToPGN(color) +  ', '
            color = 1 if color == 0 else 0
        return "(%s) [%s]" % (str(self.score), s)

    def _reset(self):
        self.score = -1
        self.moveList = None
        self.depth = -1



  
def _utility(zboard, curDepth):
    u1 = utility(zboard, curDepth)
    u2 = utility2(zboard, curDepth)
    if u1 != u2:
        import console
        print zboard.ToString(True)
        print 'utility: %s, _utility: %s' % (str(u1), str(u))
        for color in [WHITE, BLACK]:
            for pClass in PieceClasses:
                board = zboard.pieceBoards[color][pClass]
                count = bitCount(board)
                print 'piece count for %s: %s' % (console.PiececlassToString[pClass], str(count))
        pdb.set_trace()
    return u1


#Returns the utility from the perspective of the color to move
UtilVals = {PAWN:1, KNIGHT:3, BISHOP:3, ROOK: 5, QUEEN:8, KING:1000}
def utility(zboard, curDepth):
    _sum = 0
    turnColorSign = 1 - 2 * zboard.color 
    for f in xrange(8):
        for r in xrange(8):
            pColor, pClass = TypeToTupleColorClass[zboard.squares[f][r]]
            if pClass == EMPTY: continue
            pieceColorSign = 1 - 2 * pColor
            _sum += UtilVals[pClass] * (pieceColorSign * turnColorSign)
    return _sum

def utility2(zboard, curDepth):
    _sum = 0
    
    turnColorSign = 1 - 2 * zboard.color 
    for color in [WHITE, BLACK]:
        pieceColorSign = 1 - 2 * color
        for pClass in PieceClasses:
            board = zboard.pieceBoards[color][pClass]
            count = bitCount(board)
            _sum +=  (pieceColorSign * turnColorSign) * count  * UtilVals[pClass]
    return _sum

class TEntry():
    def __init__(self, zhash, depth, score):
        self.zhash = zhash
        self.depth = depth
        self.score = score
        
Trans_N = 10000

#Zobrist- or BCH-key, to look whether the position is the right one while probing
#Best- or Refutation move
#Depth (draft)
#Score, either with Integrated Bound and Value or otherwise with
#Type of Node [11]
#PV-Node, Score is Exact
#All-Node, Score is Upper Bound
#Cut-Node, Score is Lower Bound


def quiescenceMinimax_Max(board, prevBoard, isWhite, cutoffDepth, curDepth=0):
    #if quiescence: return null
    pass

def quiescenceMinimax_Min(board, prevBoard, isWhite, cutoffDepth, curDepth=0):
    #if quiescence: return null
    pass
