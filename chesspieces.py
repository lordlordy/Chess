from observer import Observable
from abc import ABC, abstractmethod


class AbstractPiece(Observable):
    """
    Defines common methods for all chess pieces
    If piece is black it moves from top of board downwards. Otherwise moves upwards
    """

    # REFACTOR - currently these pieces 'assume' they're on an 8x8 board.

    def __init__(self, isblack, position):
        super().__init__()
        self._isBlack = isblack
        self._currentPosition = position
        self._adjustmentGrid = [[None for c in range(8)]for r in range(8)]
        self.__gridReference = self.__positionToGridRerence()

    def __str__(self):
        return self._piecechr()

    def __repr__(self):
        return f'{self.colour()} {self.description()} at {self._currentPosition}'

    def position(self):
        return self._currentPosition

    def setPosition(self, position):
        hasMoved = position != self._currentPosition
        self._currentPosition = position
        self.__gridReference = self.__positionToGridRerence()
        if hasMoved:
            self.notify(self)

    @abstractmethod
    def availableSquares(self, board):
        pass

    def score(self):
        """
        This is used to provide a value score for a piece to allow assessment of position / moves
        This is useful for providing 'tips' to a human player and for providing a method for a
        computer player to decide between moves.
        Black should score negative and white positive. This allows black to try and maximise negative and white positive
        :return: signed int
        """
        return self._baseScore() + self._scoreAdjustment()

    @abstractmethod
    def _baseScore(self):
        pass

    @abstractmethod
    def description(self):
        pass

    @abstractmethod
    def _piecechr(self):
        pass

    def display(self): return self._piecechr()
    def isBlack(self): return self._isBlack
    def movesDownwards(self): return self._isBlack
    def colour(self): return 'Black' if self._isBlack else 'White'

    def _scoreAdjustment(self):
        if self._adjustmentGrid:
            return self._adjustmentGrid[self.__gridReference[0]][self.__gridReference[1]]
        else:
            return 0

    def __positionToGridRerence(self):
        if len(self._currentPosition) != 2:
            raise ValueError(
                'Positions on the board are represented by two characters the first a letter the second a digit')
        else:
            col = self._currentPosition[0].lower()
            try:
                row = len(self._adjustmentGrid) - int(self._currentPosition[1])
            except:
                raise ValueError(f'Invalid row. Valid rows are integers in the range: 1..{len(self._adjustmentGrid)}')
            if row not in range(len(self._adjustmentGrid)):
                raise ValueError(f'Invalid row. Valid rows are in the range: 1..{len(self._adjustmentGrid)}')
            colOrd = ord(col)
            return row, (ord(col) - ord('a'))

