import board
from chesspieces import Pawn, Bishop, Knight, Rook, Queen, King
from observer import Observable, AbstractObserver

helptext = """
This chess app allows you to play against another person or against a computer. 
It will check the move you make and will detect the following:
- check
- check mate
- invalid moves
- en passant
- castling
- pawn promotion
It can also provide assistance by showing you all moves that are available to you.
The computer has several levels. In the terminal this is limited to 10 but in the GUI you can set this however high you like. The level is just how many moves ahead the computer will search. Thus the levels are:
0 - Computer plays a random legal move
1 - Computer looks one move ahead and picks the best
2 - Computer looks two moves ahead and picks the best
2+ - Computer does a search of possible paths to however moves ahead. It attempts to eliminate paths that aren't worth exploring in order to speed up the search. In the absence of this 'Alpha Beta' pruning the search grows exponentially and even with it it grows fast. This means above ~ level 7 can get very slow. In the GUI if you chose 'Search To level' this does not prune the tree so above about level 3 is slow. 'AlphaBeta' in the GUI does some pruning and is usable up to about level 7.
Note in this version the move selection still has a lot of debugging to do which means at the moment the computer is completely beatable !
"""

class ChessConstants:
    # Some "Constants" - not really as python doesn't have them. However, don't really want them changing in code
    WHITE_IN_CHECK          = 'White in check!'
    WHITE_IN_CHECK_MATE     = 'Checkmate !! White loses'
    WHITE_MOVES             = 'White moves'
    WHITE_CASTLING_MOVES    = 'White Castling Moves'
    BLACK_IN_CHECK          = 'Black in check!'
    BLACK_IN_CHECK_MATE     = 'Checkmate !! Black loses'
    STALEMATE               = 'Game is a draw. No one wins'
    BLACK_MOVES             = 'Black moves'
    BLACK_CASTLING_MOVES    = 'Black Castling Moves'
    PAWN_PROMOTED           = 'Pawn Promoted'
    PROMOTION_OPTIONS       = {'Q','R','B','K'}
    CHECK                   = 'Check'     # think this should not be needed. REFACTOR - remove
    EN_PASSANT              = 'En Passant'
    PROMOTION_DONE          = 'Promotion Done'

    SHOW_WARNING    = 'Warning'
    SHOW_ADVICE     = 'Advice'
    SHOW_HELP       = 'Help'
    SHOW_USER_INPUT = 'UserInput'
    MOVE_MADE       = 'MoveMade'
    MOVE            = 'Move'
    PLAYER          = 'Player'

    STATUS_CHANGE   = 'StatusChange'
    STATUS_IN_PROGRESS = 0
    STATUS_NEW_GAME_NO_MOVES = 1
    STATUS_GAME_OVER = 2

# Custom Errors - to indicate incorrect
class IncorrectPlayerError(ValueError):
    pass

class ChessMove():
    def __init__(self, fromSquare, toSquare, description, isBlack, disallowed=False):
        self.fromSquare = fromSquare
        self.toSquare = toSquare
        self.description = description
        self._isBlack = isBlack
        # this represents a move that is valid for the piece but not allowed in the game.
        # ie a move that would result in the king being in check. This is set externally as
        # moves have no concept of the rules of the game that is being played with them
        self.disallowed = disallowed
        self.warning = None

        # create tuples for row, col in matrix for the square
        self.fromRC = (8-int(fromSquare[1]), ord(fromSquare[0])-ord('a'))
        self.toRC = (8-int(toSquare[1]), ord(toSquare[0])-ord('a'))

    def __str__(self):
        return f'{self.description}: {self.fromSquare}->{self.toSquare}'

    def isBlack(self):
        return self._isBlack

    def preChecked(self):
        return False

class PawnPromotion(ChessMove):
    def __init__(self, square, isBlack, choice):
        super().__init__(square, square, "Pawn Promotion", isBlack )
        self.choice = 'Q'
        if choice.upper() in {'Q', 'R', 'B', 'K'}:
            self.choice = choice.upper()
        self._promotedTo = 'Queen'
        if choice.upper() == 'R':
            self._promotedTo = 'Rook'
        elif choice.upper() == 'B':
            self._promotedTo = 'Bishop'
        elif choice.upper() == 'K':
            self._promotedTo = 'Knight'

    def __str__(self):
        return f'{self.description}: {self.fromSquare} promoted to {self._promotedTo}'

