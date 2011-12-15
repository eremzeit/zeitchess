#!/usr/bin/python
import sys

from utils import zlog
import fen as fen_utils
import board
import butils
from console import *
import const
import search
from const import FEN_starting
import re
import pdb
import random
import filepipe

random.seed(1)

def out(msg, dbg=False):
    print msg
    zlog.log(msg)
    sys.stdout.flush()

class ZeitchessEngine():
    def makeReady(self):
        self.zboard = board.ZBoard()
        self.zboard.Reset()
    
    @staticmethod
    def printMove(move32):
        mInfo = MoveInfo.FromInt32(move32)
        out('move ' + mInfo.ToCECPString())

    def search (self):
        out('#searching...')
        """ Finds and prints the best move from the current position """
        pdb.set_trace()
        maxRes = search.AlphaBetaSearch(self.zboard, 4)
        move = maxRes.moveList[0]
        out('# ' + str(maxRes))
        self.zboard.MakeMove(move)
        ZeitchessEngine.printMove(move)
        zlog.log(self.zboard.ToString(True))

    def stopSearching(self):
        pass 
    
    def analyze (self):
        """ Searches, and prints info from, the position as stated in the cecp
            protocol """
        out('analyzing...')
        pass

class ZeitChessCECP(ZeitchessEngine):
    def __init__ (self, fen=FEN_starting):
        self.zboard = fen_utils.ZBoardFromFen(fen)
        #pdb.set_trace()
        
        self.isForced = False
        self.isAnalyzeMode = False
        
        self.features = [
            ("setboard", '1'),
            ("analyze", '0'),
            ("usermove", '1'),
            ("reuse", '0'),
            ("draw", '1'),
            ("sigterm", '0'),
            ("colors", '0'),
            ("variants", 'normal'),
            ("myname", 'zeitchess'),
        ]
    
    def run (self):
        while True:
            msg = ''
            try:
                msg = raw_input()
            except KeyboardInterrupt, k:
                out('#keyboard int')
                out(str(k))
                continue
    
            if not msg.strip(): continue
            zlog.log(msg)
            tokens = msg.split()

            
            if tokens[0] == "protover":
                strFeatures = ["%s=%s" % (feature[0],feature[1]) for feature in self.features]
                s = "feature %s done=1" % " ".join(strFeatures)
                out(s)
            elif tokens[0] == 'new':
                self.engineColor = const.BLACK
                #self.zboard.SetColor(const.BLACK)
            
            #elif tokens[0] == "sd":
            #    self.sd = int(tokens[1])
            #    self.skipPruneChance = max(0, (5-self.sd)*0.02)
            #    if self.sd >= 5:
            #        print "If the game has no timesettings, you probably don't want\n"+\
            #              "to set a search depth much greater than 4"
            
            #elif tokens[0] == "egtb":
            #    # This is a crafty command interpreted a bit loose
            #    self.useegtb = True
           # 
            #elif tokens[0] == "level":
            #    moves = int(tokens[1])
            #    self.increment = int(tokens[3])
            #    minutes = tokens[2].split(":")
            #    self.mytime = int(minutes[0])*60
            #    if len(minutes) > 1:
            #        self.mytime += int(minutes[1])
            #    print "Playing %d moves in %d seconds + %d increment" % \
            #            (moves, self.mytime, self.increment)
           # 
            #elif tokens[0] == "time":
            #    self.mytime = int(tokens[1])/100.
           # 
            ##elif tokens[0] == "otim":
            ##   self.optime = int(tokens[1])
            
            elif tokens[0] == "quit":
                sys.exit()
            
            elif tokens[0] == "result":
                # We don't really care what the result is at the moment.
                sys.exit()
            
            elif tokens[0] == "force":
                if not self.forced and not self.analyzing:
                    self.forced = True
                    self.__stopSearching()
            
            elif tokens[0] == "go":
                self.playingAs = self.zboard.color
                self.forced = False
                #pdb.set_trace()
                self.search()
            
            elif tokens[0] == "undo":
                self.stopSearching()
                self.zboard.UnmakeMove()
                if self.analyzing:
                    self.analyze()
            
            elif tokens[0] == "?":
                self.stopSearching()
           
            elif tokens[0] in ("black", "white"):
                newColor = tokens[0] == "black" and BLACK or WHITE
                if self.playingAs != newColor:
                    self.stopSearching()
                    self.engineColor = newColor
                    self.zboard.setColor(newColor)
                    self.zboard.setEnpassant(None)
                    if self.analyzing:
                        self.analyze()
            
            elif tokens[0] == "analyze":
                self.engineColor = self.zboard.color
                self.analyzing = True
                self.analyze()
                
            elif tokens[0] == "draw":
                if self.scr <= 0:
                    out("offer draw")
                
            elif tokens[0] == "random":
                #leval.random = True
                pass
            
            elif tokens[0] == "setboard":
                self.stopSearching()
                self.zboard = fen_utils.ZBoardFromFen(" ".join(tokens[1:]))
                if self.analyzing:
                    self.analyze()
            
            elif tokens[0] in ("xboard", "otim", "hard", "easy", "nopost", "post",
                              "accepted", "rejected", 'level', 'time'):
                pass
            
            elif tokens[0] == "usermove" or len(tokens) == 1 and re.match(r'[a-h][1-8][a-h][1-8][pnbrqk]{0,1}', tokens[0]):
                if self.engineColor == self.zboard.color: pdb.set_trace()
                out('# received a move')
                if tokens[0] == "usermove":
                    moveStr = tokens[1]
                else:
                    moveStr = tokens[0]
                move = ParseMove(self.zboard, moveStr)
                if move < 0: 
                    out('#skipping')
                    out("#Illegal move, " + moveStr)
                    out("Illegal move, " + moveStr)
                    continue

                out('#about to make move')
                self.zboard.MakeMove(move)
                out('#move made')
                self.engineColor = self.zboard.color
                
                if not self.isForced and not self.isAnalyzeMode:
                    out('#searching')
                    self.search()
                elif self.isAnalyzeMode:
                    out('#analyzing')
                    self.analyze()
                else:
                    out('#why do nothing?')
                
            else:
                out("Warning (unknown command): " + msg )
    

