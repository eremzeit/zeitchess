import array
import itertools
from const import *
from butils import * 
from moves import *
from search import *
from utils import zlog
import pdb

import random
random.seed(1)

class ZBoard:
    @property
    def sHash(self):
        return self.hash % 1000
    
    """
        Models the full state of the board including meta-information.
    """
    def __init__ (self, variant = 0):
        self.Reset()
        self.variant = variant
    
    @property
    def lastOpStr(self):
        return 'Last Op: %s %s %s' % (self.debug_lastOp[0], ColorStringDict[self.debug_lastOp[2]], str(MoveInfo.FromInt32(self.debug_lastOp[1])))

    def Reset (self):
        #   Bitboards
        self.board = CreateBoard(0) #all pieces
        self.teamBoards = MultiDimList((2,), lambda: CreateBoard(0))  #pieces for each team
        self.pieceBoards = MultiDimList((2,6), lambda: CreateBoard(0))  #pieces for each team
        self.kings = MultiDimList((2,), lambda: CreateBoard(0))  #pieces for each team
        self.squares = MultiDimList((8,8), lambda: EMPTY) #piecetype
        
        #meta
        self.history = []
        self.enpassant = None # specifies the file, an int in range(0,7)
        self.color = WHITE
        self.castling = B_OOO | B_OO | W_OOO | W_OO
        self.hasCastled = [False, False]
        self.fifty = 0

        self.variant = STANDARD_CHESS
        self.hash = 0

        self.debug = False
        self.debug_LastOp = None
    
    def UpdateFromPieceBoards(self,updateSquares=True):
        if self.debug: 
            self._verifyPieceBoardSync()
       
        self.board = sum(self.pieceBoards[0] + self.pieceBoards[1])
        
        self.teamBoards[WHITE] = sum(self.pieceBoards[WHITE])
        self.teamBoards[BLACK] = sum(self.pieceBoards[BLACK])
        self.kings[WHITE] = self.pieceBoards[WHITE][KING]
        self.kings[BLACK] = self.pieceBoards[BLACK][KING]
        if updateSquares:
            self._makeSquaresFromPieceBoards()
        
        if self.debug:
            self._verifyBoardStructure()
    
    def _verifyPieceBoardSync(self):
        from console import BBoardToString, BoardSquaresToString, MakeColumns
            
        loop1 = list(itertools.product ([WHITE, BLACK], PieceClasses))
        loop2 = list(itertools.product ([WHITE, BLACK], PieceClasses))
        for color1, pClass1 in loop1:
            for color2, pClass2 in loop2:
                if color1 == color2 and pClass1 == pClass2: continue
                p1 = self.pieceBoards[color1][pClass1]
                p2 = self.pieceBoards[color2][pClass2]
                if p1 ^ p2 != p1 | p2:
                    pbStr1 = "(%s %s)" % (ColorStringDict[color1], PieceStringDict[pClass1])
                    pbStr2 = "(%s %s)" % (ColorStringDict[color2], PieceStringDict[pClass2])
                    errorBoard = (p1 ^ p2) ^ (p1 | p2)
                    errS = BBoardToString(errorBoard, caption="errored squares")
                    fullS = self.ToString(True)
                    raise Exception("\n%s\n%s\nPieceboards %s and %s are out of sync\n%s" % (fullS, errS, pbStr1, pbStr2, self.lastOpStr))
             

    def _verifyBoardStructure(self):
        from console import BBoardToString, BoardSquaresToString, MakeColumns
        for color in [WHITE, BLACK]:
            for pClass in PieceClasses:
                if self.board | self.pieceBoards[color][pClass] != self.board:
                    c = PieceStringDict[pClass]
                    s = self.ToString(True)
                    #pdb.set_trace()
                    raise Exception("\n%s %s pieceBoard out of sync with main board\n%s\n%s" % (ColorStringDict[color], PieceStringDict[pClass], s, self.lastOpStr ))
                coords = ToCoords(self.pieceBoards[color][pClass])
                for coord in coords:
                    pType = TupleColorClassToType[color][pClass]
                    if self.squares[coord[0]][coord[1]] != pType:
                        c = PieceStringDict[pClass]
                        s = self.ToString(True)
                        #pdb.set_trace()
                        print "\n%s" % (s,)
                        raise Exception("%s %s in bboard not in self.squares\n%s" % \
                            (ColorStringDict[color], PieceStringDict[pClass], str(coord)), self.lastOpStr)

    def _makeBitboardsFromSquares(self):
        for color, pclass in PieceColorTypeTuples:
            pType = TupleColorClassToType[color][pclass]
            
            bboard = 0
            for f, r in itertools.product(xrange(8), xrange(8)):
                if self.squares[f][r] == pType:
                    board = setBit(bboard, tbl8x8To64[f][r], 1)
            self.pieceBoards[color][pclass] = board

        self.teamBoards[WHITE] = reduce(lambda res, n: res & n, self.pieceBoards[WHITE])
        self.teamBoards[BLACK] = reduce(lambda res, n: res & n, self.pieceBoards[BLACK])

        self.board = self.teamBoards[WHITE] & self.teamBoards[BLACK]    
        self.kings[WHITE] = self.pieceBoards[WHITE][KING]
        self.kings[BLACK] = self.pieceBoards[BLACK][KING]

    def _makeSquaresFromPieceBoards(self):
        #def _clear():
        #    positions = ToSquares(~self.board)
        #    for pos in positions:
        #        f,r = pos
        #        self.squares[pos[0]][pos[1]] = EMPTY
        def _clear2():
            for f in xrange(8):
                for r in xrange(8):
                    self.squares[f][r] = EMPTY
        #_clear()
        _clear2()
        for color, piece in PieceColorClassTuples:
            positions = ToSquares(self.pieceBoards[color][piece])
            for pos in positions:
                f, r = pos
                _p = TupleColorClassToType[color][piece]
                self.squares[f][r] = _p

    def getColorPiececlass(self, bIndex):
        for _color in [WHITE, BLACK]:
            for pClass in PieceClasses:
                if self.pieceBoards[color][pClass] & mask:
                    return _color, pClass
        return -1,-1
    
    def getPiececlass(self, bIndex, color):
        mask = BoardBitmasksTable[bIndex]
        for pClass in PieceClasses:
            if self.pieceBoards[color][pClass] & mask:
                return pClass
        return 9999999999
    

    #############################
    #
    #   MAKE MOVE
    # 
    #############################
    #an in-place operation
    def MakeMove(self, move):
        self.debug_lastOp = ('MakeMove', move, self.color)
        opColor = 1 - self.color
        moveInfo = MoveInfo.FromInt32(move)

        oCoord = To8x8(moveInfo.origin64)
        dCoord = To8x8(moveInfo.dest64)
        
        
        oBMask = BoardBitmasksTable[moveInfo.origin64]
        dBMask = BoardBitmasksTable[moveInfo.dest64]
        capPieceClass = -1
        
        bHistory = BoardHistory(self.enpassant, self.castling, self.fifty)

        def _boardState(newEnPassant, newCastling, resetFifty, didCastle, move, capPiececlass):
            #saves into the history the board state BEFORE making the move
            self.SetCastling(newCastling) 
            
            if didCastle:
                self.hasCastled[self.color] = didCastle

            if resetFifty:
                self.fifty = 0
            else:
                self.fifty += 1
            self.SetColor (opColor) 
            self.SetEnPassant(newEnPassant) 

            mInfo = MoveInfo.FromInt32(move)
            #assert (mInfo.meta & 0b0100 == 0) or capPiececlass != -1 or mInfo.meta & EP_CAPTURE != 0
            if not ((mInfo.meta & 0b0100 == 0) or capPiececlass != -1 or mInfo.meta & EP_CAPTURE != 0):
                print mInfo
                pdb.set_trace()
            
            bHistory.nextMove = move
            bHistory.nextCapPiececlass = capPiececlass
            self.history.append(bHistory)
        
        resetFifty = True
        newEnPassant = None
        newCastling = self.castling
        didCastle = False

        if moveInfo.meta & 0b1000 != 0: #PROMOTIONS
            #remove old piece
            oTypeBoard = self.pieceBoards[self.color][moveInfo.oPiececlass]
            oTypeBoard &= ~oBMask
            self.pieceBoards[self.color][moveInfo.oPiececlass] = oTypeBoard
            self.squares[oCoord[0]][oCoord[1]] = EMPTY
            
            #set promoted piece
            newClass = moveInfo.GetPromotedPiececlass()
            dTypeBoard = self.pieceBoards[self.color][newClass]
            dTypeBoard |= dBMask
            self.pieceBoards[self.color][newClass] = dTypeBoard
            self.squares[dCoord[0]][dCoord[1]] = TupleColorClassToType[self.color][newClass]

            #if a capture...
            if moveInfo.meta & 0b0100 != 0:
                capPieceClass = self.getPiececlass(moveInfo.dest64, 1 - self.color)
                board = self.pieceBoards[opColor][capPieceClass]
                board &= ~dBMask
                self.pieceBoards[opColor][capPieceClass] = board
            resetFifty = True

        elif moveInfo.meta in [KING_CASTLE, QUEEN_CASTLE]: #CASTLING
            #assert self.variant == STANDARD_CHESS
            #king
            kingBoard = self.pieceBoards[self.color][KING]
            kingBoard &= ~oBMask
            kingBoard |= dBMask
            self.pieceBoards[self.color][KING] = kingBoard
            
            kOrigCoord = ToSquares(oBMask)[0]
            kDestCoord = ToSquares(dBMask)[0]
            self.squares[kOrigCoord[0]][kOrigCoord[1]] = EMPTY
            self.squares[kDestCoord[0]][kDestCoord[1]] = TupleColorClassToType[self.color][KING]

            #rook
            rookBoard = self.pieceBoards[self.color][ROOK]
            if moveInfo.meta == KING_CASTLE:
                oRookmask = BoardBitmasksTable[KSCastleRookSourceDest[self.color][0]]
                dRookmask = BoardBitmasksTable[KSCastleRookSourceDest[self.color][1]]
                roCoord = KSCastleRookSourceDestCoord[self.color][0]
                rdCoord = KSCastleRookSourceDestCoord[self.color][1]
            elif moveInfo.meta == QUEEN_CASTLE: 
                oRookmask = BoardBitmasksTable[QSCastleRookSourceDest[self.color][0]]
                dRookmask = BoardBitmasksTable[QSCastleRookSourceDest[self.color][1]]
                roCoord = QSCastleRookSourceDestCoord[self.color][0]
                rdCoord = QSCastleRookSourceDestCoord[self.color][1]

            rookBoard &= ~oRookmask
            rookBoard |= dRookmask
            self.pieceBoards[self.color][ROOK] = rookBoard
            try:
                self.squares[roCoord[0]][roCoord[1]] = EMPTY
            except:
                pdb.set_trace()

            self.squares[rdCoord[0]][rdCoord[1]] = TupleColorClassToType[self.color][ROOK]
            
            if self.color == WHITE:
                newCastling = self.castling & ~(W_OOO | W_OO)
            else:
                newCastling = self.castling & ~(B_OOO | B_OO)
            didCastle = True 
            
        elif moveInfo.meta & 0b0100 != 0: #PLAIN CAPTURES
            #move attacking piece
            typeBoard = self.pieceBoards[self.color][moveInfo.oPiececlass]
            typeBoard &= ~oBMask
            typeBoard |= dBMask
            self.pieceBoards[self.color][moveInfo.oPiececlass] = typeBoard
            self.squares[oCoord[0]][oCoord[1]] = EMPTY
            
            if moveInfo.meta == EP_CAPTURE:
                assert self.enpassant != None
                capRank = 4 - self.color #r = 4 if white, 3 if black.... 
                dRank = 5 - 3 * self.color #r = 5 if white, 2 if black.... 
                capdPawnMask = BoardBitmasksTable[To64((self.enpassant, capRank))]
                self.pieceBoards[opColor][PAWN] &= ~capdPawnMask
                self.squares[self.enpassant][capRank] = EMPTY
                self.squares[self.enpassant][dRank] = TupleColorClassToType[self.color][PAWN]
                
            else:
                #remove captured piece
                capPieceClass = moveInfo.dPiececlass
                try:
                    self.pieceBoards[opColor][moveInfo.dPiececlass] &= ~dBMask
                except:
                    pdb.set_trace()
                self.squares[dCoord[0]][dCoord[1]] = TupleColorClassToType[self.color][moveInfo.oPiececlass]
            
        else: #QUIET_MOVE, DOUBLE_PAWN_PUSH
            try:
                typeBoard = self.pieceBoards[self.color][moveInfo.oPiececlass]
            except:
                pdb.set_trace()
            typeBoard &= ~oBMask
            typeBoard |= dBMask
            self.pieceBoards[self.color][moveInfo.oPiececlass] = typeBoard
            self.squares[oCoord[0]][oCoord[1]] = EMPTY
            self.squares[dCoord[0]][dCoord[1]] = TupleColorClassToType[self.color][moveInfo.oPiececlass]
            
            resetFifty = False
            if moveInfo.oPiececlass == PAWN:
                resetFifty = True 
            elif moveInfo.oPiececlass == ROOK:
                if moveInfo.origin64 == 0 and newCastling & W_OOO and self.color == WHITE:
                    newCastling &= ~W_OOO
                if moveInfo.origin64 == 7 and newCastling & W_OO and self.color == WHITE:
                    newCastling &= ~W_OO
                if moveInfo.origin64 == 56 and newCastling & W_OOO and self.color == BLACK:
                    newCastling &= ~B_OOO
                if moveInfo.origin64 == 63 and newCastling & W_OO and self.color == BLACK:
                    newCastling &= ~B_OO
            elif moveInfo.oPiececlass == KING:
                if moveInfo.origin64 == 4 and self.color == WHITE:
                    newCastling &= ~(W_OOO & W_OO)
                if moveInfo.origin64 == 60 and self.color == BLACK:
                    newCastling &= ~(B_OOO & B_OO)

            if moveInfo.meta == DOUBLE_PAWN_PUSH:
                newEnPassant = moveInfo.origin64 % 8 #check for enpassant
            newCastling = self.castling
        
        _boardState(newEnPassant, newCastling, resetFifty, didCastle, move, capPieceClass)
        #zlog.log('Making move: ' + str(moveInfo))
        self.UpdateFromPieceBoards(updateSquares=False)

    
    #############################
    #   UNMAKE MOVE
    #############################
    #an in-place operation
    def UnmakeMove(self):
        self.color = 1 - self.color
        moveColor = self.color
        moveOpColor = 1 - self.color
       
        #REVERT STATE OF BOARD
        history = self.history.pop()
        self.fifty = history.initFifty
        self.enpassant = history.initEnPassant
        self.castling = history.initCastling
        move = history.nextMove
        moveInfo = MoveInfo.FromInt32(move)
        dBMask = BoardBitmasksTable[moveInfo.dest64]
        oBMask = BoardBitmasksTable[moveInfo.origin64]
        
        oCoord = To8x8(moveInfo.origin64)
        dCoord = To8x8(moveInfo.dest64)
        self.debug_lastOp = ('UnmakeMove', move, moveColor)
       
        #UNMOVE PIECES
        if moveInfo.meta & 0b1000 != 0: #promotions
            #move piece back
            typeBoard = self.pieceBoards[moveColor][PAWN]
            typeBoard |= oBMask
            self.pieceBoards[moveColor][PAWN] = typeBoard
            self.squares[oCoord[0]][oCoord[1]] = TupleColorClassToType[self.color][moveInfo.oPiececlass]
            
            #remove promoted piece
            promPClass = moveInfo.GetPromotedPiececlass()
            dTypeBoard = self.pieceBoards[moveColor][promPClass]
            dTypeBoard &= ~dBMask
            self.pieceBoards[moveColor][promPClass] = dTypeBoard
            self.squares[dCoord[0]][dCoord[1]] = EMPTY
            
            #if capture, replace piece
            if moveInfo.meta & 0b0100 != 0:
                capPieceClass = moveInfo.dPiececlass
                if capPieceClass == EMPTY:
                    capPieceClass = BISHOP #HACK!  breaks everything.  figure out why this is == EMPTY
                typeBoard = self.pieceBoards[moveOpColor][capPieceClass]
                    
                typeBoard |= dBMask
                self.pieceBoards[moveOpColor][capPieceClass] = typeBoard
                self.squares[dCoord[0]][dCoord[1]] = TupleColorClassToType[moveOpColor][capPieceClass]
            
        elif moveInfo.meta in [KING_CASTLE, QUEEN_CASTLE]: #castling
            
            #king
            kingBoard = self.pieceBoards[moveColor][KING]
            kingBoard |= oBMask
            kingBoard &= ~dBMask
            self.pieceBoards[moveColor][KING] = kingBoard
            self.squares[dCoord[0]][dCoord[1]] = EMPTY

            #rook
            rookBoard = self.pieceBoards[moveColor][ROOK]
            if moveInfo.meta == KING_CASTLE:
                oRookmask = BoardBitmasksTable[KSCastleRookSourceDest[moveColor][0]]
                dRookmask = BoardBitmasksTable[KSCastleRookSourceDest[moveColor][1]]
                roCoord = KSCastleRookSourceDestCoord[self.color][0]
                rdCoord = KSCastleRookSourceDestCoord[self.color][1]
            elif moveInfo.meta == QUEEN_CASTLE: 
                oRookmask = BoardBitmasksTable[QSCastleRookSourceDest[moveColor][0]]
                dRookmask = BoardBitmasksTable[QSCastleRookSourceDest[moveColor][1]]
                roCoord = QSCastleRookSourceDestCoord[self.color][0]
                rdCoord = QSCastleRookSourceDestCoord[self.color][1]

            rookBoard |= oRookmask
            rookBoard &= ~dRookmask
            self.pieceBoards[moveColor][ROOK] = rookBoard
            self.squares[roCoord[0]][roCoord[1]] = TupleColorClassToType[self.color][ROOK]
            self.squares[rdCoord[0]][rdCoord[1]] = EMPTY
            
            self.squares[oCoord[0]][oCoord[1]] = TupleColorClassToType[self.color][KING] #done after rook to prevent overwriting
            
        elif moveInfo.meta & 0b0100 != 0: #captures
            #unmove attacking piece
            typeBoard = self.pieceBoards[moveColor][moveInfo.oPiececlass]
            typeBoard |= oBMask
            typeBoard &= ~dBMask
            self.pieceBoards[moveColor][moveInfo.oPiececlass] = typeBoard
            self.squares[oCoord[0]][oCoord[1]] = TupleColorClassToType[self.color][moveInfo.oPiececlass]
            
            if moveInfo.meta == EP_CAPTURE:
                capRank = 4 - 1 * moveColor #r = 5th rank if white, 4th rank if black
                capdPawnMask = BoardBitmasksTable[To64((self.enpassant, capRank))]
                self.pieceBoards[moveOpColor][PAWN] |= capdPawnMask
                self.squares[dCoord[0]][dCoord[1]] = EMPTY
                self.squares[self.enpassant][capRank] = TupleColorClassToType[moveOpColor][PAWN]

            else:
                #re-place captured piece
                capPieceClass = moveInfo.dPiececlass
                try:
                    typeBoard = self.pieceBoards[moveOpColor][capPieceClass]
                except:
                    pdb.set_trace()
                typeBoard |= dBMask
                self.pieceBoards[moveOpColor][capPieceClass] = typeBoard
                
                self.squares[dCoord[0]][dCoord[1]] = TupleColorClassToType[moveOpColor][capPieceClass]
            
        else: #QUIET_MOVE, DOUBLE_PAWN_PUSH
            typeBoard = self.pieceBoards[moveColor][moveInfo.oPiececlass]
            typeBoard |= oBMask
            typeBoard &= ~dBMask
            self.pieceBoards[moveColor][moveInfo.oPiececlass] = typeBoard
            self.squares[oCoord[0]][oCoord[1]] = TupleColorClassToType[self.color][moveInfo.oPiececlass]
            self.squares[dCoord[0]][dCoord[1]] = EMPTY
        
        #zlog.log('Unmaking move: ' + str(moveInfo))
        self.UpdateFromPieceBoards(updateSquares=False)
    
    def clone (self):
        copy = ZBoard(self.variant)
        
        copy.board = self.board
        copy.teamBoards = self.teamBoards
        copy.pieceBoards = self.pieceBoards
        copy.kings = self.kings

        copy.enpassant = self.enpassant
        copy.color = self.color
        copy.castling = self.castling
        copy.hasCastled = self.hasCastled
        copy.fifty = self.fifty
        
        return copy
    #def IsChecked (self):
    #    if self.checked == None:
    #        kingpos = self.kings[self.color]
    #        self.checked = isAttacked (self, kingcord, 1-self.color)
    #    return self.checked