class EnPassant(ChessMove):
    def __init__(self, fromSquare, toSquare, isBlack, removingPieceAtSquare, playerWhoCanPlayEnPassant):
        super().__init__(fromSquare,toSquare, 'En Passant', isBlack)
        self.removingPieceAtSquare = removingPieceAtSquare
        self.playWhoCanPlayEnPassant = playerWhoCanPlayEnPassant

    def __str__(self):
        return f'{super().__str__()} (removing piece at {self.removingPieceAtSquare})'

    def preChecked(self):
        return True

class CastlingMove(ChessMove, AbstractObserver):
    """
    Represents the castle move. It needs to observe the king and rook to make sure they haven't moved.
    """
    def __init__(self, kingFrom, kingTo, rookFrom, rookTo,isBlack, positionsThatMustBeEmpty, positionsCannotBeBeingAttacked, description):
        # note we default this case to be disallowed=True
        ChessMove.__init__(self,kingFrom, kingTo, description, isBlack)
        self.rookFrom = rookFrom
        self.rookTo = rookTo
        self._emptyPositions = positionsThatMustBeEmpty
        self._positionsCannotBeBeingAttacked = positionsCannotBeBeingAttacked
        self._noLongerPossible = False # this flag is toggled once the king or rook has moved

    def objectChanged(self, theObjectThatChanged):
        self._noLongerPossible = True

    def isCastlingOn(self, positionsBeingAttacked, positionsEmpty):
        if self._noLongerPossible:
            return False # ie rook or king have moved
        if not self._emptyPositions.issubset(positionsEmpty):
            return False # squares between king and rook are not all empty
        if self.fromSquare in positionsBeingAttacked:
            return False # ie the king is in check
        # now check that king won't pass through a square that is being attacked
        if len(self._positionsCannotBeBeingAttacked.intersection(positionsBeingAttacked)) > 0:
            return False # ie move would require passing through a square under attack

        # PHEW! If we got this far without returning false. So lets return True !
        return True


