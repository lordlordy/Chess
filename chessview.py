import tkinter
from observer import AbstractObserver, Observable
from chessgame import ChessConstants, ChessMove
from chesspieces import Pawn
from boardgui import OutlineSquaresEvent, HighlightSquaresEvent, BoardCanvas
from chessplayers import ChessPlayers

class ChessGUI( AbstractObserver, Observable):

    NEW_GAME = 'New Game'
    MAKE_MOVE = 'Make Move'

    def __init__(self, size, root, testMode=False):
        Observable.__init__(self)
        self.pawnPromoted = False
        self._highlightMoves = tkinter.IntVar()
        self._highlightMoves.set(1)
        self._mouseOverGridRef = None
        self._mouseOverMoveGridRefs = []
        self._selectedGridRef = None
        self._selectedMoveGridRefs = []
        self._player1Type = tkinter.StringVar()
        self._player1Type.set(ChessPlayers.HUMAN)
        self._player2Type = tkinter.StringVar()
        self._player2Type.set(ChessPlayers.COMPUTER_LEVEL0)
        self.pWhiteDropDown = None
        self.pBlackDropDown = None

        middleColumn = tkinter.Frame(root)
        middleColumn.grid(row=0, column=1)

        self.playerLabel = tkinter.Label(middleColumn)
        self.playerLabel.grid(row=0, sticky='nsew')

        self.feedbackLabel = tkinter.Label(middleColumn)
        self.feedbackLabel.grid(row=1, sticky='nsew')

        self.boardCanvas = BoardCanvas(middleColumn, 8)
        self.boardCanvas.grid(row=2, sticky='nsew')
        self.addObserver(self.boardCanvas)

        self._moveText = tkinter.Text(root, width=20, state='disabled', wrap=tkinter.WORD, background=self.boardCanvas.colours[1])
        self._moveText.grid(row=0,column=0, sticky='nsew')

        helpFrame = self._createHelpFrame(root)
        helpFrame.grid(row=0,column=2, sticky='nsew')


        # follow movements of the mouse
        self.boardCanvas.bind('<Motion>', self.mouseMovement)
        self.boardCanvas.bind('<Button-1>', self.selectSquare)

    def setHighlightMoves(self):
        if not self._highlightMoves.get():
            self.removeSelectedSquareHighlighting()
            self._removeMouseMovementOutlines()

    def selectSquare(self, event):
        potentialMoveGridRef = self.boardCanvas.gridRefFromCoordinates(event.x, event.y)

        # TESTING
        pieceValue = self.controller.valueOfPiece(potentialMoveGridRef[0],potentialMoveGridRef[1])
        print(f'Piece Value = {pieceValue}')

        # END TESTING

        if potentialMoveGridRef:
            if potentialMoveGridRef == self._selectedGridRef:
                self.removeSelectedSquareHighlighting()
            elif potentialMoveGridRef in set(self._selectedMoveGridRefs):
                move = f'{self.boardCanvas.gridRefToLabel(self._selectedGridRef)}{self.boardCanvas.gridRefToLabel(potentialMoveGridRef)}'
                self.controller.makeMove(move)
                self.removeSelectedSquareHighlighting()
                self._removeMouseMovementOutlines()
                self.controller.nextPlayer()
            else:
                self.removeSelectedSquareHighlighting()
                self._selectedGridRef = potentialMoveGridRef
                self._selectedMoveGridRefs = []
                availableSquares = self.controller.availableSquares(potentialMoveGridRef[0],potentialMoveGridRef[1])
                if availableSquares:
                    for s in availableSquares:
                        self._selectedMoveGridRefs.append(tuple((s[0],s[1])))

                self.notify(HighlightSquaresEvent([self._selectedGridRef]))
                if self._highlightMoves.get() and len(self._selectedMoveGridRefs)>0:
                    self.notify(OutlineSquaresEvent(self._selectedMoveGridRefs,True))

    def removeSelectedSquareHighlighting(self):
        if self._selectedGridRef:
            self.notify(HighlightSquaresEvent([self._selectedGridRef],True))
            self._selectedGridRef = None
        if len(self._selectedMoveGridRefs) > 0:
            self.notify(OutlineSquaresEvent(self._selectedMoveGridRefs, True, True))
            self._selectedMoveGridRefs = []

    def mouseMovement(self,event):
        if not self._highlightMoves.get(): return
        gridRef = self.boardCanvas.gridRefFromCoordinates(event.x, event.y)
        if gridRef:
            if gridRef != self._mouseOverGridRef:
                self._removeMouseMovementOutlines()
                self._mouseOverGridRef = gridRef
                self._mouseOverMoveGridRefs = []
                availableSquares = self.controller.availableSquares(gridRef[0],gridRef[1])
                if availableSquares:
                    for m in availableSquares:
                        self._mouseOverMoveGridRefs.append(tuple((m[0],m[1])))

                self.notify(OutlineSquaresEvent([self._mouseOverGridRef],False))
                if len(self._mouseOverMoveGridRefs)>0:
                    self.notify(OutlineSquaresEvent(self._mouseOverMoveGridRefs,False))
        else:
            # outside grid bounds to remove highlighting
            self._removeMouseMovementOutlines()

    def _removeMouseMovementOutlines(self):
        if self._mouseOverGridRef:
            self.notify(OutlineSquaresEvent([self._mouseOverGridRef],False, True))
        if len(self._mouseOverMoveGridRefs)>0:
            self.notify(OutlineSquaresEvent(self._mouseOverMoveGridRefs,False,True))

    def clearPlayerLabel(self):
        self.playerLabel.configure(text='')

    def setPlayerLabel(self, labelText):
        self.playerLabel.configure(text=labelText)

    def setController(self, controller):
        self.controller = controller

    def setFeedbackLabel(self, labelText):
        self.feedbackLabel.configure(text=labelText)

    def objectChanged(self, data):
        if isinstance(data, dict):
            if ChessConstants.SHOW_WARNING in data:
                self.setFeedbackLabel(data[ChessConstants.SHOW_WARNING])
            if ChessConstants.MOVE in data:
                self._insertMoveText(data[ChessConstants.MOVE])
            if ChessConstants.WHITE_IN_CHECK in data:
                self._insertMoveText(data[ChessConstants.WHITE_IN_CHECK])
                self.setFeedbackLabel(data[ChessConstants.WHITE_IN_CHECK])
            if ChessConstants.BLACK_IN_CHECK in data:
                self._insertMoveText(data[ChessConstants.BLACK_IN_CHECK])
                self.setFeedbackLabel(data[ChessConstants.BLACK_IN_CHECK])
            if ChessConstants.WHITE_IN_CHECK_MATE in data:
                self._insertMoveText(data[ChessConstants.WHITE_IN_CHECK_MATE])
                self.setFeedbackLabel(data[ChessConstants.WHITE_IN_CHECK_MATE])
            if ChessConstants.BLACK_IN_CHECK_MATE in data:
                self.setFeedbackLabel(data[ChessConstants.BLACK_IN_CHECK_MATE])
                self._insertMoveText(data[ChessConstants.BLACK_IN_CHECK_MATE])
            if ChessConstants.STALEMATE in data:
                self.setFeedbackLabel(data[ChessConstants.STALEMATE])
                self._insertMoveText(data[ChessConstants.STALEMATE])
            if ChessConstants.PROMOTION_DONE in data:
                self._insertMoveText(str(data[ChessConstants.PROMOTION_DONE]))
            if ChessConstants.PAWN_PROMOTED in data:
                promotedPawn = data[ChessConstants.PAWN_PROMOTED]
                if isinstance(promotedPawn, Pawn):
                    colour = 'Black' if promotedPawn.isBlack() else 'White'
                    self.setFeedbackLabel("Pawn promoted. Please chose 'Q', 'R', 'B', or 'K' (Queen, Rook, Bishop or Knight) ")
            if ChessConstants.STATUS_CHANGE in data:
                if data[ChessConstants.STATUS_CHANGE] == ChessConstants.STATUS_IN_PROGRESS:
                    # disable drop downs - can't change player types during play
                    self.pWhiteDropDown.configure(state=tkinter.DISABLED)
                    self.pBlackDropDown.configure(state=tkinter.DISABLED)
                else:
                    self.pWhiteDropDown.configure(state=tkinter.NORMAL)
                    self.pBlackDropDown.configure(state=tkinter.NORMAL)


    def _start(self):
        self.controller.nextPlayer()

    def _setPlayer1Type(self, *args):
        self.controller.setPlayer1(self._player1Type.get(), self.__player1Level())
        if self._player1Type.get() == ChessPlayers.HUMAN:
            self._startButton.configure(state=tkinter.DISABLED)
        else:
            self._startButton.configure(state=tkinter.NORMAL)
        if self._player1Type.get() == ChessPlayers.COMPUTER_DEPTH or self._player1Type.get() == ChessPlayers.COMPUTER_ALPHA_BETA:
            self.whiteLevel.configure(state=tkinter.NORMAL)
        else:
            self.whiteLevel.configure(state=tkinter.DISABLED)
        self._player1LevelChanged(None)

    def _setPlayer2Type(self, *args):
        self.controller.setPlayer2(self._player2Type.get(), self.__player2Level())
        if self._player2Type.get() == ChessPlayers.COMPUTER_DEPTH or self._player2Type.get() == ChessPlayers.COMPUTER_ALPHA_BETA:
            self.blackLevel.configure(state=tkinter.NORMAL)
        else:
            self.blackLevel.configure(state=tkinter.DISABLED)
        self._player2LevelChanged(None)

    def _player1LevelChanged(self,event):
        if self._player1Type.get() == ChessPlayers.COMPUTER_DEPTH and self.__player1Level() > 3:
            print("WARNING: more than level 3 search gets exponentially slow")
            self.setFeedbackLabel("WARNING: more than level 3 search gets exponentially slow")
        elif self._player1Type.get() == ChessPlayers.COMPUTER_ALPHA_BETA and self.__player1Level() > 7:
            print("WARNING: more than level 7 aplha beta search gets exponentially slow")
            self.setFeedbackLabel("WARNING: more than level 7 aplha beta search gets exponentially slow")
        else:
            self.setFeedbackLabel("")
        self.controller.setPlayer1(self._player1Type.get(), self.__player1Level())

    def _player2LevelChanged(self,event):
        if self._player2Type.get() == ChessPlayers.COMPUTER_DEPTH and self.__player2Level() > 3:
            print("WARNING: more than level 3 search gets exponentially slow")
            self.setFeedbackLabel("WARNING: more than level 3 search gets exponentially slow")
        elif self._player2Type.get() == ChessPlayers.COMPUTER_ALPHA_BETA and self.__player2Level() > 7:
            print("WARNING: more than level 7 aplha beta search gets exponentially slow")
            self.setFeedbackLabel("WARNING: more than level 7 aplha beta search gets exponentially slow")
        else:
            self.setFeedbackLabel("")
        self.controller.setPlayer2(self._player2Type.get(), self.__player2Level())

    def __player1Level(self):
        try:
            return int(self.whiteLevel.get())
        except:
            return 1

    def __player2Level(self):
        try:
            return int(self.blackLevel.get())
        except:
            return 1

    def __levelValidation(self, S):
        # def __levelValidation(self, d, i, P, s, S, v, V, W):
        try:
            int(S)
            return True
        except:
            return False

    def _insertMoveText(self, someText):
        self._moveText.configure(state=tkinter.NORMAL)
        self._moveText.insert(1.0, '\n')
        text = str(someText)
        self._moveText.insert(1.0, text)
        if isinstance(someText, ChessMove):
            if not someText.isBlack():
                self._moveText.tag_add('white', '1.0', f'1.{str(len(text))}')
                self._moveText.tag_configure('white', foreground='white')
        self._moveText.insert(1.0, f'{self.controller.moveCount()}: ')
        self._moveText.configure(state=tkinter.DISABLED)

    def _newGame(self):
        self.controller.newGame()
        self.setHelpText('')
        self._moveText.configure(state=tkinter.NORMAL)
        self._moveText.delete(1.0, tkinter.END)
        self._moveText.configure(state=tkinter.DISABLED)

    def _quit(self):
        self.controller.quit()

    def _help(self):
        self.setHelpText(self.controller.getHelp())

    def setHelpText(self, someText):
        self._helpText.configure(state=tkinter.NORMAL)
        self._helpText.delete(1.0, tkinter.END)
        self._helpText.insert(tkinter.END, someText)
        self._helpText.configure(state=tkinter.DISABLED)

    def _makeMove(self):
        self.clearPlayerLabel()
        self.controller.makeMove(self.inputBox.get())

    def _moves(self):
        self.setHelpText(self.controller.getMoves())



    def _createHelpFrame(self, parent):
        frame = tkinter.Frame(parent)

        tkinter.Label(frame,text='Level:').grid(row=0,column=2)
        tkinter.Label(frame,text='White:').grid(row=1,column=0, sticky='nse')
        tkinter.Label(frame,text='Black:').grid(row=2,column=0, sticky='nse')

        self.pWhiteDropDown = tkinter.OptionMenu(frame, self._player1Type, *ChessPlayers.PLAYER_TYPES,
                                        command=self._setPlayer1Type)
        self.pWhiteDropDown.grid(row=1, column=1, sticky='nsew')
        self.pBlackDropDown = tkinter.OptionMenu(frame, self._player2Type, *ChessPlayers.PLAYER_TYPES,
                                        command=self._setPlayer2Type)
        self.pBlackDropDown.grid(row=2, column=1 , sticky='nsew')

        # validationCMD = (frame.register(self.__levelValidation),
        #         '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        validationCMD = (frame.register(self.__levelValidation),'%S')

        self.whiteLevel = tkinter.Entry(frame, width=5, validate='key', validatecommand=validationCMD)
        self.whiteLevel.grid(row=1, column=2, sticky= tkinter.N + tkinter.S + tkinter.E + tkinter.W)
        self.whiteLevel.bind('<FocusOut>', self._player1LevelChanged)
        self.whiteLevel.bind('<Return>', self._player1LevelChanged)
        self.whiteLevel.insert(0,'1')
        self.whiteLevel.configure(state=tkinter.DISABLED)

        self.blackLevel = tkinter.Entry(frame, width=5, validate='key', validatecommand=validationCMD)
        self.blackLevel.grid(row=2, column=2, sticky= tkinter.N + tkinter.S + tkinter.E + tkinter.W)
        self.blackLevel.bind('<FocusOut>', self._player2LevelChanged)
        self.blackLevel.bind('<Return>', self._player2LevelChanged)
        self.blackLevel.insert(0,'1')
        self.blackLevel.configure(state=tkinter.DISABLED)

        self._startButton = tkinter.Button(frame, text='START', command=self._start, state=tkinter.DISABLED)
        self._startButton.grid(row=3, column=0, sticky='nsew')

        newGameButton = tkinter.Button(frame, text='New Game', command=self._newGame)
        newGameButton.grid(row=3,column=1, sticky='nsew')

        quitButton = tkinter.Button(frame, text='Quit', command=self._quit)
        quitButton.grid(row=3, column=2, sticky='nsew')

        helpButton = tkinter.Button(frame, text='Help', command=self._help)
        helpButton.grid(row=4, column=0,sticky='nsew')

        self._highlightMovesCheckBox = tkinter.Checkbutton(frame, text='Highlight Moves', command=self.setHighlightMoves, variable=self._highlightMoves)
        self._highlightMovesCheckBox.grid(row=4, column=1, sticky='nsew')

        movesButton = tkinter.Button(frame, text='Moves', command=self._moves)
        movesButton.grid(row=4, column=2,sticky='nsew')

        self._helpText = tkinter.Text(frame, width=30, state=tkinter.DISABLED, wrap=tkinter.WORD, background=self.boardCanvas.colours[1])
        self._helpText.grid(row=5, columnspan=3, sticky='nsew')
        return frame

