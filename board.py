from abc import ABC, abstractmethod
from observer import Observable
from copy import deepcopy


class SquareChangeEvent():
    def __init__(self, row, col, content):
        self.row = row
        self.col = col
        self.content = content

class BoardChangeEvent():
    """
    Used to indicate the full board has changed - eg it's been reset
    """
    def __init__(self, board):
        self.board = board

class Board(Observable):
    """
    Generic Board. Merely a grid that can maintain state of pieces on it.
    This does not and should not know the rules of a game or how pieces move.
    It should  be possible to use this board with different types of game
    Will need refactoring if board sizes great than 9 ever required as the parsing to and from
    matrix position and string code assumes single digits
    The board expects pieces to have methods:
    setPosition(self, position) and position(self)
    """
    def __init__(self, size, grid=None):
        # do need option to pass in grid ? RE FACTOR - probably don't need this
        Observable.__init__(self)
        self._colOrdStart = ord('a')
        self._colOrdEnd = self._colOrdStart + size - 1
        self._grid = grid if grid else [[None for c in range(size)] for r in range(size)]
        self.size = size

        # create regular expression to match moves. Do it here so only done once.
        r = r'[a-' + chr(self._colOrdEnd) + 'A-' + chr(self._colOrdEnd).upper() + ']'
        # add number range.
        r += '[1-' + str(size) + ']'
        self._movePattern = r


    def movePattern(self): return self._movePattern

    def __str__(self):
        gridStr = '\n'
        gridStr += ' |'
        for c in range(self._colOrdStart, self._colOrdStart + len(self._grid)):
            gridStr += f' {chr(c)} |'
        gridStr += '\n'
        gridStr += '-'*(len(self._grid)*4+4)
        gridStr += '\n'

        for r in range(len(self._grid)):
            gridStr += f'{len(self._grid)-r}|'
            for c in range(len(self._grid)):
                piece = self._grid[r][c]
                if piece == None:
                    gridStr += '   |'
                else:
                    gridStr += f' {piece} |'
            gridStr += str(len(self._grid)-r)
            gridStr += '\n'
            gridStr += '-'*(len(self._grid)*4+4)
            gridStr += '\n'
        gridStr += ' |'
        for c in range(self._colOrdStart, self._colOrdStart + len(self._grid)):
            gridStr += f' {chr(c)} |'
        gridStr += '\n'
        return gridStr

    def piecesScore(self):
        value = 0
        for r in self._grid:
            for c in r:
                if c:
                    value += c.score()
        return value

    def reset(self):
        """
        Sets all grid positions to 'None'
        :return: None
        """
        self._grid = [[None for c in range(len(self._grid))] for r in range(len(self._grid))]
        self.notify(BoardChangeEvent(self._grid))

    def validColumns(self):
        """
        :return: str - Valid letters to represent a column
        """
        return [chr(i) for i in range(self._colOrdStart, self._colOrdStart + len(self._grid))]

    def validRows(self):
        """
        Valid row numbers for use in position string
        :return: List of integers
        """
        return [i for i in range(1, len(self._grid)+1)]

    def getRow(self, rowNumber):
        rowIndex = self.size - rowNumber
        if rowIndex < 0 or rowIndex >= self.size:
            raise ValueError(f'{rowNumber} is outside the range of rows: 1 - {self.size}')
        return self._grid[rowIndex]

    def setRow(self, row, index):
        """
        Set a row on the board in one go. Just aimed at simplifying the code
        :param row: Array of pieces same length as the matrix
        :param index: index as per board referencing - ie based from 1 and goes bottom to top
        :return: None
        """
        if len(row) != len(self._grid):
            raise ValueError(f'Incorrect length row provided. Row of length {len(row)} but matrix is {len(self._grid)} x {len(self._grid)}')
        if index < 1 or index > self.size:
            raise ValueError(f'Row index out of range. {index} supplied but matrix rows run from 1 to {len(self._grid)}')

        self._grid[self.size - index] = row
        self.notify(BoardChangeEvent(self._grid))

    def set(self, piece):
        """
        Pieces are placed in the new position whether or not there is a pieceAtLabel there already
        :param piece: Should be an implementation of AbstractPiece
        :return: None
        """
        gridP = self.labelToGridReference(piece.position())
        self._grid[gridP[0]][gridP[1]] = piece
        self.notify(SquareChangeEvent(gridP[0],gridP[1],piece))

    def remove(self, atPosition):
        """
        Remove pieceAtLabel at this position
        :param atPosition: str - col as a letter, row as a digit (running bottom to top)
        :return: the pieceAtLabel removed
        """
        gridP = self.labelToGridReference(atPosition)
        piece = self._grid[gridP[0]][gridP[1]]
        self._grid[gridP[0]][gridP[1]] = None
        self.notify(SquareChangeEvent(gridP[0],gridP[1],None))
        return piece

    def move(self, fromSquare, toSquare):
        """
        Moves the pieceAtLabel at from square to square. Returns any pieceAtLabel at to square or none.
        The board has no concepts of the rules so this will not raise an exception.
        This means you can move a blank square and remove a pieceAtLabel. Or can remove a pieceAtLabel of the same colour.
        :param fromSquare: game square as a position (eg d3)
        :param toSquare: game square as a position (eg d3)
        :return: AbstractPiece or None
        """
        # note - no need to send notifications here as they are sent in the self.remove and self.set methods
        moving = self.remove(fromSquare)
        target = self.remove(toSquare)
        moving.setPosition(toSquare)
        self.set(moving)
        return target

    def pieceAtLabel(self, label):
        """
        Get the pieceAtLabel at a given position if any.
        :param label: code for grid position (eg d5). Can be generated from zero based co-ordinates using gridReferenceToLabel(row,col)
        :return: AbstractPiece or None if square is empty or doesn't equist
        """
        if label:
            g = self.labelToGridReference(label)
            return self.pieceAtGridReference(g[0], g[1])
        else:
            return None

    def pieceAtGridReference(self, atRow, atCol):
        return self._grid[atRow][atCol]

    def labelToGridReference(self, position):
        """
        Returns grid reference for accessing matric from a code
        :param position: position code
        :return: tuple (r,c) - row column in matrix
        """
        if len(position) != 2:
            raise ValueError('Positions on the board are represented by two characters the first a letter the second a digit')
        else:
            col = position[0].lower()
            if ord(col) not in range(self._colOrdStart, self._colOrdStart + len(self._grid)):
                raise ValueError(f'Invalid column. Valid columns are: {self.validColumns()}')
            try:
                row = len(self._grid) - int(position[1])
            except:
                raise ValueError(f'Invalid row. Valid rows are integers in the range: 1..{len(self._grid)}')
            if row not in range(len(self._grid)):
                raise ValueError(f'Invalid row. Valid rows are in the range: 1..{len(self._grid)}')
            # colOrd = ord(col)
            # newCol = colOrd - self._colOrdStart
            return row, (ord(col) - self._colOrdStart)

    def gridReferenceToLabel(self, rcTuple):
        """
        Returns the position code for a row and column
        :param rcTuple: (r,c) representing row, col in matrix (as it's zero based)
        :return: string code
        """
        positionStr = chr(self._colOrdStart + rcTuple[1])
        r = len(self._grid) - rcTuple[0]
        positionStr += str(r)
        return positionStr

    def positionOffset(self, fromSquare, rcOffset):
        grid = self._positionXandYFrom(fromSquare, rcOffset)
        return grid

    def isEmpty(self,position):
        return self.pieceAtLabel(position) == None

    def isBlack(self,atPosition):
        if self.isEmpty(atPosition): return None
        else: return self.pieceAtLabel(atPosition).isBlack()

    def piecesStillOnBoard(self):
        pieces = []
        for r in self._grid:
            for p in r:
                if p:
                    pieces.append(p)
        return pieces

    def piecesLeft(self, isBlack):
        pOnBoard = self.piecesStillOnBoard()
        pieces = [p for p in pOnBoard if p.isBlack() == isBlack]
        return pieces


    def copyOfBoard(self):
        # NB - don't want to copy the observers. This is the reason moved from deepcopy. Need to think before overriding __deepcopy__
        copyOfGrid = deepcopy(self._grid)
        new = Board(self.size, copyOfGrid)
        return new

    def _positionXandYFrom(self, square, rcTuple):
        """
        Returns the square c columns and r rows from square
        :param fromSquare: position (ie d2)
        :param x: Int
        :param y: Int
        :return: position (ie e6) or None if move is off the board
        """
        gridRef = self.labelToGridReference(square)
        newRow = gridRef[0] + rcTuple[0]
        newCol = gridRef[1] + rcTuple[1]
        if newRow < 0 or newCol < 0 or newRow >= len(self._grid) or newCol >= len(self._grid):
            return None
        else:
            return self.gridReferenceToLabel((newRow, newCol))