class ChessGame(Observable):

    def __init__(self):
        super().__init__()
        self._blackPieces = []
        self._whitePieces = []
        self._player1 = None
        self._player2 = None
        self._moveCount = 0
        self._board = board.Board(8)
        self._status = None
        self._basicMoveCalculator = BasicChessMoveCalculator()

    def status(self):
        return self._status

    def setPlayer1(self, player):
        self._player1 = player
        player.setGame(self)
        if self._player2:
            self._player2.isBlack = not player.isBlack

    def setPlayer2(self, player):
        self._player2 = player
        player.setGame(self)
        if self._player1:
            self._player1.isBlack = not player.isBlack

    def nonHumanGame(self):
        return (not self._player1.isHuman()) and (not self._player2.isHuman())

    def playerToMove(self):
        return self._currentPlayer()

    def playerWaiting(self):
        return self._nextPlayer()

    def incheck(self, player):
        if player.isBlack:
            return self._boardAnalysis[ChessConstants.BLACK_IN_CHECK]
        else:
            return self._boardAnalysis[ChessConstants.WHITE_IN_CHECK]

    def moveCount(self):
        return self._moveCount

    def newGame(self):
        """
        Sets up board with pieces in appropriate places ready for a new game
        :return: None
        """
        self._board.reset()
        self._moveCount = 0

        self._blackKingSideCastle = CastlingMove('e8','g8','h8','f8', True, {'f8','g8'},{'f8','g8'},"Black King Side Castling")
        self._blackQueenSideCastle = CastlingMove('e8','c8','a8','d8', True, {'b8','c8','d8'},{'c8','d8'},"Black Queen Side Castling")
        self._whiteKingSideCastle = CastlingMove('e1','g1','h1','f1', False, {'f1','g1'},{'f1','g1'},"White King Side Castling")
        self._whiteQueenSideCastle = CastlingMove('e1','c1','a1','d1', False, {'b1','c1','d1'},{'c1','d1'},"White Queen Side Castling")

        # pieces that need observing
        blackKing = King(1, 'e8')
        blackKingSideRook = Rook(1, 'h8')
        blackQueenSideRook = Rook(1, 'a8')
        whiteKing = King(0, 'e1')
        whiteKingSideRook = Rook(0, 'h1')
        whiteQueenSideRook = Rook(0, 'a1')

        # add observers
        blackKing.addObserver(self._blackKingSideCastle)
        blackKingSideRook.addObserver(self._blackKingSideCastle)

        blackKing.addObserver(self._blackQueenSideCastle)
        blackQueenSideRook.addObserver(self._blackQueenSideCastle)

        whiteKing.addObserver(self._whiteKingSideCastle)
        whiteKingSideRook.addObserver(self._whiteKingSideCastle)

        whiteKing.addObserver(self._whiteQueenSideCastle)
        whiteQueenSideRook.addObserver(self._whiteQueenSideCastle)

        # set white pawns
        self._board.setRow([Pawn(0, chr(c)+str(2)) for c in range(ord('a'), ord('a') + self._board.size)],2)
        # set black pawns
        self._board.setRow([Pawn(1, chr(c)+str(7)) for c in range(ord('a'), ord('a') + self._board.size)],7)
        #set white officers
        self._board.setRow([whiteQueenSideRook,Knight(0,'b1'),Bishop(0,'c1'),Queen(0,'d1'),whiteKing,Bishop(0,'f1'), Knight(0,'g1'), whiteKingSideRook],1)
        #set black officers
        self._board.setRow([blackQueenSideRook,Knight(1,'b8'),Bishop(1,'c8'),Queen(1,'d8'),blackKing,Bishop(1,'f8'), Knight(1,'g8'), blackKingSideRook],8)

        self._boardAnalysis = self._analyseBoard()[1]

        self._setStatus(ChessConstants.STATUS_NEW_GAME_NO_MOVES)

    def _setStatus(self, newStatus):
        if newStatus != self._status:
            # print(f'STATUS CHANGE {self._status} tp {newStatus}')
            self._status = newStatus
            self.notify({ChessConstants.STATUS_CHANGE: newStatus})

    def promotePawn(self, pawn, pieceChoice='Q'):
        # pieceChoice is either Q, R, B, K, - for Queen, Rook, Bishop or Knight. Unlikely anyone will chose other than Q so default to that
        if pieceChoice.upper() == 'Q':
            newPiece = Queen(pawn.isBlack(), pawn.position())
        elif pieceChoice.upper() == 'R':
            newPiece = Rook(pawn.isBlack(), pawn.position())
        elif pieceChoice.upper() == 'B':
            newPiece = Bishop(pawn.isBlack(), pawn.position())
        elif pieceChoice.upper() == 'K':
            newPiece = Knight(pawn.isBlack(), pawn.position())
        else:
            self.notify({ChessConstants.SHOW_WARNING: 'Invalid choice please chose again'})
            raise ValueError('Invalid choice of piece for Pawn promotion.')
        # now switch piece
        self._board.remove(pawn.position())
        self._board.set(newPiece)
        self._boardAnalysis = self._analyseBoard()[1]

    def nextMoveColour(self):
        return 'Black' if self._moveCount % 2 else 'White'

    def moveListForCurrentPlayer(self):
        return self.availableMoves(self._currentPlayer())

    def makeMove(self, player, move):
        if self._status == ChessConstants.STATUS_GAME_OVER:
            return
        event = None
        if player.isBlack != self._moveCount % 2:
            text = f'Wrong player trying to move. Next move is {self.nextMoveColour()} but player moving is {player.colour()}'
            self.notify({ChessConstants.SHOW_WARNING: text})
            raise IncorrectPlayerError(text)
        if isinstance(move, ChessMove):
            if isinstance(move, PawnPromotion):
                # unusual move as there is purely a change of piece
                self.promotePawn(self._boardAnalysis[ChessConstants.PAWN_PROMOTED], move.choice)
                self.notify({ChessConstants.PROMOTION_DONE: move})
            else:
                self._board.move(move.fromSquare, move.toSquare)
                self.notify({ChessConstants.MOVE: move})
                if isinstance(move, EnPassant):
                    self._board.remove(move.removingPieceAtSquare)
                if isinstance(move, CastlingMove):
                    # the move above will have moved the king. Need to move the rook
                    self._board.move(move.rookFrom, move.rookTo)
                self._moveCount += 1
                self.notify({ChessConstants.MOVE_MADE: {ChessConstants.PLAYER: player, ChessConstants.MOVE: move}})
                analysis = self._analyseBoard(move=move)
                event = analysis[0]
                self._boardAnalysis = analysis[1]
                if event == ChessConstants.PAWN_PROMOTED:
                    self.notify({ChessConstants.PAWN_PROMOTED: self._boardAnalysis[ChessConstants.PAWN_PROMOTED]})
                if event in {ChessConstants.BLACK_IN_CHECK_MATE, ChessConstants.WHITE_IN_CHECK_MATE, ChessConstants.STALEMATE}:
                    self._setStatus(ChessConstants.STATUS_GAME_OVER)
                else:
                    self._setStatus(ChessConstants.STATUS_IN_PROGRESS)

                return event

        else:
            # this should not happen and is fatal. So through an exception that is unlikely to be dealt with.
            text = f'Invalid move. {move} should be an instance of ChessMove. Programme has almost certainly exited'
            self.notify({ChessConstants.SHOW_WARNING: text})
            raise Exception(text)

    def playerForSquare(self, row, col):
        piece = self._board.pieceAtGridReference(row,col)
        if piece:
            if self._player1.isBlack == piece.isBlack():
                return self._player1
            else:
                return self._player2
        else:
            return None

    def availableSquares(self, forRow, andCol):
        piece = self._board.pieceAtGridReference(forRow, andCol)
        if piece:
            allMoves = self.availableMoves(self.playerForSquare(forRow, andCol))
            allRowCols = [(m.fromRC, m.toRC) for m in allMoves]
            rowCols = [m[1] for m in allRowCols if m[0] == (forRow, andCol)]

            return rowCols
        else:
            return None

    def availableMoves(self, forPlayer):
        moves = []
        if forPlayer.isBlack:
            moves.extend(self._boardAnalysis[ChessConstants.BLACK_MOVES])
            cMoves = self._boardAnalysis[ChessConstants.BLACK_CASTLING_MOVES]
            if cMoves:
                moves.extend(cMoves)
        else:
            moves.extend(self._boardAnalysis[ChessConstants.WHITE_MOVES])
            cMoves = self._boardAnalysis[ChessConstants.WHITE_CASTLING_MOVES]
            if cMoves:
                moves.extend(cMoves)

        if self._boardAnalysis[ChessConstants.EN_PASSANT]:
            if self._boardAnalysis[ChessConstants.EN_PASSANT][0].playWhoCanPlayEnPassant == forPlayer:
                moves.extend(self._boardAnalysis[ChessConstants.EN_PASSANT])
        return moves

    def _currentPlayer(self):
        # white goes first so black will move on multiples of 2.
        isBlack = self._moveCount % 2
        if self._player1.isBlack == isBlack:
            return self._player1
        else:
            return self._player2

    def _nextPlayer(self):
        if self._currentPlayer() == self._player1:
            return self._player2
        else:
            return self._player1



    def _getEnPassant(self, move, board):
        pieceThatMoved = board.pieceAtLabel(move.toSquare)
        if not isinstance(pieceThatMoved,Pawn) or (abs(int(move.fromSquare[1])-int(move.toSquare[1])) == 1):
            return []
        # know we've got a pawn that didn't move one row up or down.
        # so this is a candidate for En Passant rule
        # check piece either side of destination - if it's an oponnents pawn then en passant is an option
        epMoves = []
        for i in [(0,1), (0,-1)]:
            p = self._board.pieceAtLabel(board._positionXandYFrom(move.toSquare, i))
            if p and p.isBlack() != pieceThatMoved.isBlack() and isinstance(p, Pawn):
                # yeh we have it - en passant
                fromSquare = p.position()

                toSquare = board._positionXandYFrom(pieceThatMoved.position(),(1 if p.isBlack() else -1,0))
                epMoves.append(EnPassant(fromSquare, toSquare, p.isBlack(), pieceThatMoved.position(), self._currentPlayer()))
        return epMoves

    def _analyseBoard(self, board=None, move=None):

        gameBoard = board if board else self._board
        sendNotifications = (board == None) # ie send notifications if analysing this objects game board

        boardAnalysis = self._basicMoveCalculator.calculateMoves(gameBoard)

        # check for Pawn promotion - check for pawns on end rows
        promotedPawns = []
        whitePromotionRow = gameBoard.getRow(8)
        for i in whitePromotionRow:
            if isinstance(i, Pawn) and not i.isBlack():
                promotedPawns.append(i)

        blackPromotionRow = gameBoard.getRow(1)
        for i in blackPromotionRow:
            if isinstance(i,Pawn) and i.isBlack():
                promotedPawns.append(i)

        if len(promotedPawns) == 0:
            boardAnalysis[ChessConstants.PAWN_PROMOTED] = None
        elif len(promotedPawns) == 1:
            boardAnalysis[ChessConstants.PAWN_PROMOTED] = promotedPawns[0]
        # we analyse board after every move so should only have one promoted pawn at most. More is a 'proper' error
        else:
            raise ValueError(f"Somehow you've managed to get {len(promotedPawns)} at the same time. This should not be possible")

        # check for castling
        # White first
        whiteCastling = []
        emptyFirstRankSquares = set([s for s in {'a1','b1','c1','d1','e1','f1','g1','h1'} if gameBoard.isEmpty(s)])
        positionsBeingAttacked = set([s.toSquare for s in boardAnalysis[ChessConstants.BLACK_MOVES] if not s.disallowed])
        if self._whiteKingSideCastle.isCastlingOn(positionsBeingAttacked,emptyFirstRankSquares):
            whiteCastling.append(self._whiteKingSideCastle)
        if self._whiteQueenSideCastle.isCastlingOn(positionsBeingAttacked, emptyFirstRankSquares):
            whiteCastling.append(self._whiteQueenSideCastle)
        boardAnalysis[ChessConstants.WHITE_CASTLING_MOVES] = whiteCastling if len(whiteCastling) > 0 else None

        # Now Black
        blackCastling = []
        emptyFinalRankSquares = set([s for s in {'a8', 'b8', 'c8', 'd8', 'e8', 'f8', 'g8', 'h8'} if self._board.isEmpty(s)])
        positionsBeingAttacked = set([s for s in boardAnalysis[ChessConstants.WHITE_MOVES] if not s.disallowed])
        if self._blackKingSideCastle.isCastlingOn(positionsBeingAttacked, emptyFinalRankSquares):
            blackCastling.append(self._blackKingSideCastle)
        if self._blackQueenSideCastle.isCastlingOn(positionsBeingAttacked, emptyFinalRankSquares):
            blackCastling.append(self._blackQueenSideCastle)
        boardAnalysis[ChessConstants.BLACK_CASTLING_MOVES] = blackCastling if len(blackCastling) > 0 else None

        # En Passant
        if move:
            boardAnalysis[ChessConstants.EN_PASSANT] = self._getEnPassant(move, gameBoard)
        else:
            boardAnalysis[ChessConstants.EN_PASSANT] = None

        interpretation = self._interpretAnalysis(boardAnalysis, gameBoard, sendNotifications)

        return (interpretation, boardAnalysis)

    def _interpretAnalysis(self, boardAnalysis, board, sendNotifications):
        cPlayer = self._currentPlayer()
        if boardAnalysis[ChessConstants.PAWN_PROMOTED]:
            if boardAnalysis[ChessConstants.PAWN_PROMOTED].isBlack() == self._nextPlayer().isBlack:
                self.notify({ChessConstants.PAWN_PROMOTED: f'{self._nextPlayer()}: You have promoted a pawn!'})
                return ChessConstants.PAWN_PROMOTED
            else:
                # shouldn't get here - we have a promoted pawn of the wrong colour
                raise Exception(
                    f"Somehow {cPlayer.colour()} has managed to promote a {boardAnalysis[ChessConstants.PAWN_PROMOTED].colour()} Pawn")
        # playerInCheck = 0
        if boardAnalysis[ChessConstants.WHITE_IN_CHECK_MATE]:
            if sendNotifications:
                self.notify({ChessConstants.WHITE_IN_CHECK_MATE: 'CHECK MATE  !!! Black wins'})
            return ChessConstants.WHITE_IN_CHECK_MATE
        elif boardAnalysis[ChessConstants.BLACK_IN_CHECK_MATE]:
            if sendNotifications:
                self.notify({ChessConstants.BLACK_IN_CHECK_MATE: 'CHECK MATE !!!  White wins'})
            return ChessConstants.BLACK_IN_CHECK_MATE
        elif boardAnalysis[ChessConstants.WHITE_IN_CHECK]:
            if sendNotifications:
                self.notify({ChessConstants.WHITE_IN_CHECK: 'CHECK!'})
            return ChessConstants.WHITE_IN_CHECK
        elif boardAnalysis[ChessConstants.BLACK_IN_CHECK]:
            if sendNotifications:
                self.notify({ChessConstants.BLACK_IN_CHECK: 'CHECK!'})
            return ChessConstants.BLACK_IN_CHECK
        else:
            #check for stalemate due to King not being able to move without getting in to check
            currentPlayerMoves = boardAnalysis[ChessConstants.BLACK_MOVES] if cPlayer.isBlack else boardAnalysis[ChessConstants.WHITE_MOVES]
            # if we've got this far the current player is not in check. Thus if no valid moves it is stalemate
            currentPlayerAvailableMoves = [m for m in currentPlayerMoves if not m.disallowed]
            if len(currentPlayerAvailableMoves) == 0:
                if sendNotifications:
                    self.notify({ChessConstants.STALEMATE:'King cannot move. STALEMATE! Game Over'})
                return ChessConstants.STALEMATE
            # check for stalemate due to too view pieces left
            if self._checkForStalemate(board, 0) or self._checkForStalemate(board,1):
                if sendNotifications:
                    self.notify({ChessConstants.STALEMATE:'Too few pieces to win. STALEMATE! Game Over'})
                return ChessConstants.STALEMATE

    def _checkForStalemate(self, board, attackerIsBlack):
        """
                Below a minimum pieces it is not possible to get check against solo king.
        first check for only king left for defender
        The other side must have minimum of
        - Queen (or pawn as could get promoted)
        - Rook
        - 2 x Bishop
        - Knight and Bishop - very unlikely
        This will not cover all possible stalemates but will automatically stop for known ones.
        :param board:
        :param attackerIsBlack:
        :return: True for stalemate
        """
        defendingPieces = board.piecesLeft(not attackerIsBlack)
        if len(defendingPieces) > 1:
            # defender not down to only it's king
            return False
        attackingPieces = board.piecesLeft(attackerIsBlack)
        if len(attackingPieces) > 3:
            # this could still be potentially by stalemate but won't check.
            return False
        else:
            # down to 3 or fewer pieces
            remainingPieceTypes = [type(p) for p in attackingPieces]
            if (Queen in remainingPieceTypes
                    or Pawn in remainingPieceTypes
                    or Rook in remainingPieceTypes
                    or remainingPieceTypes.count(Bishop) > 1
                    or (Knight in remainingPieceTypes and Bishop in remainingPieceTypes)):
                return False
            else:
                return True

        return False

    def _checkForCheck(self, board, attackerIsBlack):
        # need to pass in the board here since when checking for checkmate need to  use a copy of the board so we can move on that and check with this method
        attackingPieces = [p for p in board.piecesStillOnBoard() if p.isBlack() == attackerIsBlack]
        defenderKing = [p for p in board.piecesStillOnBoard() if isinstance(p, King) and p.isBlack() != attackerIsBlack][0]
        aSquares = set()
        for p in attackingPieces:
            if isinstance(p, Pawn):
                # pawn can only take diagonally so can't check all moves
                aSquares = aSquares.union(p.attackingSquares(board))
            else:
                aSquares = aSquares.union(p.availableSquares(board))

        return defenderKing.position() in aSquares


    def _movesWithThoseLeavingCheckDisallowed(self, board, isBlack):
        moves = self._possibleMoves(isBlack)
        for m in moves:
            copyBoard = board.copyOfBoard()
            copyBoard.move(m.fromSquare, m.toSquare)
            if self._checkForCheck(copyBoard, not isBlack):
                m.disallowed = True # since would put player in to check
                pieceDescripton = self._board.pieceAtLabel(m.fromSquare).description()
                m.warning = f'Cannot make move {pieceDescripton}: {m.fromSquare}->{m.toSquare} as that would place / leave you in check.'
        return moves

    def _possibleMoves(self, isBlack):
        return self._basicMoveCalculator.possibleMoves(self._board, isBlack)

    def help(self):
