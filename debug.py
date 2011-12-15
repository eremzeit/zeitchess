from const import *
from butils import *
from const import *
from console import *
from moves import *
from board import *
from utils import zlog
import utils
import fen 
import array
import os
import cProfile
import pstats

from pprint import pprint

FEN_Starting = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
FEN_BlackCanCastle = "r1b1k2r/ppp1npb1/2n4p/3BP2q/3P1ppP/2N2N2/PPPB2P1/R2Q2KR b kq - 1 1"
FEN_BlackCanQSCastle = "r3kb1r/ppqn1ppp/4pn2/1B1p1b2/3P4/1Q2PN2/PP1B1PPP/RN2K2R b KQkq - 2 9" # QS can castle
FEN_CapPromo = "r1r3k1/p2P1nbp/1p2N1p1/2p1pb2/8/4BB1P/PP3PP1/2R2RK1 w - - 1 23"
FEN_WhiteCanCastle = "r3kb1r/ppqn1ppp/4pn2/1B1p1b2/3P4/1Q2PN2/PP1B1PPP/RN2K2R w KQkq - 2 9" # white can castle
FEN_BlackBlockingWhitesCastle = "r1bq1rk1/pp1n1ppp/2n1p3/3pP3/5Pb1/2N1B3/PPPQ2PP/R3KB1R w KQkq - 0 1"
FEN_WhiteChecked = "r1bq1rk1/pp1n1ppp/2n1p3/3pP3/5Pb1/2N1B1b1/PPPQ2PP/R3KB1R w KQkq - 0 1" #must block with queen
FEN_WhiteMated = "r1bq1rk1/pp1n1ppp/2n1p3/3pP3/5Pb1/2N1N1b1/PPPB2PP/R3KB1R w KQkq - 0 1"
FEN_WhiteCanEPCap = "rnbqkbnr/1p1ppppp/p7/2pP4/8/8/PPP1PPPP/RNBQKBNR w KQkq c6 0 3"  #on C file from D file
FEN_WhiteCanEPCapTwoWays = "rnbqkbnr/1ppp1ppp/8/3PpP2/p7/8/PPP1P1PP/RNBQKBNR w KQkq e6 0 5"
randomfens = ["r1bq1r2/p4pkp/3p2p1/1p1P4/1Q2n3/5PPP/P4PB1/R3R1K1 w - - 0 21",
                "5rk1/1pNn1pp1/2npb2p/4p3/1PP1P2q/3BP2P/2N1Q1P1/r4RK1 w - - 0 21",
                "rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2",
                "r1b1k2r/ppp1npb1/2n4p/3BP2q/3P1ppP/2N2N2/PPPB2P1/R2Q2KR b kq - 1 1",
                "6r1/2p1k2b/p2b1p1p/P1nPp1r1/1pB5/1P3PP1/R5NP/2N1KR2 w - - 5 24",
                "1k1r3r/1p1bbp2/pq1ppp2/N7/2B1PP1p/2N2R2/PPP3PP/1K1RQ3 b - - 0 19"]
FEN_blackShouldMoveKnight = "rnbqkbr1/pppppppp/7n/6P1/8/PPPPPP1P/8/RNBQKBNR b KQq - 1 11"
FEN_WhiteShouldPromo = "r1r3k1/p2P1nbp/1p2N1p1/2p1pb2/8/4BB1P/PP3PP1/2R2RK1 w - - 1 23"
FEN_WhiteShouldMateWithPawn = "r1bqkbnr/pppppppp/2P5/4NB2/n7/8/PPP1PPPP/RNBQK2R w KQkq - 0 1"
allfens = randomfens + [FEN_BlackCanCastle, FEN_BlackCanQSCastle, FEN_CapPromo, FEN_WhiteCanCastle, FEN_BlackBlockingWhitesCastle, FEN_WhiteChecked, FEN_WhiteMated, FEN_WhiteCanEPCap, FEN_WhiteCanEPCapTwoWays,] 

def main():
    #testRankAndFileCoords()
    #testKnightMap() 
    #testFileRankBBoards()
    #testMakeColumns()
    #testFENImport
    #TestZBoardToFEN()
    #testPawnMoveMaps()
    #testMoveEncoding() 
    #testInitialBoardMoveGen()
    #testMoveGen2()
    #TestEnPassantMoveGen()
    #TestPromoMoveGen()
    #TestCastlingMoveGen()
    #TestMakeUnmakeMove()
    #TestRandomMoves()
    #TestMakeAllMoves()
    #TestRandomMoveSequence()
    #TestAlphaBetaSearch()
    #ProfileAlphaBetaSearch()
    #TestZLog()
    DebugDeepSearch(3, False)

