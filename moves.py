from array import array
from utils import zlog
import itertools
from const import *
from butils import *

class MoveGen():
    @classmethod
    def GetMoves(cls, zboard, onlyLegal=False):

        #TODO: was modifying these functions to be generators (they are only half done)
        moves = []
        moves = moves + list(cls.Pawns(zboard))
        moves = moves + cls.Knights(zboard)
        moves = moves + list(cls.Bishops(zboard))
        moves = moves + cls.Rooks(zboard)
        moves = moves + cls.Queens(zboard)
        moves = moves + cls.Kings(zboard)
        moves = moves + cls.Castling(zboard)
        return moves
    
    @staticmethod
    def GetMoveGen(zboard, onlyLegal=False, isOpColor=False):
        moves = []
        funcs = [lambda: MoveGen.Queens(zboard, isOpColor=isOpColor),
            lambda: MoveGen.Rooks(zboard, isOpColor=isOpColor),
            lambda: MoveGen.Bishops(zboard, isOpColor=isOpColor),
            lambda: MoveGen.Knights(zboard, isOpColor=isOpColor),
            lambda: MoveGen.Pawns(zboard, isOpColor=isOpColor),
            lambda: MoveGen.Kings(zboard, isOpColor=isOpColor),
            lambda: MoveGen.Castling(zboard, isOpColor=isOpColor)]
        for f in funcs:
            moves = f()
            for move in moves:
                yield move

    @staticmethod
    def Pawns(zboard, isOpColor=False):
        color = zboard.color if not isOpColor else 1 - zboard.color
        opColor = 1 - color
        backRank = 7 - color * 7
        
        positions = ToSquares(zboard.pieceBoards[color][PAWN])
        for srcCoord in positions:
            #single push
            snglePush = False 
            spBoard = PawnPushTable[color][srcCoord[0]][srcCoord[1]]
            if not zboard.board & spBoard:
                snglePush = True
                spCoord = ToSquares(spBoard)[0]
                
                if spCoord[1] == backRank: #promotion
                    for promPiececlass in [KNIGHT, BISHOP, ROOK, QUEEN]:
                        meta = 0b1000 | promPiececlass - 1
                        mInfo = MoveInfo.From8x8(srcCoord, spCoord, PAWN, EMPTY, meta)
                        yield mInfo.ToInt32()
                else:
                    mInfo = MoveInfo.From8x8(srcCoord, spCoord, PAWN, EMPTY, QUIET_MOVE)
                    yield mInfo.ToInt32()
             
            #double push
            if snglePush:
                dpBoard = PawnDoublePushTable[color][srcCoord[0]][srcCoord[1]]
                if dpBoard and not zboard.board & dpBoard:
                    destCoord = ToSquares(dpBoard)[0]
                    mInfo = MoveInfo.From8x8(srcCoord, destCoord, PAWN, EMPTY, DOUBLE_PAWN_PUSH)
                    yield mInfo.ToInt32()
            
            #threats
            capBoard = PawnCapturingTable[color][srcCoord[0]][srcCoord[1]] & zboard.teamBoards[opColor]
            if capBoard > 0:
                capCoords = ToSquares(capBoard)
                if capCoords[0][1] == backRank: #if promoting
                    for coord in capCoords:
                        capColor, capClass = TypeToTupleColorClass[zboard.squares[coord[0]][coord[1]]] 
                        if not capClass != EMPTY: pdb.set_trace()
                        for promPiececlass in [KNIGHT, BISHOP, ROOK, QUEEN]:
                            meta = 0b1100 | promPiececlass - 1
                            mInfo = MoveInfo.From8x8(srcCoord, coord, PAWN, capClass, meta)
                            yield mInfo.ToInt32()
                        
                else:
                    for coord in capCoords:
                        capColor, capClass = TypeToTupleColorClass[zboard.squares[coord[0]][coord[1]]]
                        assert capClass != EMPTY
                        mInfo = MoveInfo.From8x8(srcCoord, coord, PAWN, capClass, CAPTURE)
                        yield mInfo.ToInt32()

        #enpassant
        if zboard.enpassant:
            from console import BBoardToString
            adv = 1 - 2 * color #if white 1, if black -1 
            epBoard = CanEnPassantTable[color][zboard.enpassant]
            #zlog.log( BBoardToString(epBoard))
            epBoard &= zboard.pieceBoards[color][PAWN]
            #zlog.log( BBoardToString(epBoard))
            epCoords = ToSquares(epBoard)

            for epCoord in epCoords:
                mInfo = MoveInfo.From8x8(epCoord, (zboard.enpassant, epCoord[1] + adv) , PAWN, EMPTY, EP_CAPTURE)
                yield mInfo.ToInt32()
        
    @staticmethod
    def Bishops(zboard, isOpColor=False):
        color = zboard.color if not isOpColor else 1 - zboard.color
        opColor = 1 - color
        positions = ToSquares(zboard.pieceBoards[color][BISHOP])
        for pos in positions:
            moves = MoveGen.DiagRayAttack(zboard, pos, BISHOP)
            for move in moves:
                yield move
    
    @staticmethod
    def Knights(zboard, isOpColor=False):
        color = zboard.color if not isOpColor else 1 - zboard.color
        opColor = 1 - color
        kSquares = ToSquares(zboard.pieceBoards[color][KNIGHT])
        moves = []
        for kSquare in kSquares:        
            destsBB = knight_map[kSquare[0]][kSquare[1]]
            destsSq = ToSquares(destsBB)
            for destSq in destsSq:
                dType = zboard.squares[destSq[0]][destSq[1]]
                
                pColor, dPiececlass = TypeToTupleColorClass[dType]
                if pColor != color:
                    meta = QUIET_MOVE
                    if pColor == opColor:
                        meta = CAPTURE
                    moveInfo = MoveInfo.From8x8(kSquare, destSq, KNIGHT, dPiececlass, meta)
                    yield moveInfo.ToInt32()

    @staticmethod
    def Rooks(zboard, isOpColor=False):
        moves = []
        color = zboard.color if not isOpColor else 1 - zboard.color
        opColor = 1 - color
        rSquares = ToCoords(zboard.pieceBoards[color][ROOK])
        for rSquare in rSquares:
            moves = moves + MoveGen.LineRayAttack(zboard, rSquare, ROOK) 
        return moves 
    
    @staticmethod
    def Queens(zboard, isOpColor=False):
        moves = []
        color = zboard.color if not isOpColor else 1 - zboard.color
        opColor = 1 - color
        positions = ToCoords(zboard.pieceBoards[color][QUEEN])
        for qPos in positions:
            moves = moves + MoveGen.LineRayAttack(zboard, qPos, QUEEN)
            moves = moves + MoveGen.DiagRayAttack(zboard, qPos, QUEEN)
        return moves
            
    @staticmethod
    def Kings(zboard, isOpColor=False):
        #these moves could be put into a table
        moves = []
        color = zboard.color if not isOpColor else 1 - zboard.color
        opColor = 1 - color
        #pdb.set_trace() 
        pos = ToCoords(zboard.kings[color])[0]
        
        dels = list(itertools.product([-1, 0, 1,],[-1, 0, 1]))
        dels.remove((0,0))
        for fDel, rDel in dels:
            dest = (pos[0] + fDel, pos[1] + rDel)
            if not IsLegalCoord(dest): continue
            destType = zboard.squares[dest[0]][dest[1]]
            destColor, destClass = TypeToTupleColorClass[destType]
            if destType == EMPTY:
                mInfo = MoveInfo.From8x8(pos, dest, KING, EMPTY, QUIET_MOVE)
                moves.append(mInfo.ToInt32())
            elif destColor == opColor:
                mInfo = MoveInfo.From8x8(pos, dest, KING, destClass, CAPTURE)
                moves.append(mInfo.ToInt32())
        return moves
    
    @staticmethod
    def Castling(zboard, isOpColor=False):
        moves = []
        color = zboard.color if not isOpColor else 1 - zboard.color
        opColor = 1 - color
        qSide, kSide = False,False
        if color == WHITE:
            if zboard.castling & W_OO:
                kSide = True
            if zboard.castling & W_OOO:
                qSide = True
        if color == BLACK:
            if zboard.castling & B_OO:
                kSide = True
            if zboard.castling & B_OOO:
                qSide = True
        if not (qSide or kSide): return
        
        betQSBBoard = BetweenQSCastleBBoards[color]
        betKSBBoard = BetweenKSCastleBBoards[color]
        qSide = qSide and (betQSBBoard & zboard.board) == 0
        kSide = kSide and (betKSBBoard & zboard.board) == 0
        #qSide = qSide and betQSBBoard & zboard.teamBoards[color]
        #kSide = kSide and betKSBBoard & zboard.teamBoards[color]

        qSidePos = BetweenQSCastlePositions[color] if qSide else []
        kSidePos = BetweenKSCastlePositions[color] if kSide else []

        #
        #   Iterate through blacks attacks and return as soon as we know that we can't castle
        #   Note: this could be much more efficient
        #
        i=0
        func = [
                lambda qSidePos, kSidePos: MoveGen.doesViolateCastle(MoveGen.Pawns(zboard, True), qSidePos, kSidePos), 
                lambda qSidePos, kSidePos: MoveGen.doesViolateCastle(MoveGen.Knights(zboard, True), qSidePos, kSidePos), 
                lambda qSidePos, kSidePos: MoveGen.doesViolateCastle(MoveGen.Bishops(zboard, True), qSidePos, kSidePos), 
                lambda qSidePos, kSidePos: MoveGen.doesViolateCastle(MoveGen.Rooks(zboard, True), qSidePos, kSidePos), 
                lambda qSidePos, kSidePos: MoveGen.doesViolateCastle(MoveGen.Kings(zboard, True), qSidePos, kSidePos), ]
        while (qSide or kSide) and i < 5:
            _qSide, _kSide = func[i](qSidePos, kSidePos)
            qSide = qSide and _qSide
            kSide = kSide and _kSide
            i+=1
        
        if qSide:
            srcDest = QSCastleKingSourceDest[zboard.color]
            mInfo = MoveInfo(srcDest[0], srcDest[1], KING, EMPTY, QUEEN_CASTLE)
            yield mInfo.ToInt32()
        if kSide:
            srcDest = KSCastleKingSourceDest[zboard.color]
            mInfo = MoveInfo(srcDest[0], srcDest[1], KING, EMPTY, KING_CASTLE)
            yield mInfo.ToInt32()
    #def __init__(self, origin64, dest64, oPiececlass, dPiececlass, metaConstant):

    @staticmethod
    def doesViolateCastle(moves, qSidePos, kSidePos):
        qSide, kSide = False, False
        if qSidePos: qSide = True
        if kSidePos: kSide = True

        kSideSet = set(map(lambda pos: tbl8x8To64[pos[0]][pos[1]], kSidePos))
        qSideSet = set(map(lambda pos: tbl8x8To64[pos[0]][pos[1]], qSidePos))
        for move in moves:
            mInfo = MoveInfo.FromInt32(move)
            if mInfo.dest64 in kSideSet:
                kSide = False
                if not qSide: return False, False
            if mInfo.dest64 in qSideSet:
                qSide = False
                if not kSide: return False, False
        return qSide, kSide
        
    @staticmethod
    def LineRayAttack(zboard, srcPos, srcPiececlass, isOpColor=False):
        #Along file
        color = zboard.color if not isOpColor else 1 - zboard.color
        opColor = 1 - color
        f,r = srcPos
        moves = MoveGen.rayAttacks(zboard, srcPos, srcPiececlass, FileSquares[f][r+1:]) # positive
        rev = FileSquares[f][:max(0, r-1)+1]
        rev.reverse()
        moves = moves + MoveGen.rayAttacks(zboard, srcPos, srcPiececlass, rev) # negative
        
        #Along rank
        moves = moves + MoveGen.rayAttacks(zboard, srcPos, srcPiececlass, RankSquares[r][f+1:])
        rev = RankSquares[r][:max(0, f-1)+1]
        rev.reverse()
        moves = moves + MoveGen.rayAttacks(zboard, srcPos, srcPiececlass, rev)

        return moves

    @staticmethod
    def DiagRayAttack(zboard, srcPos, srcPiececlass, isOpColor=False):
        color = zboard.color if not isOpColor else 1 - zboard.color
        opColor = 1 - color
        #Diag
        diagSq = DiagSquares[srcPos[0]][srcPos[1]]

        i = diagSq.index(srcPos)
        moves = MoveGen.rayAttacks(zboard, srcPos, srcPiececlass, diagSq[i+1:])
        rev = diagSq[:max(0, i-1)+1]
        rev.reverse()
        moves = moves + MoveGen.rayAttacks(zboard, srcPos, srcPiececlass, rev)

        #from console import MoveListToString
        #print MoveListToString(moves, caption=str(srcPos) + 'diag')
        #pdb.set_trace()
        
        #Anti Diag
        diagSq = AntiDiagSquares[srcPos[0]][srcPos[1]]
        i = diagSq.index(srcPos)
        moves = moves + MoveGen.rayAttacks(zboard, srcPos, srcPiececlass, diagSq[i+1:])
        rev = diagSq[:max(0, i-1)+1]
        rev.reverse()
        moves = moves + MoveGen.rayAttacks(zboard, srcPos, srcPiececlass, rev)
        
        #from console import MoveListToString
        #print MoveListToString(moves, caption=str(srcPos) + 'antidiag')
        #pdb.set_trace()

        return moves

    @staticmethod
    def rayAttacks(zboard, srcPos, srcPiececlass, destPositions, isOpColor=False):
        color = zboard.color if not isOpColor else 1 - zboard.color
        opColor = 1 - color
        moves = []
        for destPos in destPositions:
            dPiecetype = zboard.squares[destPos[0]][destPos[1]]

            if dPiecetype == EMPTY:
                mInfo = MoveInfo.From8x8(srcPos, destPos, srcPiececlass, EMPTY, QUIET_MOVE)
                moves.append(mInfo.ToInt32())
            elif TypeToColor(dPiecetype) == color:
                break
            else:
                pClass = TypeToTupleColorClass[dPiecetype][1]
                mInfo = MoveInfo.From8x8( srcPos, destPos, srcPiececlass, pClass, CAPTURE)
                moves.append(mInfo.ToInt32())
                break

        
        #from console import CoordListToString, MoveListToString, MakeColumns
        #s = [
        #    CoordListToString(destPositions, caption=str(srcPos)), 
        #    MoveListToString(moves, caption=str(srcPos))
        #    ]
        #print MakeColumns(s) 
        #pdb.set_trace()
        return moves
    @staticmethod
    def IsChecked(zboard):
        '''
        Diags
            Get opColor pieces in each diag, for each ray
            If no piece intervenes between diag attacking piece and king, checked
        Ranks - same
        Files - same
        Knights
            Generate king-centric knight attack maps
        Pawn attack
            Get opColor pawns in appropriate rank

        '''

