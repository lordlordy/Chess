import tkinter
from observer import AbstractObserver
from board import BoardChangeEvent, SquareChangeEvent

class OutlineSquaresEvent:
    def __init__(self, gridRefs, isInner, removeOutline=False):
        self.gridRefs = gridRefs
        self.isInner = isInner
        self.removeOutline = removeOutline

class HighlightSquaresEvent:
    def __init__(self, gridRefs, removeHighlight=False):
        self.gridRefs = gridRefs
        self.removeHighlight = removeHighlight

class BoardCanvas(tkinter.Canvas, AbstractObserver):

    def __init__(self, master, size, squareSize=50, padding=15, colour1='lightyellow', colour2='lightblue', innerColour='green', outerColour='red'):
        canvasWidth = size * squareSize + padding*2
        canvasHeight = size * squareSize + padding*2
        tkinter.Canvas.__init__(self,master, width=canvasWidth, height=canvasHeight)
        self.pack()
        self._size = size
        self._squaresize = squareSize
        self._padding = padding
        self.colours = (colour1, colour2)
        self._innerColour = innerColour
        self._outerColour = outerColour
        self._displayGrid = []
        self._createBoardCanvas()
        # self._boardCanvas.pack()


    def gridRefFromCoordinates(self, x, y):
        """
        This converts a x,y co-ordinate within the canvas to a r,c in the grid. If outside returns None
        :param x: x co-ordinate within canvas
        :param y: y co-ordinate within canvas
        :return: Tuple (row, col) or none if x,y outside board
        """
        r = (y - self._padding) // self._squaresize
        c = (x - self._padding) // self._squaresize
        if r < self._size and c < self._size:
            return (r,c)
        else:
            return None

    def gridRefToLabel(self, gridRef):
        r = str(self._size-gridRef[0])
        c = chr(ord('a')+ gridRef[1])
        return f'{c}{r}'

    def objectChanged(self, data):
        if isinstance(data, BoardChangeEvent):
            self._displayPieces(data.board)
        if isinstance(data, SquareChangeEvent):
            self._displaySquare(data.row, data.col, data.content)
        if isinstance(data, OutlineSquaresEvent):
            if data.removeOutline:
                self._removeOutline(data.gridRefs, data.isInner)
            else:
                self._outline(data.gridRefs, data.isInner)
        if isinstance(data, HighlightSquaresEvent):
            if data.removeHighlight:
                self._removeHighlight(data.gridRefs)
            else:
                self._highlight(data.gridRefs)

    def _outline(self, gridRefs, isInner):
        for (r,c) in gridRefs:
            if isInner:
                self._displayGrid[r][c].innerOutline()
            else:
                self._displayGrid[r][c].outerOutline()

    def _removeOutline(self, gridRefs, isInner):
        for (r,c) in gridRefs:
            if r < len(self._displayGrid) and c < len(self._displayGrid):
                if isInner:
                    self._displayGrid[r][c].removeInnerOutline()
                else:
                    self._displayGrid[r][c].removeOuterOutline()

    def _highlight(self, gridRefs):
        for (r,c) in gridRefs:
            if r < len(self._displayGrid) and c < len(self._displayGrid):
                self._displayGrid[r][c].highlight()

    def _removeHighlight(self, gridRefs):
        for (r,c) in gridRefs:
            if r < len(self._displayGrid) and c < len(self._displayGrid):
                self._displayGrid[r][c].removeHighlight()

    def _displaySquare(self, row, col, content):
        square = self._displayGrid[row][col]
        if content:
            square.show(str(content), self)
        else:
            square.clearString()
            square.removeContent(self)

    def _displayPieces(self, board):
        row = 0
        for r in self._displayGrid:
            col = 0
            for c in r:
                piece = board[row][col]
                if piece:
                    c.show(str(piece), self)
                else:
                    c.clearString()
                    c.removeContent(self)
                col += 1
            row += 1


    def _createBoardCanvas(self):

        colour = 0
        rIndex = 0
        # create the grid of squares for display
        for r in range(self._padding, self._padding + self._squaresize * self._size, self._squaresize):
            row = []
            cIndex = 0
            self._displayGrid.append(row)
            for c in range(self._padding, self._padding + self._squaresize * self._size, self._squaresize):
                # put in the numbers and letters
                rStr = str(self._size - rIndex)
                cStr = chr(ord('a') + cIndex)
                if cIndex == 0:
                    self.create_text(c + self._squaresize * -0.17, r + self._squaresize * 0.5,
                                            text=rStr)
                if rIndex == self._size - 1:
                    self.create_text(c + self._squaresize * 0.5, r + self._squaresize * 1.17,
                                            text=cStr)
                row.append(BoardCanvas.Square(self, r, c, self._squaresize, self.colours[colour % 2], f'{cStr}{rStr}', self))
                colour += 1
                cIndex += 1
            colour += 0 if (self._size % 2) else 1
            rIndex += 1

        # return canvas


    class Square:

        def __init__(self, canvas, atR, atC, size, colour, label, board):
            self.OUTLINE_WIDTH = 3
            self.label = label
            self.board = board
            self.row = atR
            self.col = atC
            self.colour = colour
            self.size = size
            self.canvas = canvas
            self.square = canvas.create_rectangle(self.col, self.row, self.col + self.size, self.row + self.size,
                                                  fill=self.colour, outline='black', width=self.OUTLINE_WIDTH)
            self.centre = (self.col + self.size / 2, self.row + self.size / 2)
            self.content = None
            self._string = ''

        def __str__(self):
            return self._string if self.content else ''

        def outerOutline(self):
            self.canvas.create_rectangle(self.col + self.OUTLINE_WIDTH, self.row + self.OUTLINE_WIDTH,
                                         self.col + self.size - self.OUTLINE_WIDTH,
                                         self.row + self.size - self.OUTLINE_WIDTH,
                                         outline=self.board._outerColour, width=self.OUTLINE_WIDTH)

        def removeOuterOutline(self):
            self.canvas.create_rectangle(self.col + self.OUTLINE_WIDTH, self.row + self.OUTLINE_WIDTH,
                                         self.col + self.size - self.OUTLINE_WIDTH,
                                         self.row + self.size - self.OUTLINE_WIDTH,
                                         outline=self.colour, width=self.OUTLINE_WIDTH)

        def innerOutline(self):
            self.canvas.create_rectangle(self.col + self.OUTLINE_WIDTH * 2, self.row + self.OUTLINE_WIDTH * 2,
                                         self.col + self.size - self.OUTLINE_WIDTH * 2,
                                         self.row + self.size - self.OUTLINE_WIDTH * 2,
                                         outline=self.board._innerColour, width=self.OUTLINE_WIDTH)

        def removeInnerOutline(self):
            self.canvas.create_rectangle(self.col + self.OUTLINE_WIDTH * 2, self.row + self.OUTLINE_WIDTH * 2,
                                         self.col + self.size - self.OUTLINE_WIDTH * 2,
                                         self.row + self.size - self.OUTLINE_WIDTH * 2,
                                         outline=self.colour, width=self.OUTLINE_WIDTH)

        def highlight(self):
            self.removeContent(self.canvas)
            self.canvas.create_rectangle(self.col, self.row, self.col + self.size, self.row + self.size,
                                         fill=self.board._innerColour)
            self.show(self._string, self.canvas)

        def removeHighlight(self):
            self.removeContent(self.canvas)
            self.canvas.create_rectangle(self.col, self.row, self.col + self.size, self.row + self.size,
                                         fill=self.colour, outline='black', width=self.OUTLINE_WIDTH)
            self.show(self._string, self.canvas)

        def show(self, string, canvas):
            self._string = string
            if self.content:
                canvas.delete(self.content)
            self.content = canvas.create_text(self.centre[0], self.centre[1], text=string, font=(0, 33))

        def clearString(self):
            self._string = ''

        def removeContent(self, canvas):
            if self.content:
                canvas.delete(self.content)




# if __name__ == '__main__':
#     print('test')
#     root = tkinter.Tk()
#     BoardGUI(root, 8, 50)
#     root.mainloop()