class Pawn(AbstractPiece):

    def __init__(self,isBlack, position):
        super().__init__(isBlack, position)
        if isBlack:
            self._adjustmentGrid = [
                [-0, -0, -0, -0, -0, -0, -0, -0],
                [-0, -0, -0, -0, -0, -0, -0, -0],
                [-0, -0, -0, -1, -1, -0, -0, -0],
                [-0, -0, -0, -2, -2, -0, -0, -0],
                [-0, -0, -0, -0, -0, -0, -0, -0],
                [-10, -10, -10, -30, -30, -30, -30, -30],
                [-30, -30, -30, -30, -30, -30, -30, -30],
                [-80, -80, -80, -80, -80, -80, -80, -80]
            ]
        else:
            self._adjustmentGrid = [
                [80, 80, 80, 80, 80, 80, 80, 80],
                [30, 30, 30, 30, 30, 30, 30, 30],
                [10, 10, 10, 10, 10, 10, 10, 10],
                [0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 2, 2, 0, 0, 0],
                [0, 0, 0, 1, 1, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0]
            ]


    def availableSquares(self, board):
        """
        Pawns can move forward one square typically if not blocked by any piece. Two on first move
        Pawns can move diagonally one space if that takes another piece
        :param board:
        :param fromSquare: square piece is currently on
        :return: Array of strings representing squares
        """
        moves = []
        # note (r,c) referencing here is zero based top to bottom So A1 is actually (7,0) and H8 is (7,0)
        direction = (1,0) if self.isBlack() else (-1,0)
        canMoveTwo = (self.isBlack() and self._currentPosition[1] == '7') or ((not self.isBlack()) and self._currentPosition[1] == '2')

        s = board._positionXandYFrom(self._currentPosition, direction)
        if s and board.isEmpty(s):
            moves.append(s)
            # check for double move
            if canMoveTwo:
                # hasn't moved so perhaps can move 2 spaces
                s = board._positionXandYFrom(s, direction)
                if s and board.isEmpty(s):
                    moves.append(s)

        # check diagonals
        for m in [(1,1),(1,-1)] if self.isBlack() else [(-1,1),(-1,-1)]:
            s = board._positionXandYFrom(self._currentPosition, m)
            pieceAtTarget = board.pieceAtLabel(s)
            if pieceAtTarget and pieceAtTarget.isBlack() != self.isBlack():
                moves.append(s)

        return moves

    def attackingSquares(self, board):
        moves = []
        # check diagonals
        for m in [(1,1),(1,-1)] if self.isBlack() else [(-1,1),(-1,-1)]:
            s = board._positionXandYFrom(self._currentPosition, m)
            if s: moves.append(s)
        return moves


    def description(self): return "Pawn"

    def _baseScore(self):
        return -10 if self.isBlack() else 10

    # def score(self, board):
    #     if self.isBlack():
    #         # next move and its a queen
    #         if self._currentPosition[1] == '2': return -3
    #         elif self._currentPosition[1] == '3': return -2
    #         elif self._currentPosition[1] == '1': return -9 # this will be promoted to a queen
    #         else: return -1
    #     else:
    #         if self._currentPosition[1] == '7': return 3
    #         elif self._currentPosition[1] == '6': return 2
    #         elif self._currentPosition[1] == '8': return 9 # this will be promoted to a queen
    #         else: return 1

    def _piecechr(self):
        return chr(9823) if self.isBlack() else chr(9817)

class AbstractOfficer(AbstractPiece):
    @abstractmethod
    def _validDirections(self):
        """
        This should return a list (iterable) of tuples giving (r,c) where r and c represent rows and columns that
        a piece can move. Note this is only giving the direction - so it's hte minimum move. See method _canMoveMultipleTimes
        for pieces moving more than one square. Here are examples of moves for each piece:
        Bishop - (1,1) - it can move a diagonal up one row and across one column. NB this is just one of it's possible moves
        Knight - (2,1) - up 2 cross 1
        Rook - (1,0) - up 1
        Queen - (1,0) - up 1
        King - (1,0) - up one
        Note this is only for 'officers' ie not pawns.
        :return: iterable
        """
        pass

    @abstractmethod
    def _canMoveMultipleTimes(self):
        """
        Whether the valid directions given in _validDirections can be done multiple times. Eg - knight only does it move once
        :return: Boolean
        """
        pass

    @abstractmethod
    def description(self):
        pass

    def availableSquares(self, board):
        moves = []
        for d in self._validDirections():
            possMove = self._currentPosition
            while True:
                possMove = board.positionOffset(possMove, d)
                if possMove and board.isEmpty(possMove):
                    moves.append(possMove)
                elif possMove and board.isBlack(possMove) != self.isBlack():
                    # can move to this point, take the piece but move no further
                    moves.append(possMove)
                    break
                else:
                    break
                if not self._canMoveMultipleTimes():
                    # only allow one move
                    break
        return moves