#         helptext = """
# This chess app allows you to play against another person or against a computer.
# It will check the move you make and will detect the following:
# - check
# - check mate
# - invalid moves
# - en passant
# - castling
# - pawn promotion
# It can also provide assistance by showing you all moves that are available to you.
# The computer has several levels. In the terminal this is limited to 10 but in the GUI you can set this however
#         """
        return helptext

class BasicChessMoveCalculator:
    def calculateMoves(self, gameBoard):

        moveDict = dict()
        moveDict[ChessConstants.WHITE_IN_CHECK] = self._checkForCheck(gameBoard, 1)
        moveDict[ChessConstants.BLACK_IN_CHECK] = self._checkForCheck(gameBoard, 0)

        moveDict[ChessConstants.WHITE_MOVES] = self._movesWithThoseLeavingCheckDisallowed(gameBoard, 0)
        moveDict[ChessConstants.WHITE_IN_CHECK_MATE] = (
                    len([x for x in moveDict[ChessConstants.WHITE_MOVES] if not x.disallowed]) == 0
                    and moveDict[ChessConstants.WHITE_IN_CHECK])

        moveDict[ChessConstants.BLACK_MOVES] = self._movesWithThoseLeavingCheckDisallowed(gameBoard, 1)
        moveDict[ChessConstants.BLACK_IN_CHECK_MATE] = (
                    len([x for x in moveDict[ChessConstants.BLACK_MOVES] if not x.disallowed]) == 0
                    and moveDict[ChessConstants.BLACK_IN_CHECK])

        return moveDict

    def possibleMoves(self, board, isBlack):
        pieces = [p for p in board.piecesStillOnBoard() if p.isBlack() == isBlack]
        moves = []
        for p in pieces:
            am = p.availableSquares(board)
            if len(am) == 0: continue
            for m in am:
                moves.append(ChessMove(p.position(), m, p.description(), isBlack))
        return moves

    def _checkForCheck(self, board, attackerIsBlack):
        # need to pass in the board here since when checking for checkmate need to  use a copy of the board so we can move on that and check with this method
        attackingPieces = [p for p in board.piecesStillOnBoard() if p.isBlack() == attackerIsBlack]
        defenderKing = [p for p in board.piecesStillOnBoard() if isinstance(p, King) and p.isBlack() != attackerIsBlack][0]
        aSquares = set()
        for p in attackingPieces:
            if isinstance(p, Pawn):
                # pawn can only take diagonally so can't check all moves
                aSquares = aSquares.union(p.attackingSquares(board))
            else:
                aSquares = aSquares.union(p.availableSquares(board))

        return defenderKing.position() in aSquares


    def _movesWithThoseLeavingCheckDisallowed(self, board, isBlack):
        moves = self.possibleMoves(board, isBlack)
        for m in moves:
            copyBoard = board.copyOfBoard()
            copyBoard.move(m.fromSquare, m.toSquare)
            if self._checkForCheck(copyBoard, not isBlack):
                m.disallowed = True # since would put player in to check
                pieceDescripton = board.pieceAtLabel(m.fromSquare).description()
                m.warning = f'Cannot make move {pieceDescripton}: {m.fromSquare}->{m.toSquare} as that would place / leave you in check.'
        return moves




if __name__ == '__main__':
    BasicChessMoveCalculator()