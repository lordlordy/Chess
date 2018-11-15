from observer import AbstractObserver
from chessgame import ChessConstants, ChessGame, ChessMove, IncorrectPlayerError
from chessplayers import HumanPlayerTerminal, HumanPlayerGUI, ComputerLevelZeroPlayer, ComputerLevelOnePlayer, ComputerLevelTwoPlayer, ChessPlayers
from chessplayers import ComputerTreeSearchPlayer, ComputerTreeSearchAlphaBetaPlayer
import sys, tkinter
from abc import ABC, abstractmethod
from chessview import ChessGUI
from boardgui import BoardCanvas

class TerminalChessObserver(AbstractObserver):

    def __init__(self, board):
        self._board = board

    def objectChanged(self, data):
        if isinstance(data, dict):
            for v in data.items():
                if v[0] == ChessConstants.MOVE_MADE:
                    player = v[1][ChessConstants.PLAYER]
                    move = v[1][ChessConstants.MOVE]
                    print(f'{player}: {move}')
                    print(self._board)
                else:
                    print(v[1])


class ChessController(ABC):

    @abstractmethod
    def play(self):
        pass

class TerminalChessGame(ChessController):
    def __init__(self, chessGame, debug=False):
        self.chessGame = chessGame
        self.__debug = debug


    def play(self):
        c = input('Player White human or computer (h or c): ')
        if c.upper() == 'C':
            level = input('Computer level [0 - 10]: ')
            self.chessGame.setPlayer1(self.__playerForLevel(level, 0))
        else:
            self.chessGame.setPlayer1(HumanPlayerTerminal(0, input("Player one name: ")))
        c = input('Player Black human or computer (h or c): ')
        if c.upper() == 'C':
            level = input('Computer level [0 - 10]: ')
            self.chessGame.setPlayer2(self.__playerForLevel(level,1))
        else:
            self.chessGame.setPlayer2(HumanPlayerTerminal(1, input("Player two name: ")))
        self.chessGame.newGame()

        print(self.chessGame._board)

        # moveCount = 0
        while True:
            # moveCount += 1
            quitGame = 0
            # cPlayer = self.chessGame.playerToMove(moveCount)
            cPlayer = self.chessGame.playerToMove()
            while True:
                move = cPlayer.choseMove(self.chessGame._board, self.chessGame.availableMoves(cPlayer), self.chessGame, self.chessGame.incheck(cPlayer))
                if isinstance(move, ChessMove):
                    try:
                        event = self.chessGame.makeMove(cPlayer, move)
                        if (event == ChessConstants.BLACK_IN_CHECK_MATE) or (event == ChessConstants.WHITE_IN_CHECK_MATE):
                            quitGame = 1
                            break
                        elif event == ChessConstants.PAWN_PROMOTED:
                            choice = cPlayer.promotePawnTo()
                            pawn = self.chessGame._board.pieceAtLabel(move.toSquare)
                            if choice:
                                self.chessGame.promotePawn(pawn, choice)
                            else:
                                self.chessGame.promotePawn(pawn)
                        break
                    except IncorrectPlayerError as ipe:
                        print(ipe)
                        quitGame = 1
                        break
                    except Exception as e:
                        print(e)
                        continue
                elif isinstance(move, str):
                    if move.lower() == 'h':
                        print(self.chessGame.help())
                        continue
                    elif move.lower() == 'd':
                        print(self.chessGame._board)
                        continue
                    elif move.lower() == 'q':
                        quitGame = 1
                        break
                    elif move.lower() == 'a':
                        moves = self.chessGame.availableMoves(cPlayer)
                        disallowed = [m for m in moves if m.disallowed]
                        allowed = [m for m in moves if not m.disallowed]
                        if len(disallowed):
                            print('disallowed moves: ', end="")
                            for m in disallowed:
                                print(m,',', end='')
                            print('\n')
                        print('Allowed Moves:')
                        for m in allowed:
                            print(m)
                        continue
                else:
                    print('Invalid string')
                    quitGame = 1
                    break
            if quitGame:
                break

    def __playerForLevel(self, level, isBlack):
        if level == '0':
            return ComputerLevelZeroPlayer(isBlack)
        elif level == '1':
            return ComputerLevelOnePlayer(isBlack)
        elif level == '2':
            return ComputerLevelTwoPlayer(isBlack)
        else:
            try:
                l = int(level)
                return ComputerTreeSearchAlphaBetaPlayer(isBlack, l, self.__debug)
            except:
                return ComputerLevelTwoPlayer(isBlack)