class Knight(AbstractOfficer):

    def __init__(self,isBlack, position):
        super().__init__(isBlack, position)
        if isBlack:
            self._adjustmentGrid = [
                [5, 4, 3, 3, 3, 3, 4, 5],
                [4, 2, 0, 0, 0, 0, 2, 4],
                [3, 0, -1, -2, -2, -1, 0, 3],
                [3, -1, -2, -3, -3, -2, -1, 3],
                [3, -1, -2, -3, -3, -2, -1, 3],
                [3, 0, -1, -2, -2, -1, 0, 3],
                [4, 2, 0, 0, 0, 0, 2, 4],
                [5, 4, 3, 3, 3, 3, 4, 5]
            ]
        else:
            self._adjustmentGrid = [
                [-5, -4, -3, -3, -3, -3, -4, -5],
                [-4, -2, 0, 0, 0, 0, -2, -4],
                [-3, 0, 1, 2, 2, 1, 0, -3],
                [-3, 1, 2, 3, 3, 2, 1, -3],
                [-3, 1, 2, 3, 3, 2, 1, -3],
                [-3, 0, 1, 2, 2, 1, 0, -3],
                [-4, -2, 0, 0, 0, 0, -2, -4],
                [-5, -4, -3, -3, -3, -3, -4, -5]
            ]


    def _validDirections(self):
        return ((2,-1), (2,1), (1,-2), (1,2), (-1,-2), (-1,2), (-2,-1), (-2,1))

    def _canMoveMultipleTimes(self):
        return False

    def description(self): return 'Knight'

    # def score(self, board):
    #     factor = -1 if self.isBlack() else 1
    #     score = 3
    #     # if at side of board reduce by 1
    #     if self._currentPosition in {'a1','b1','c1','d1','e1','f1','g1','h1',
    #                                  'a8','b8','c8','d8','e8','f8','g8','h8',
    #                                  'a2','a3','a4','a5','a6','a7',
    #                                  'h2','h3','h4','h5','h6','h7'}:
    #         score -= 1
    #     return score * factor

    def _baseScore(self):
        return -30 if self.isBlack() else 30

    def _piecechr(self):
        return chr(9822) if self.isBlack() else chr(9816)

class Bishop(AbstractOfficer):

    def __init__(self,isBlack, position):
        super().__init__(isBlack, position)
        if isBlack:
            self._adjustmentGrid = [
                [2,1,1,1,1,1,1,2],
                [1,0,0,0,0,0,0,1],
                [1,0,-1,-1,-1,-1,0,1],
                [1,0,-1,-1,-1,-1,0,1],
                [1,0,-1,-1,-1,-1,0,1],
                [1,0,-1,-1,-1,-1,0,1],
                [1,0,0,0,0,0,0,1],
                [2,1,1,1,1,1,1,2]
            ]
        else:
            self._adjustmentGrid = [
                [-2,-1,-1,-1,-1,-1,-1,-2],
                [-1,0,0,0,0,0,0,-1],
                [-1,0,1,1,1,1,0,-1],
                [-1,0,1,1,1,1,0,-1],
                [-1,0,1,1,1,1,0,-1],
                [-1,0,1,1,1,1,0,-1],
                [-1,0,0,0,0,0,0,-1],
                [-2,-1,-1,-1,-1,-1,-1,-2]
            ]

    def _validDirections(self):
        return ((1, 1), (1, -1), (-1, 1), (-1, -1))

    def _canMoveMultipleTimes(self):
        return True

    def description(self): return 'Bishop'

    def _baseScore(self):
        return -30 if self.isBlack() else 30

    def _piecechr(self):
        return chr(9821) if self.isBlack() else chr(9815)

class Rook(AbstractOfficer):

    def __init__(self,isBlack, position):
        super().__init__(isBlack, position)
        if isBlack:
            self._adjustmentGrid = [
                [-0, -0, -0, -1, -1, -1, -0, -0],
                [-0, -0, -0, -0, -0, -0, -0, -0],
                [1, -0, -0, -0, -0, -0, -0, 1],
                [1, -0, -0, -0, -0, -0, -0, 1],
                [1, -0, -0, -0, -0, -0, -0, 1],
                [1, -0, -0, -0, -0, -0, -0, 1],
                [-0, -1, -1, -1, -1, -1, -1, -0],
                [-0, -0, -0, -0, -0, -0, -0, -0]
            ]
        else:
            self._adjustmentGrid = [
                [0, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 1, 1, 1, 1, 1, 0],
                [-1, 0, 0, 0, 0, 0, 0, -1],
                [-1, 0, 0, 0, 0, 0, 0, -1],
                [-1, 0, 0, 0, 0, 0, 0, -1],
                [-1, 0, 0, 0, 0, 0, 0, -1],
                [0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 1, 1, 1, 0, 0]
            ]

    def _validDirections(self):
        return ((1,0),(0,1),(-1,0),(0,-1))

    def _canMoveMultipleTimes(self):
        return True

    def description(self): return "Rook"

    def _baseScore(self):
        return -50 if self.isBlack() else 50

    def _piecechr(self):
        return chr(9820) if self.isBlack() else chr(9814)