#Normal moves:   e2e4
#Pawn promotion: e7e8q
#Castling:   e1g1, e1c1, e8g8, e8c8
#Bughouse/crazyhouse drop:   P@h3
#ICS Wild 0/1 castling:  d1f1, d1b1, d8f8, d8b8
#FischerRandom castling: O-O, O-O-O (oh, not zero)
#Note that on boards with more than 9 ranks, counting of the ranks starts at 0.

#Beginning in protocol version 2, you can use the feature command to select SAN (standard algebraic notation) instead; for example, e4, Nf3, exd5, Bxf7+, Qxf7#, e8=Q, O-O, or P@h3. Note that the last form, P@h3, is a extension to the PGN standard's definition of SAN, which does not support bughouse or crazyhouse.

#xboard doesn't reliably detect illegal moves, because it does not keep track of castling unavailability due to king or rook moves, or en passant availability. If xboard sends an illegal move, send back an error message so that xboard can retract it and inform the user; see the section "Commands from the engine to xboard".
def ParseMove(zboard, moveStr):
    opColor = 1 - zboard.color
    coord1 = butils.CoordStringToCoord(moveStr[:2])
    coord2 = butils.CoordStringToCoord(moveStr[2:4])

    pClass = -1
    if len(moveStr) == 5:
        pClass = PieceStringToClass[moveStr[4].upper()]

    move = zboard.InterpretMove(coord1, coord2, pClass) 
    if move < 0:
        out('#move not valid ' + moveStr)
        return -1
    else:
        out('#parsed move ' + moveStr)
        return move

    #for pClass in PieceClasses:
    #    zboard.pieceBoards[opColor][

#def IsMoveValid(zboard, move):