#    
#    def opIsChecked (self):
#        raise Exception()
#        if self.opchecked == None:
#            kingcord = self.kings[1-self.color]
#            self.opchecked = isAttacked (self, kingcord, self.color)
#        return self.opchecked

    def AddPiece(self, pos64, pieceType):
        from console import BBoardToString
        color, pClass = TypeToTupleColorClass[pieceType]
        pieceBoard = self.pieceBoards[color][pClass]
        pieceBoard = setBit(pieceBoard, pos64, True)
        self.pieceBoards[color][pClass] = pieceBoard

        self.hash ^= GetPieceZHash(pos64, pieceType)
        self.UpdateFromPieceBoards()

    def RemovePiece(self, pos64):
        subtractBBoard = 1 << pos64 
        for color, pClass in itertools.product( [WHITE, BLACK], PieceClasses) :
            pBoard = self.pieceBoards[color][pClass] 
            if pBoard & subtractBBoard:
                self.pieceBoards[color][pClass] = pBoard & ~substractBBoard
                
                pType = TupleColorClassToType[color][pClass]
                self.hash ^= GetPieceZHash(pos64, pType)
                self.UpdateFromPieceBoards()
                return TupleColorClassToType[color][pClass]

    def SetCastling (self, castling):
        if self.castling == castling: return
        
        self.hash ^= ZHash_Castling[self.castling]
        self.castling = castling
        self.hash ^= ZHash_Castling[castling]
    
    def SetEnPassant (self, f):
        if self.enpassant == f: return
        if self.enpassant != None:
            self.hash ^= ZHash_EnPassant[self.enpassant]
        if f != None:
            self.hash ^= ZHash_EnPassant[f]
        self.enpassant = f
   
    #def Move (self, fcord, tcord, ):
    #    """ Moves the piece at fcord to tcord. """
    #    pType = self.RemovePiece(self, fcord) 
    #    self.AddPiece(self, tcord, pType)
    
    def SetColor (self, color):
        if color == self.color: return
        self.color = color
        self.hash ^= ZHash_Color * self.color

    def ToString(self, full=False):
        from console import BBoardToString, BoardSquaresToString, MakeColumns
        s = ''

        if full:
            s += MakeColumns([BoardSquaresToString(self.squares, caption='squares'),
                            BBoardToString(self.board, caption='board'),
                            BBoardToString(self.teamBoards[WHITE], caption='white teamboard'),
                            BBoardToString(self.teamBoards[BLACK], caption='black teamboard')])

        for color in [WHITE, BLACK]:
            pStr = []
            for pClass in PieceClasses:
                cap = "%s %s" % (ColorStringDict[color], PieceStringDict[pClass])
                pStr.append(BBoardToString(self.pieceBoards[color][pClass], caption=cap))
            s += MakeColumns(pStr) + '\n'
        s += 'hash: ' + str(self.sHash) + '\n'
        return s
    def Hash(self):
        h = 0
        #lambda r * 8 + f, pType: pos64 * 12 + pType
        for f in xrange(0,8):
            for r in xrange(0,8):
                pType = self.squares[f][r]
                if pType != EMPTY:
                    h ^= GetPieceZHash(To64((f,r)), pType)
        h ^= ZHash_Color * self.color
        h ^= ZHash_Castling[self.castling]

        if self.enpassant != None:
            h ^= ZHashEnPassant[self.enpassant]
        self.hash = h
    
    def IsMoveValid(move):
        mInfo = MoveInfo.FromInt32(move)
        
        moves = MoveGen.GetMoves(zboard)
        if move in moves:
            return True
        else:
            return False


    def IsChecked(self):
        if self.checked != None:
            return self.checked


    def InterpretMove(self, fromCoord, toCoord, promoClass = -1):
        srcColor, srcClass = TypeToTupleColorClass[self.squares[fromCoord[0]][fromCoord[1]]]
        destType = self.squares[toCoord[0]][toCoord[1]]

        if destType == EMPTY:
            destClass = EMPTY
            if srcClass == PAWN:
                if abs(fromCoord[1] - toCoord[1]) == 2:
                    meta = DOUBLE_PAWN_PUSH
                elif abs(fromCoord[0] - toCoord[0]) == 1:
                    meta = EP_CAPTURE
                elif toCoord[1] == 7 - 7 * self.color:
                    meta = 0b1000 | promoClass - 1
            if srcClass == KING:
                if fromCoord[0] == 4 and toCoord[0] == 2:
                    meta = QUEEN_CASTLE
                elif fromCoord[0] == 4 and toCoord[0] == 6:
                    meta = KING_CASTLE
            else:
                meta = QUIET_MOVE
        else:
            destColor, destClass = TypeToTupleColorClass[destType]
            if (destClass == PAWN):
                if toCoord[1] == 7 - 7 * self.color:
                    meta = 0b1100 | promoClass - 1
                else:
                    meta = CAPTURE
            else:
                meta = CAPTURE
                
        if srcClass == EMPTY: pdb.set_trace()
        return MoveInfo.From8x8(fromCoord, toCoord, srcClass, destClass, meta).ToInt32()

                
