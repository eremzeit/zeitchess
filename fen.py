from board import *
from utils import zlog
from const import *
import pdb


CharToPiecetype = {
    'P' : W_PAWN,
    'N' : W_KNIGHT,
    'B' : W_BISHOP,
    'R' : W_ROOK,
    'Q' : W_QUEEN,
    'K' : W_KING,
    'p' : B_PAWN,
    'n' : B_KNIGHT,
    'b' : B_BISHOP,
    'r' : B_ROOK,
    'q' : B_QUEEN,
    'k' : B_KING,
}

PiecetypeToChar = {
    W_PAWN : 'P',
    W_KNIGHT : 'N',
    W_BISHOP : 'B',
    W_ROOK : 'R',
    W_QUEEN : 'Q',
    W_KING : 'K',
    B_PAWN : 'p',
    B_KNIGHT : 'n',
    B_BISHOP : 'b',
    B_ROOK : 'r',
    B_QUEEN : 'q',
    B_KING : 'k',
}

def PGNCoordTo8x8(pgnCoord):
    pgnCoord = pgnCoord.strip().lower()
    assert len(pgnCoord) == 2
    f = ord(pgnCoord[0]) - 97
    r = int(pgnCoord[1]) - 1
    return (f,r)

def PGNCoordTo64(pgnCoord):
    return To64(PGNCoordTo8x8(pgnCoord))

def FileToLetter(f):
    return chr(f + 97)
    

def ZBoardFromFen (fenstr):
    """ Applies the fenstring to the board.
        If the string is not properly
        written a SyntaxError will be raised, having its message ending in
        Pos(%d) specifying the string index of the problem.
        if an error is found, no changes will be made to the board. """
    

    zboard = ZBoard()
    
    # Get information
    parts = fenstr.split()
    
    if len(parts) > 6:
        raise Exception, "Can't have more than 6 fields in fenstr. "+ \
                           "Pos(%d)" % fenstr.find(parts[6])
    #STRICT_FEN = False 
    #if STRICT_FEN and len(parts) != 6:
    #    raise SyntaxError, "Needs 6 fields in fenstr. Pos(%d)" % len(fenstr)
    
    elif len(parts) < 4:
        raise Exception, "Needs at least 6 fields in fenstr. Pos(%d)" % \
                                                                 len(fenstr)
    
    elif len(parts) >= 6:
        pieceChrs, colChr, castChr, epChr, fiftyChr, moveNoChr = parts[:6]
    
    elif len(parts) == 5:
        pieceChrs, colChr, castChr, epChr, fiftyChr = parts
        moveNoChr = "1"
    
    else:
        pieceChrs, colChr, castChr, epChr = parts
        fiftyChr = "0"
        moveNoChr = "1"
    
    # Try to validate some information
    # TODO: This should be expanded and perhaps moved
    
    slashes = len([c for c in pieceChrs if c == "/"])
    if slashes != 7:
        raise SyntaxError, "Needs 7 slashes in piece placement field. "+ \
                           "Pos(%d)" % fenstr.rfind("/")
    
    if not colChr.lower() in ("w", "b"):
        raise SyntaxError, "Active color field must be one of w or b. "+ \
                           "Pos(%d)" % fenstr.find(len(pieceChrs), colChr)
    
    #if epChr != "-":
    #    pdb.set_trace()
    #    raise SyntaxError, ("En passant cord %s is not legal. "+ \
    #                        "Pos(%d) - %s") % (epChr, fenstr.rfind(epChr), \
    #                         fenstr)
    
    # Reset this board
    zboard.Reset()
    
    # Parse piece placement field
    from console import BoardSquaresToString 
    for _r, rank in enumerate(pieceChrs.split("/")):
        f = 0
        r = 7 - _r
        for char in rank:
            if char.isdigit():
                f += int(char)
            else:
                color = char.islower() 
                piecetype = CharToPiecetype[char]
                zboard.AddPiece(To64((f,r)), piecetype)
                f += 1
            

    # Parse active color field
    if colChr.lower() == "w":
        zboard.SetColor (WHITE)
    else: zboard.SetColor (BLACK)
    
    # Parse castling availability
    castling = 0
    for char in castChr:
        if zboard.variant == CHESS_960:
            raise NotImplemented()
        else:
            if char == "K":
                castling |= W_OO
            elif char == "Q":
                castling |= W_OOO
            elif char == "k":
                castling |= B_OO
            elif char == "q":
                castling |= B_OOO
    zboard.SetCastling(castling)

    # Parse en passant target sqaure
    if epChr == "-":
        zboard.SetEnPassant (None) 
    else:
        zboard.SetEnPassant(PGNCoordTo8x8(epChr)[0])
    
    # Parse halfmove clock field
    zboard.fifty = max(int(fiftyChr),0)
    
    # Parse fullmove number
    movenumber = int(moveNoChr)*2 -2
    if zboard.color == BLACK: movenumber += 1
    
    #zboard.history = [None]*movenumber
    
    zboard.UpdateFromPieceBoards()

    return zboard

def ZBoardToFen(zboard):
    pStr = ''
    
    _blank = 0
    for r in range(7, -1, -1):
        if r != 7: pStr += '/'
        _blank=0
        for f in range(0, 8):
            pType = zboard.squares[f][r]
            s = ''
            if pType == EMPTY:
                _blank += 1
                if f == 7:
                    s += str(_blank)

            else:
                if _blank != 0:
                    s += str(_blank)
                _blank = 0
                s += PiecetypeToChar[pType]
            pStr += s
    
    #color
    colorStr = 'b' if zboard.color else 'w'
    #castling
    
    castleStr = ''
    if zboard.castling & W_OO:
        castleStr += 'K'
    if zboard.castling & W_OOO:
        castleStr += 'Q'
    if zboard.castling & B_OO:
        castleStr += 'k'
    if zboard.castling & B_OOO:
        castleStr += 'q'

    if castleStr == '':
        castleStr = '-'

    #enpassant
    epStr = ''
    if zboard.enpassant == None:
        epStr = '-'
    else:
        fStr = FileToLetter(zboard.enpassant)
        rStr = '3' if zboard.color else '6'
        epStr = fStr + rStr
    

    #halfmove clock (fifty move)
    fiftyStr = str(zboard.fifty)

    #fullmove number
    fullmoveStr = str(len(zboard.history))

    return ' '.join([pStr, colorStr, castleStr, epStr, fiftyStr, fullmoveStr])


            
            #color, pClass = TypeToTupleColorClass[pType]

            