class GUIChessController(ChessController, AbstractObserver):

    def __init__(self,gui, chessGame, root, debug=False):
        self.root = root
        self.gui = gui
        self.chessGame = chessGame
        self.gui.setController(self)
        self._p1 = HumanPlayerGUI(0,'Human')
        self._p2 = ComputerLevelZeroPlayer(1)
        self._helpIsShowingMoves = 0
        self._pawnPromoted = False
        self._gameOver = False
        chessGame.setPlayer1(self._p1)
        chessGame.setPlayer2(self._p2)
        self.count = 0
        self.__debug = debug


    def moveCount(self):
        return self.chessGame.moveCount()

    def play(self):
        self.chessGame.newGame()
        self._gameOver = False
        firstPlayer = self.chessGame.playerToMove()
        self.gui.setPlayerLabel(str(firstPlayer))
        # this starts the game loop
        self.nextPlayer()

    def nextPlayer(self):
        # used to manage the game order. Does nothing if players are human, just lets gui await the move
        # for a computer player this prods the computer to make it's move
        if self._gameOver:
            print('game is over')
            return
        player = self.chessGame.playerToMove()
        if not player.isHuman():
            self.root.update() #ensure the GUI updates for move prior to thinking about next move
            self.makeMove('')

    def makeMove(self, moveString):
        print(f'Pieces Score = {self.chessGame._board.piecesScore()}')
        if self.chessGame.status() == ChessConstants.STATUS_GAME_OVER:
            return
        event = None
        cPlayer = self.chessGame.playerToMove()
        if self._pawnPromoted:
            cPlayer.setPromotePawnChoice(moveString, self.chessGame._boardAnalysis[ChessConstants.PAWN_PROMOTED].position())
            move = cPlayer.promotePawnTo()
        else:
            cPlayer.setChosenMove(moveString)
            move = cPlayer.choseMove(self.chessGame._board, self.chessGame.availableMoves(cPlayer), self.chessGame, self.chessGame.incheck(cPlayer))
        if isinstance(move, ChessMove):
            event = self.chessGame.makeMove(cPlayer,move)
            if (event == ChessConstants.STALEMATE
                    or event == ChessConstants.WHITE_IN_CHECK_MATE
                    or event == ChessConstants.BLACK_IN_CHECK_MATE):
                self._gameOver = True
                return event
            if event == ChessConstants.PAWN_PROMOTED:
                self._pawnPromoted = True
                self.gui.pawnPromoted = True
                self.gui.setPlayerLabel(str(cPlayer))
                # playerSwitched = False
            else:
                self._pawnPromoted = False
                self.gui.pawnPromoted = False
                self.gui.setPlayerLabel(str(self.chessGame.playerToMove()))
                if event not in {ChessConstants.BLACK_IN_CHECK_MATE, ChessConstants.WHITE_IN_CHECK_MATE, ChessConstants.WHITE_IN_CHECK, ChessConstants.BLACK_IN_CHECK}:
                    self.gui.setFeedbackLabel('')
            # self.gui.clearInput()
            self.gui.removeSelectedSquareHighlighting()
        if self._helpIsShowingMoves:
            self.gui.setHelpText('')

        if self.chessGame.nonHumanGame():
            self.root.after(100, self.nextPlayer)
        elif not isinstance(self.chessGame.playerToMove(), HumanPlayerGUI):
            self.nextPlayer()



    def availableSquares(self, forRow, andCol):
        return self.chessGame.availableSquares(forRow,andCol)

    def valueOfPiece(self, atRow, atCol):
        piece = self.chessGame._board.pieceAtGridReference(atRow, atCol)
        return piece.score() if piece else 0

    def quit(self):
        self.root.destroy()

    def newGame(self):
        self.chessGame.newGame()
        self._gameOver = False

    def moves(self):
        moves = self.chessGame.moveListForCurrentPlayer()
        print(moves)

    def setPlayer1(self, playerType, level=None):
        if playerType == ChessPlayers.HUMAN:
            self.chessGame.setPlayer1(HumanPlayerGUI(0))
        elif playerType == ChessPlayers.COMPUTER_LEVEL0:
            self.chessGame.setPlayer1(ComputerLevelZeroPlayer(0))
        elif playerType == ChessPlayers.COMPUTER_LEVEL1:
            self.chessGame.setPlayer1(ComputerLevelOnePlayer(0))
        elif playerType == ChessPlayers.COMPUTER_LEVEL2:
            self.chessGame.setPlayer1(ComputerLevelTwoPlayer(0))
        elif playerType == ChessPlayers.COMPUTER_DEPTH:
            self.chessGame.setPlayer1(ComputerTreeSearchPlayer(0, level if level else 1))
        elif playerType == ChessPlayers.COMPUTER_ALPHA_BETA:
            self.chessGame.setPlayer1(ComputerTreeSearchAlphaBetaPlayer(0, level if level else 1, self.__debug))

    def setPlayer2(self, playerType,level=None):
        if playerType == ChessPlayers.HUMAN:
            self.chessGame.setPlayer2(HumanPlayerGUI(1))
        elif playerType == ChessPlayers.COMPUTER_LEVEL0:
            self.chessGame.setPlayer2(ComputerLevelZeroPlayer(1))
        elif playerType == ChessPlayers.COMPUTER_LEVEL1:
            self.chessGame.setPlayer2(ComputerLevelOnePlayer(1))
        elif playerType == ChessPlayers.COMPUTER_LEVEL2:
            self.chessGame.setPlayer2(ComputerLevelTwoPlayer(1))
        elif playerType == ChessPlayers.COMPUTER_DEPTH:
            self.chessGame.setPlayer2(ComputerTreeSearchPlayer(1,level if level else 1))
        elif playerType == ChessPlayers.COMPUTER_ALPHA_BETA:
            self.chessGame.setPlayer2(ComputerTreeSearchAlphaBetaPlayer(1, level if level else 1, self.__debug))

    def setNames(self, p1Name, p2Name):
        self._p1.name = p1Name
        self._p2.name = p2Name
        self.gui.setPlayerLabel(str(self.chessGame.playerToMove()))

    def getHelp(self):
        self._helpIsShowingMoves = 0
        return self.chessGame.help()

    def getMoves(self):
        self._helpIsShowingMoves = 1
        moves = self.chessGame.moveListForCurrentPlayer()
        s = 'The following are valid moves:\n'
        allowed = [m for m in moves if not m.disallowed]
        for m in allowed:
            s += str(m) + '\n'
        disallowed = [m for m in moves if m.disallowed]
        if len(disallowed)>0:
            s += 'The following are disallowed:\n'
            for m in disallowed:
                s += str(m) + '\n'
        return s

    def objectChanged(self, data):
        if ChessConstants.STATUS_GAME_OVER in data:
            self._gameOver = True