# --------------------------------------------------------------------
#  enpassant:  file which can be captured by enpassant or None         
#  castling:   The castling availability in the position               
#  hash:       The hash of the position                                
#  fifty:      A counter for the fifty moves rule                      
#  move:       The move that was applied to get the position           
#  tpiece:     The piece the move captured, == EMPTY for normal moves  
#                                                                      
#   important: The state variables refer to the state BEFORE           
#   the move is made.                                                  
#           
#   Early entries may be None instead of tuples if the information is  
#   not available (e.g. if the board was loaded from a position).      
#---------------------------------------------------------------------

class BoardHistory():
    def __init__(self, enpassant, castling, fiftymoveclock, moveInt32 = None, capPiececlass = None):
        self.initEnPassant = enpassant
        self.initCastling = castling
        self.initFifty = fiftymoveclock
        self.nextMove = moveInt32
        self.nextCapPiececlass = capPiececlass
    
    def __repr__(self):
        return self.__str__()
    def __str__(self):
        return '<BoardHistory: %s>' % MoveInfo.FromInt32(self.nextMove).ToPGN()


#class BoardException(Exception):
#    def __init__(self, zboard):
#        self.zboard = zboard
#    def __str__(self,):
#        
        

class BDebug():
    @staticmethod
    def MoveSort(zboard, moves):
        h = BDebug.Hash(zboard)
        a,b,c = h % 4-2, h % 2-1, h % 5 - 2
        vals = []
        for move in moves:
            mInfo = MoveInfo.FromInt32(move)
            if mInfo.meta == [QUEEN_CASTLE, KING_CASTLE, EP_CAPTURE]: pdb.set_trace()
            v = mInfo.origin64 % 8 * a + mInfo.dest64 % 8  * b + mInfo.oPiececlass % 4 * c - mInfo.meta * 2
            vals.append((v, move))

        vals.sort(key=lambda x: x[0])
        return [ val[1] for val in vals ]

    @staticmethod 
    def RandomMove(zboard):
        moves = MoveGen.GetMoves(zboard)
        return moves[random.randint(0, len(moves)-1)]
        

    @staticmethod
    def RandomMoves(zboard):
        moves = MoveGen.GetMoves(zboard)
        return BDebug.MoveSort(zboard, moves)
        

    @staticmethod
    def Hash(zboard):
        magic = 7
        wrap = lambda x: x % 10000
        cnt = 0
        cnt = wrap(cnt + zboard.board) 
        cnt = wrap(cnt + zboard.teamBoards[WHITE]) 
        cnt = wrap(cnt + zboard.teamBoards[BLACK]) 

        ep = zboard.enpassant if zboard.enpassant != None else 0
        castling = zboard.castling if zboard.castling != None else 0
        hasCastled = 7 if zboard.hasCastled else 2

        cnt = wrap(cnt + (zboard.color + 1) * ep * castling * hasCastled * zboard.fifty) 
        for color in [WHITE, BLACK]:
            for pClass in PieceClasses:
                cnt = wrap(cnt + zboard.pieceBoards[color][pClass])
        return cnt