#   Move meta info constants
#
QUIET_MOVE              = 0b0000
DOUBLE_PAWN_PUSH        = 0b0001
KING_CASTLE             = 0b0010
QUEEN_CASTLE            = 0b0011

CAPTURE                 = 0b0100 
EP_CAPTURE              = 0b0101 

KNIGHT_PROMOTION        = 0b1000
BISHOP_PROMOTION        = 0b1001
ROOK_PROMOTION          = 0b1010
QUEEN_PROMOTION         = 0b1011

KNIGHT_PROMO_CAPTURE    = 0b1100
BISHOP_PROMO_CAPTURE    = 0b1101
ROOK_PROMO_CAPTURE      = 0b1110
QUEEN_PROMO_CAPTURE     = 0b1111
class MoveInfo:
    def __init__(self, origin64, dest64, oPiececlass, dPiececlass, metaConstant):
        self.origin64 = origin64
        self.dest64 = dest64
        self.oPiececlass = oPiececlass
        self.dPiececlass = dPiececlass
        self.meta = metaConstant

        if self.meta & 0b0100 == 0 and not self.meta & 0b0101 == 1:
            if dPiececlass != EMPTY: pdb.set_trace()

    @property
    def origin8x8(self):
        return tbl64To8x8[self.origin64]
    
    @property
    def dest8x8(self):
        return tbl64To8x8[self.dest64]
    @property
    def metastr(self):
        return MoveMetaInfoStrings[self.meta]
    
    @property
    def int32(self):
        return MoveInfo.ToInt32(self)

    def ToInt32 (self):
        r = (self.meta << 24) | \
        (self.dPiececlass << 20) | \
        (self.oPiececlass << 16) | \
        (self.dest64 << 8) | \
        (self.origin64)
        return r

    @staticmethod
    def FromInt32 (move32):
        source = move32 & 0xff
        _m = move32 >> 8

        dest = _m & 0xff
        _m = _m >> 8

        opiece = _m & 0xf
        _m = _m >> 4

        dpiece = _m & 0xf
        _m = _m >> 4

        meta = _m & 0xf
        return MoveInfo(source, dest, opiece, dpiece, meta)

    @staticmethod
    def From8x8(origin8x8, dest8x8, oPiececlass, dPiececlass, meta):
        return MoveInfo(tbl8x8To64[origin8x8[0]][origin8x8[1]], \
        tbl8x8To64[dest8x8[0]][dest8x8[1]], \
        oPiececlass, \
        dPiececlass, \
        meta)
        
        """ 
        origin64 = tbl8x8To64[origin8x8[0]][origin8x8[1]]
        dest64 = tbl8x8To64[dest8x8[0]][dest8x8[1]]
        oPiececlass = oPiececlass
        dPiececlass = dPiececlass
        meta = metaConstant
        """
  
    def GetPromotedPiececlass (self):
        pflag = self.meta & 0b11
        return pflag + 1 
    
    @staticmethod
    def SortMovesByPiece(moves):
        #creating two lists can be optimized
        moves = [ MoveInfo.FromInt32(move) for move in moves ]
        moves.sort(None, key=lambda info: info.oPiececlass)
        return [ move.ToInt32() for move in moves]
    
    @staticmethod
    def CoordToPGN(coord):
        coordPGNMapping = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        return coordPGNMapping[coord[0]] + str(coord[1] + 1)
        

    def ToPGN(self, color=-1):
        dash = '-'
        prom = ''
        if self.meta == KING_CASTLE:
            return "O-O"
        elif self.meta == QUEEN_CASTLE:
            return "O-O-O"
        
        if self.meta & 0b1000 != 0: #promotion
            pClass = self.meta & 0b11
            prom = '=' + PiecePGNStringDict[pClass]
        
        if self.meta & 0b100 != 0: #capture
            if self.dPiececlass != EMPTY:
                dash = 'x' + PiecePGNStringDict[self.dPiececlass]
            else:
                dash = 'x'

        src = PiecePGNStringDict[self.oPiececlass] + MoveInfo.CoordToPGN(self.origin8x8)
        dst = MoveInfo.CoordToPGN(self.dest8x8) + prom
        
        if color != -1:
            if color == WHITE:
                src = src.upper()
                dst = dst.upper()
                dash = dash[0] + dash[1:].upper()
            elif color == BLACK:
                src = src.lower()
                dst = dst.lower()
                dash = dash[0] + dash[1:].lower()
        return ''.join((src, dash, dst))


    def ToCECPString(self):
        strOrig = MoveInfo.CoordToPGN(self.origin8x8).lower()
        strDest = MoveInfo.CoordToPGN(self.dest8x8).lower()
        
        strProm = ''
        if self.meta & 0x1000 != 0:
            strProm = PiececlassToString[self.GetPromotedPiececlass()].lower()
        return strOrig + strDest + strProm
    
    @staticmethod
    def Int32ToPGN(int32):
        return MoveInfo.FromInt32(int32).ToPGN()
    
    def __str__(self):
        cap = ''
        if self.meta & 0b100 != 0:
            cap = ', capturing %s' % PieceStringDict[self.dPiececlass]
        
        return "%s moves from %s to %s%s (%s)" % \
                                    (PieceStringDict[self.oPiececlass],
                                    str(self.origin8x8), str(self.dest8x8),
                                    cap,
                                    MoveMetaInfoStrings[self.meta])

MoveMetaInfoStrings = {QUIET_MOVE:'QUIET_MOVE', 
     DOUBLE_PAWN_PUSH: 'DOUBLE_PAWN_PUSH',
     KING_CASTLE:'KING_CASTLE',
     QUEEN_CASTLE:'QUEEN_CASTLE',
     CAPTURE: 'CAPTURE',
     EP_CAPTURE:'EP_CAPTURE',
     KNIGHT_PROMOTION: 'KNIGHT_PROMOTION',
     BISHOP_PROMOTION: 'BISHOP_PROMOTION',
     ROOK_PROMOTION: 'ROOK_PROMOTION',
     QUEEN_PROMOTION: 'QUEEN_PROMOTION',
     KNIGHT_PROMO_CAPTURE: 'KNIGHT_PROMO_CAPTURE',
     BISHOP_PROMO_CAPTURE: 'BISHOP_PROMO_CAPTURE',
     ROOK_PROMO_CAPTURE: 'ROOK_PROMO_CAPTURE',
     QUEEN_PROMO_CAPTURE: 'QUEEN_PROMO_CAPTURE'}