if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1:] == ["xboard"]:
        zchess = ZeitChessCECP()
    else:
        out("Unknown argument(s): " + repr(sys.argv))
        sys.exit(0)
    
    #zchess.makeReady()
    try:
        zchess.run()
    except Exception, e:
        out('#in exception block')
        out('#' + str(e))




        ## TODO: Length info should be put in the book.
        ## Btw. 10 is not enough. Try 20
        ##if len(self.board.history) < 14:
        #movestr = self.__getBestOpening()
        #if movestr:
        #    mvs = [parseSAN(self.board, movestr)]
       # 
        ##if len(self.board.history) >= 14 or not movestr:
        #if not movestr:
        #       
        #    lsearch.skipPruneChance = self.skipPruneChance
        #    lsearch.useegtb = self.useegtb
        #    lsearch.searching = True
        #    
        #    if self.mytime == None:
        #        lsearch.endtime = sys.maxint
        #        worker.publish("Searching to depth %d without timelimit" % self.sd)
        #        mvs, self.scr = alphaBeta (self.board, self.sd)
        #    
        #    else:
        #        usetime = self.mytime / self.__remainingMovesA()
        #        if self.mytime < 6*60+self.increment*40:
        #            # If game is blitz, we assume 40 moves rather than 80
        #            usetime *= 2
        #        # The increment is a constant. We'll use this allways
        #        usetime += self.increment
        #        if usetime < 0.5:
        #            # We don't wan't to search for e.g. 0 secs
        #            usetime = 0.5
        #        
        #        starttime = time()
        #        lsearch.endtime = starttime + usetime
        #        prevtime = 0
        #        worker.publish("Time left: %3.2f seconds; Planing to thinking for %3.2f seconds" % (self.mytime, usetime))
        #        for depth in range(1, self.sd+1):
        #            # Heuristic time saving
        #            # Don't waste time, if the estimated isn't enough to complete next depth
        #            if usetime > prevtime*4 or usetime <= 1:
        #                lsearch.timecheck_counter = lsearch.TIMECHECK_FREQ
        #                search_result = alphaBeta(self.board, depth)
        #                if lsearch.searching:
        #                    mvs, self.scr = search_result
        #                    if time() > lsearch.endtime:
        #                        # Endtime occured after depth
        #                        worker.publish("Endtime occured after depth")
        #                        break
        #                    worker.publish("got moves %s from depth %d" % (" ".join(listToSan(self.board, mvs)), depth))
        #                else:
        #                    # We were interrupted
        #                    worker.publish("I was interrupted (%d) while searching depth %d" % (lsearch.last, depth))
        #                    if depth == 1:
        #                        worker.publish("I've got to have some move, so I use what we got")
        #                        mvs, self.scr = search_result
        #                    break
        #                prevtime = time()-starttime - prevtime
        #            else:
        #                worker.publish("I don't have enough time to go into depth %d" % depth)
        #                # Not enough time for depth
        #                break
        #        else:
        #            worker.publish("I searched through depths [1, %d]" % (self.sd+1))
        #        
        #        self.mytime -= time() - starttime
        #        self.mytime += self.increment
        #    
        #    if not mvs:
        #        if not lsearch.searching:
        #            # We were interupted
        #            lsearch.movesearches = 0
        #            lsearch.nodes = 0
        #            return
        #        
        #        # This should only happen in terminal mode
        #        
        #        #if lsearch.last == 4:
        #        #    print "resign"
        #        #else:
        #        if self.scr == 0:
        #            worker.publish("result %s" % reprResult[DRAW])
        #        elif self.scr < 0:
        #            if self.board.color == WHITE:
        #                worker.publish("result %s" % reprResult[BLACKWON])
        #            else: worker.publish("result %s" % reprResult[WHITEWON])
        #        else:
        #            if self.board.color == WHITE:
        #                worker.publish("result %s" % reprResult[WHITEWON])
        #            else: worker.publish("result %s" % reprResult[BLACKWON])
        #        worker.publish("last: %d %d" % (lsearch.last, self.scr))
        #        return
        #    
        #    worker.publish("moves were: %s %d" % (" ".join(listToSan(self.board, mvs)), self.scr))
        #    
        #    lsearch.movesearches = 0
        #    lsearch.nodes = 0
        #    lsearch.searching = False
       # 
        #move = mvs[0]
        #sanmove = toSAN(self.board, move)
        #return sanmove