def DebugDeepSearch(d=3, debug=True):
    #todo: improve speed by improving move ordering function.  
    #todo: verify that pruning works in the min function
    #todo: write is_checked
    #todo: modify MoveGen to only gen legal moves
    f = FEN_WhiteShouldMateWithPawn 
    #f = FEN_blackShouldMoveKnight
    print f
    utils.FenToXBoard(f)
    zboard = fen.ZBoardFromFen(f)
    zboard.debug = debug
    res = AlphaBetaSearch(zboard, d)
    print res

def TestZLog():
    zlog.log('aaaa ' * 100)
    zlog.log('bbbb ' * 100)
    zlog.log('1234 ' * 100)
    zlog.log('9876 ' * 100)
    zlog.Flush()

def ProfileAlphaBetaSearch():
    cProfile.run('TestAlphaBetaSearch(d=3)', 'profileout')
    #cProfile.run('TestAlphaBetaSearch(d=4)', 'profileout')
    p = pstats.Stats('profileout') 
    p.sort_stats('cumulative').print_stats()
    
def TestAlphaBetaSearch(d=5):
    zboard = fen.ZBoardFromFen(FEN_blackShouldMoveKnight)
    res = AlphaBetaSearch(zboard, d)
    print res
    if len(res.moveList) != d - 1:
        pdb.set_trace()


def TestRandomMoveSequence():
    import random
    random.seed(0)
    print 'aoue'
    zboard = fen.ZBoardFromFen(FEN_starting)
    firstHash = BDebug.Hash(zboard) 
    
    for run in range(2):
        for i in range(100):
            if run == 0:
                moves = BDebug.RandomMoves(zboard)
                if not moves:
                    print "no moves left"
                    break
                move = moves[random.randint(0,len(moves)-1)]
                zboard.MakeMove(move)
            elif run == 1:
                zboard.UnmakeMove()
    lastHash = BDebug.Hash(zboard)
    print 'aoeu'
    assert firstHash == lastHash
                
def TestMakeAllMoves():
    import random
    random.seed(0)
       
    for j in range(len(allfens)):
        zboard = fen.ZBoardFromFen(allfens[j])
        moves = MoveGen.GetMoves(zboard)
        for i in range(len(moves)):
            testMakeUnmakeMove(zboard, moves[i])

def TestRandomMoves():
    import random
    random.seed(0)
    
    for i in range(20):
        for j in range(len(allfens)):
            #x = random.randint(0,len(allfens) - 1)
            zboard = fen.ZBoardFromFen(allfens[j])
            move = BDebug.RandomMoves(zboard)[i]
            testMakeUnmakeMove(zboard, move)

def TestMakeUnmakeMove():
    zboard = fen.ZBoardFromFen(FEN_pos2)
    #Nc6-b4
    mInfo = MoveInfo.From8x8((2,5), (1,3), KNIGHT, EMPTY, QUIET_MOVE)
    testMakeUnmakeMove(zboard, mInfo.ToInt32())

def testMakeUnmakeMove(zboard, move):
    oldS =  BoardSquaresToString(zboard.squares, caption='START') 
    oHash = BDebug.Hash(zboard)
    
    #print zboard.ToString(True)
    zboard.MakeMove(move)
    
    #print zboard.ToString(True)
    movedS = BoardSquaresToString(zboard.squares, caption='After ' + MoveInfo.Int32ToPGN(move)) 
    #pdb.set_trace() 
    zboard.UnmakeMove()
    
    #print zboard.ToString(True)
    nHash = BDebug.Hash(zboard)
    unmadeS = BoardSquaresToString(zboard.squares, caption='Unmade ' + MoveInfo.Int32ToPGN(move)) 

    if oHash != nHash:
        s = "\n%s\nHashes don't match after make then unmake" % MakeColumns([oldS, movedS, unmadeS])
        print s
        pdb.set_trace()
        raise Exception(s)
    print MoveInfo.FromInt32(move)
    print MakeColumns([oldS, movedS, unmadeS])
    #print BoardSquaresToString(zboard.squares, caption='After %s unmade' % MoveInfo.Int32ToPGN(move)) 

def TestEnPassantMoveGen():
    zboard = fen.ZBoardFromFen(FEN_WhiteCanEPCapTwoWays)
    pdb.set_trace()
    moves = MoveGen.GetMoves(zboard)
    ep_moves = filter(lambda m: m.meta == EP_CAPTURE, [ MoveInfo.FromInt32(move) for move in moves])
    assert len(ep_moves) == 2
    
    print 'ep moves:'
    for move in ep_moves:
        print move
        testMakeUnmakeMove(zboard, move.int32)