def startTerminalMode(debug=False):
    chess = ChessGame()
    chess.addObserver(TerminalChessObserver(chess._board))
    game = TerminalChessGame(chess, debug)
    game.play()

def startGUIMode(debug=False):
    root = tkinter.Tk()
    root.title('Chess')

    gui = ChessGUI(8, root)

    chess = ChessGame()
    terminalObserver = TerminalChessObserver(chess._board)

    chess.addObserver(gui)
    chess.addObserver(terminalObserver)
    chess._board.addObserver(gui.boardCanvas)
    chess._board.addObserver(terminalObserver)

    game = GUIChessController(gui, chess, root, debug)
    game.play()

    root.resizable(False, False)

    root.mainloop()

if __name__ == '__main__':

    if '-gui' in sys.argv:
        if '-debug' in sys.argv:
            startGUIMode(True)
        else:
            startGUIMode()
    elif '-terminal' in sys.argv:
        if '-debug' in sys.argv:
            startTerminalMode(True)
        else:
            startTerminalMode()
    else:
        while True:
            choice = input("Gui or terminal ? Type 'g' or 't' : ")
            if choice.lower() == 'g':
                startGUIMode()
                break
            elif choice.lower() == 't':
                startTerminalMode()
                break
            else:
                print('INVALID CHOICE')