class Queen(Rook, Bishop):

    def __init__(self,isBlack, position):
        AbstractOfficer.__init__(self, isBlack, position)
        if isBlack:
            # centre of board better than outside. Don't want too big adjustment as that may encourage early
            # exposure of the queen
            self._adjustmentGrid = [
                [2, 1, 1, 0, 0, 1, 1, 2],
                [1, 0, 0, 0, 0, 0, 0, 1],
                [1, 0, -1, -1, -1, -1, 0, 1],
                [0, 0, -1, -1, -1, -1, 0, 0],
                [0, 0, -1, -1, -1, -1, 0, 0],
                [1, 0, -1, -1, -1, -1, 0, 1],
                [1, 0, 0, 0, 0, 0, 0, 1],
                [2, 1, 1, 0, 0, 1, 1, 2],
            ]
        else:
            self._adjustmentGrid = [
                [-2, -1, -1, 0, 0, -1, -1, -2],
                [-1, 0, 0, 0, 0, 0, 0, -1],
                [-1, 0, 1, 1, 1, 1, 0, -1],
                [0, 0, 1, 1, 1, 1, 0, 0],
                [0, 0, 1, 1, 1, 1, 0, 0],
                [-1, 0, 1, 1, 1, 1, 0, -1],
                [-1, 0, 0, 0, 0, 0, 0, -1],
                [-2, -1, -1, 0, 0, -1, -1, -2]
            ]

    def _validDirections(self):
        return Rook._validDirections(self) + Bishop._validDirections(self)

    def description(self): return 'Queen'

    def _baseScore(self):
        return -90 if self.isBlack() else 90

    def _piecechr(self):
        return chr(9819) if self.isBlack() else chr(9813)

class King(Queen):

    def __init__(self,isBlack, position):
        super().__init__(isBlack, position)
        if isBlack:
            # adjustments - scores better if sitting in its own cornders - baddly in middle of board and in opponents half
            self._adjustmentGrid = [
                [-3, -2, -1, -0, -0, -1, -2, -3],
                [-2, -2, -0, -0, -0, -0, -2, -2],
                [1, 2, 2, 2, 2, 2, 2, 1],
                [2, 3, 3, 4, 4, 3, 3, 2],
                [3, 4, 5, 5, 5, 5, 4, 3],
                [3, 4, 5, 5, 5, 5, 4, 3],
                [3, 4, 5, 5, 5, 5, 4, 3],
                [3, 4, 5, 5, 5, 5, 4, 3]
            ]
        else:
            self._adjustmentGrid = [
                [-3, -4, -5, -5, -5, -5, -4, -3],
                [-3, -4, -5, -5, -5, -5, -4, -3],
                [-3, -4, -5, -5, -5, -5, -4, -3],
                [-3, -4, -5, -5, -5, -5, -4, -3],
                [-2, -3, -3, -4, -4, -3, -3, -1],
                [-1, -2, -2, -2, -2, -2, -2, -1],
                [2, 2, 0, 0, 0, 0, 2, 2],
                [3, 2, 1, 0, 0, 1, 2, 3]
            ]

    def _canMoveMultipleTimes(self):
        return False

    def description(self): return 'King'

    def _baseScore(self):
        # If you lose your King you've lost the game. King is effectively infinite in value - instead we use a large number
        return -999 if self.isBlack() else 999

    def _piecechr(self):
        return chr(9818) if self.isBlack() else chr(9812)