def TestPromoMoveGen():
    zboard = fen.ZBoardFromFen(FEN_CapPromo)
    moves = MoveGen.GetMoves(zboard)
    promoMoves = filter(lambda m: m.meta & 0b1100 == 0b1100, [ MoveInfo.FromInt32(move) for move in moves])
    assert len(promoMoves) > 0

    print 'promo moves:'
    for move in promoMoves:
        testMakeUnmakeMove(zboard, move.int32)

def TestCastlingMoveGen():
    zboard = fen.ZBoardFromFen(FEN_BlackCanQSCastle)
    moves = MoveGen.GetMoves(zboard)
    moves = filter(lambda m: m.meta in [KING_CASTLE, QUEEN_CASTLE], [ MoveInfo.FromInt32(move) for move in moves])
    print '---black QS castle:'
    for move in moves:
        testMakeUnmakeMove(zboard, move.int32)


    pdb.set_trace()
    zboard = fen.ZBoardFromFen(FEN_BlackCanCastle)
    moves = MoveGen.GetMoves(zboard)
    moves = filter(lambda m: m.meta in [KING_CASTLE, QUEEN_CASTLE], [ MoveInfo.FromInt32(move) for move in moves])
    print '---black castling moves:'
    for move in moves:
        print move
        testMakeUnmakeMove(zboard, move.int32)

    zboard = fen.ZBoardFromFen(FEN_WhiteCanCastle)
    moves = MoveGen.GetMoves(zboard)
    moves = filter(lambda m: m.meta in [KING_CASTLE, QUEEN_CASTLE], [ MoveInfo.FromInt32(move) for move in moves])
    print '---white castling moves:'
    for move in moves:
        testMakeUnmakeMove(zboard, move.int32)

    zboard = fen.ZBoardFromFen(FEN_BlackBlockingWhitesCastle)
    moves = MoveGen.GetMoves(zboard)
    moves = filter(lambda m: m.meta in [KING_CASTLE, QUEEN_CASTLE], [ MoveInfo.FromInt32(move) for move in moves])
    print '---white has blocked castling:'
    for move in moves:
        testMakeUnmakeMove(zboard, move.int32)

def testMoveGen2():
    zboard = fen.ZBoardFromFen(FEN_pos2)
    testMoveGenerationBreakdown(zboard)

def testInitialBoardMoveGen():
    zboard = fen.ZBoardFromFen(FEN_starting)
    testMoveGenerationBreakdown(zboard)

def testMoveGenerationBreakdown(zboard):
    print BoardSquaresToString(zboard.squares)
    pdb.set_trace()

    _f = [ 
        (lambda: MoveGen.Pawns(zboard), 'Pawns'),
        (lambda: MoveGen.Knights(zboard), 'knights'),
        (lambda: MoveGen.Bishops(zboard), 'Bishops'),
        (lambda: MoveGen.Rooks(zboard), 'Rooks' ),
        (lambda: MoveGen.Queens(zboard), 'Queens'),
        (lambda: MoveGen.Kings(zboard), 'Kings')
        ]
    
    for f in _f[5:]:
        moves = f[0]() 
        print MoveListToString(moves, caption=f[1] + ' moves')
        pdb.set_trace()
    exit()
    #moves = MoveGen.GetMoves(zboard)  

def testMoveEncoding():
    mInfo = MoveInfo.From8x8((5,5), (6,6), PAWN, KNIGHT, QUEEN_PROMOTION)
    print mInfo
    i = mInfo.ToInt32()
    print MoveInfo.FromInt32(i)

def testPawnMoveMaps():
    coords = [(6,4), (1,7), (0,6), (4,0), (7,1)]
    for color in [WHITE, BLACK]:
        colorStr = 'white' if color == WHITE  else 'BLACK'
        for coord in coords:
            strs = []
            c = colorStr + ' single push ' + CoordToPGN(coord)
            strs.append(BBoardToString(PawnPushTable[color][coord[0]][coord[1]], caption=c))
            c = colorStr + ' double push ' + CoordToPGN(coord)
            strs.append(BBoardToString(PawnDoublePushTable[color][coord[0]][coord[1]], caption=c))
            c = colorStr + ' capturing ' + CoordToPGN(coord)
            strs.append(BBoardToString(PawnCapturingTable[color][coord[0]][coord[1]], caption=c))
            print '\n'
            print MakeColumns(strs)
            #pdb.set_trace()
    strs = [] 
    strs.append(BBoardToString(CanEnPassantTable[WHITE][0], caption='white, A file'))
    strs.append(BBoardToString(CanEnPassantTable[WHITE][3], caption='white, D file'))
    strs.append(BBoardToString(CanEnPassantTable[WHITE][7], caption='white, H file'))
    strs.append(BBoardToString(CanEnPassantTable[BLACK][0], caption='black, A file'))
    strs.append(BBoardToString(CanEnPassantTable[BLACK][3], caption='black, D file'))
    strs.append(BBoardToString(CanEnPassantTable[BLACK][7], caption='black, H file'))
    print MakeColumns(strs[:3])
    pdb.set_trace()
    print MakeColumns(strs[3:])
    pdb.set_trace()

def testPERFT():
    pass

def TestZBoardToFEN():
    
    for _fen in allfens:
        zboard = fen.ZBoardFromFen(_fen)
        print 'orig: ' + _fen
        print 'redn: ' + fen.ZBoardToFen(zboard) + '\n'

def testFENImport():
    FEN_pos1 = "rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2"
    FEN_pos2 = "r1b1k2r/ppp1npb1/2n4p/3BP2q/3P1ppP/2N2N2/PPP3P1/R1BQ2KR w kq - 0 12"
    FEN_pos3 = "6r1/2p1k2b/p2b1p1p/P1nPp1r1/1pB5/1P3PP1/R5NP/2N1KR2 w - - 5 24"
    
    zboard = fen.ZBoardFromFen(FEN_pos2)
    print BoardSquaresToString(zboard.squares)
    pdb.set_trace()
    
    zboard = fen.ZBoardFromFen(FEN_pos3)
    print BoardSquaresToString(zboard.squares)
    pdb.set_trace()

def testMakeColumns():
    strs = [
    """Fish, especially as food, are an important resource worldwide. Commercial and subsistence fishers hunt fish in wild fisheries (see fishing) or farm them in ponds or in cages in the ocean (see aquaculture). They are also caught by recreational fishers, kept as pets, raised by fishkeepers, and exhibited in public aquaria. Fish have had a role in culture through the ages, serving as deities, religious symbols, and as the subjects of art, books and movies.
    """,
    """Most fish are "cold-blooded", or ectothermic, allowing their body temperatures to vary as ambient temperatures change. Fish are abundant in most bodies of water. They can be found in nearly all aquatic environments, from high mountain streams (e.g., char and gudgeon) to the abyssal and even hadal depths of the deepest oceans (e.g., gulpers and anglerfish). At 32,000 species, fish exhibit greater species diversity than any other class of vertebrates.[1] 
    """,
    """A fish is any gill-bearing aquatic vertebrate (or craniate) animal that lacks limbs with digits. Included in this definition are the living hagfish, lampreys, and cartilaginous and bony fish, as well as various extinct related groups. Because the term is defined negatively, and excludes the tetrapods (i.e., the amphibians, reptiles, birds and mammals) which descend from within the same ancestry, it is paraphyletic. The traditional term pisces (also ichthyes) is considered a typological, but not a phylogenetic classification. 
    """]
    print MakeColumns(strs)
    pdb.set_trace()
    
def testFileRankBBoards():
    PrintBBoard(FileBitboards[0], "A file")
    PrintBBoard(FileBitboards[3], "D file")

    PrintBBoard(RankBitboards[0], "1st rank")
    PrintBBoard(RankBitboards[4], "5th rank")
    PrintBBoard(RankBitboards[5], "6th rank")
    PrintBBoard(RankBitboards[7], "8th rank")

def testKnightMap():
    print "knight on A2: "
    PrintBBoard(knight_map[0][1])
    
    print "knight on H4: "
    PrintBBoard(knight_map[7][3])
    
    print "knight on D5: "
    PrintBBoard(knight_map[3][4])
    pdb.set_trace()

def testRankAndFileCoords():
    print "File squares (A file):"
    PrintCoordList(FileSquares[0])

    print "File squares (D file):"
    PrintCoordList(FileSquares[3])

    print "File squares (H file):"
    PrintCoordList(FileSquares[7])

    print "Rank squares (1st rank):"
    PrintCoordList(RankSquares[0])

    print "Rank squares (4st rank):"
    PrintCoordList(RankSquares[3])

    print "Rank squares (8st rank):"
    PrintCoordList(RankSquares[7])
    
    pdb.set_trace()
    
def Untested():
    print "\n\n"
    pdb.set_trace()

if __name__ == "__main__":
    main()
#xboard -fcp "./crafty" -fd crafty_directory
