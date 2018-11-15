from abc import ABC, abstractmethod
import re
from random import randint
from chessgame import PawnPromotion, ChessConstants, BasicChessMoveCalculator

class ChessPlayers:

    HUMAN           = "Human"
    COMPUTER_LEVEL0 = "Random"
    COMPUTER_LEVEL1 = "1 Move Ahead"
    COMPUTER_LEVEL2 = "2 Move Ahead"
    COMPUTER_DEPTH = "Search to Level"
    COMPUTER_ALPHA_BETA = "AlphaBeta to Level"
    PLAYER_TYPES    = [HUMAN, COMPUTER_LEVEL0, COMPUTER_LEVEL1, COMPUTER_LEVEL2,
                       COMPUTER_DEPTH, COMPUTER_ALPHA_BETA]


class AbstractPlayer(ABC):
    def __init__(self, isBlack, name):
        self._game = None
        self.isBlack = isBlack
        self.name = name

    def __str__(self):
        return f'{self.name} [{self.colour()}]'

    def game(self):
        return self._game

    def setGame(self, game):
        self._game = game

    def colour(self):
        return 'Black' if self.isBlack else 'White'

    def setChosenMove(self, move):
        pass

    def setPromotePawnChoice(self, promote, square):
        pass

    def isHuman(self):
        return False

    @abstractmethod
    def choseMove(self, board, moves, observable=None, incheck=False):
        pass

    @abstractmethod
    def promotePawnTo(self):
        pass

class ComputerLevelZeroPlayer(AbstractPlayer):
    """
    This computer player chooses randomly from available moves.
    """

    def __init__(self, isBlack, name='Toe Deep Blue'):
        super().__init__(isBlack, name)
        self._promotePawnChoice = None

    def choseMove(self, board, moves, observable=None, incheck=False):
        availableMoves = [m for m in moves if not m.disallowed]
        if len(availableMoves)>0:
            choice = randint(0, len(availableMoves)-1)
            return availableMoves[choice]

    def setPromotePawnChoice(self, promote, square):
        self._promotePawnChoice = PawnPromotion(square, self.isBlack, 'Q')

    def promotePawnTo(self):
        return self._promotePawnChoice

class ComputerLevelOnePlayer(ComputerLevelZeroPlayer):
    """
    This computer evaluates the board for each of it's moves and choses the one with the highest score.
    In practise it means it at least takes a piece if it's offered but is easy to beat as it doesn't consider
    whether it may lose a piece in exchange.
    """

    def __init__(self, isBlack, name='Shallow Blue'):
        super().__init__( isBlack, name)
        self._calculator = BasicChessMoveCalculator()

    def choseMove(self, board, moves, observable=None, incheck=False):
        best = self._bestScoreAndMoveAfterAMove(board, self.isBlack, [m for m in moves if not m.disallowed])
        return best[0]

    def _bestScoreAndMoveAfterAMove(self, forBoard, isBlack, moves=None):
        if moves:
            availableMoves = moves
        else:
            availableMoves = [m for m in self._calculator.possibleMoves(forBoard,isBlack) if not m.disallowed]

        copyBoard = forBoard.copyOfBoard()
        # randomly chose starting initial move. This ensures that if all moves are same value it choses random
        move = availableMoves[randint(0, len(availableMoves)-1)]
        # note that if white a high score is better. If black a lower score is better
        scoreFactor = -1 if isBlack else 1
        copyBoard.move(move.fromSquare, move.toSquare)
        score = copyBoard.piecesScore()

        # print(f'\tSTART [{"Black" if isBlack else "White"}] move: {move} score: {score}')

        for i in range(1,len(availableMoves)):
            copyBoard = forBoard.copyOfBoard()
            copyBoard.move(availableMoves[i].fromSquare, availableMoves[i].toSquare)
            newScore = copyBoard.piecesScore()
            # print(f'\t\tCONSIDERING move: {availableMoves[i]} score: {newScore}')

            if newScore*scoreFactor > score*scoreFactor:
                # print(f'\tBetter - new best score is {newScore}')
                score = newScore
                move = availableMoves[i]

        return (move, score)

class ComputerLevelTwoPlayer(ComputerLevelOnePlayer):
    """
    This plays quite a bit better because it now looks at what the opponents most likely response in evaluating the board
    This means it won't offer up a stupid sacrifice. Still easily beatable but should give a half decent game and won't
    make many blatant 'mistakes'
    """
    def __init__(self, isBlack, name='Out of your depth Blue'):
        super().__init__( isBlack, name)

    def choseMove(self, board, moves, observable=None, incheck=False):
        availableMoves = [m for m in moves if not m.disallowed]
        if len(availableMoves) == 0:
            return # game over as no moves
        scoreFactor = -1 if self.isBlack else 1
        move = availableMoves[randint(0, len(availableMoves)-1)]
        copyBoard = board.copyOfBoard()
        copyBoard.move(move.fromSquare, move.toSquare)
        # print(f'START [{"Black" if self.isBlack else "White"}] move: {move}')
        score = self._bestScoreAndMoveAfterAMove(copyBoard, not self.isBlack)[1] # this is scoring the opponents move
        # the best score is now the lowest score after the oponents move - as they're chosing the best for them
        # print(f'SCORE: {score}')

        for i in range(1, len(availableMoves)):
            copyBoard = board.copyOfBoard()
            copyBoard.move(availableMoves[i].fromSquare, availableMoves[i].toSquare)
            # print(f'\tCONSIDERING move: {availableMoves[i]}')

            newScore = self._bestScoreAndMoveAfterAMove(copyBoard, not self.isBlack)
            # the best score is now the lowest score after the oponents move - as they're chosing the best for them
            # print(f'\tSCORE: {newScore[1]}')

            if newScore[1] * scoreFactor > score * scoreFactor:
                # print(f'Better - new best score is {newScore[1]}')

                score = newScore[1]
                move = availableMoves[i]

        return move

class ComputerTreeSearchPlayer(ComputerLevelTwoPlayer):
    """
    This looks an arbitrary number of moves ahead. The tree grows rapidly (exponentially) ... so looking more than
    a few levels down will get very slow.
    """
    def __init__(self, isBlack, depth, name='Deepish Blue'):
        newName = f'{name} (level {str(depth)}'
        super().__init__( isBlack, newName)
        self._depth = depth

    def setDepth(self, depth):
        self._depth = depth

    def choseMove(self, board, moves, observable=None, incheck=False):
        self.leafCount = 0
        self.moveCount = 0
        availableMoves = {m for m in moves if not m.disallowed}
        if len(availableMoves) == 1:
            return list(availableMoves)[0]
        else:
            return self._bestScore(0,board,self.isBlack, moves)[1]

    def _bestScore(self, depth, board, isBlack, moves=None):
        # spaces = '  ' * depth
        if depth == self._depth:
            self.leafCount += 1
            # searched as far down as we want to go
            colour = 'Black' if isBlack else 'White'
            s = board.piecesScore()
            print('\t\tSeaching tree: %s Score: %04d' % (self.leafCount, s), end='\r')
            # print(f'{spaces}Depth: {depth} [{colour}] Searching tree: {self.leafCount}  score: {s}')
            return (s, None)
        else:
            availableMoves = moves if moves else [m for m in self._calculator.possibleMoves(board,isBlack) if not m.disallowed]
            if isBlack:
                # so negative is good
                score = 99999 # big positive number - so guaranteed all scores will be less than
                move = None
                for m in availableMoves:
                    # if depth == 0:
                        # self.moveCount += 1
                        # print(f'checking {m} Move {self.moveCount} of {len(availableMoves)} moves')
                    copyBoard = board.copyOfBoard() # CHECK - could do a lot of copies
                    copyBoard.move(m.fromSquare, m.toSquare)
                    newScore = self._bestScore(depth+1, copyBoard, not isBlack)[0]
                    if newScore < score:
                        score = newScore
                        move = m
                # print(f'{spaces}DEPTH:{depth} [Black] Returning {move} with score {score}')
                return (score, move)
            else:
                # white to positive is good
                score = -99999
                move = None
                for m in availableMoves:
                    copyBoard = board.copyOfBoard() # CHECK - could do a lot of copies
                    copyBoard.move(m.fromSquare, m.toSquare)
                    newScore = self._bestScore(depth+1, copyBoard, not isBlack)[0]
                    if newScore > score:
                        score = newScore
                        move = m
                # print(f'{spaces}DEPTH:{depth} [White] Returning {move} with score {score}')
                return (score, move)


class ComputerTreeSearchAlphaBetaPlayer(ComputerLevelTwoPlayer):
    """
    This looks an arbitrary number of moves ahead. The tree grows rapidly (exponentially) ... so looking more than
    a few levels down will get very slow.
    """

    def __init__(self, isBlack, depth, debug=False, name='Deeper Blue'):
        newName = f'{name} (level {str(depth)})'
        super().__init__(isBlack, newName)
        self._depth = depth
        self.__debug = debug

    def setDepth(self, depth):
        self._depth = depth

    def setDebug(self, debug):
        self.__debug = debug

    def choseMove(self, board, moves, observable=None, incheck=False):
        self.leafCount = 0
        self.moveCount = 0
        availableMoves = {m for m in moves if not m.disallowed}
        if len(availableMoves) == 1:
            return list(availableMoves)[0]
        else:
            return self._bestScore(0, -9999, 9999, board, self.isBlack, availableMoves)[1]

    # incorporating "alpha-beta" pruning - this stops searching branches that can give nothing better than we've already found
    def _bestScore(self, depth, alpha, beta, board, isBlack, moves=None):
        spaces = '  ' * depth
        if depth == self._depth:
            self.leafCount += 1
            # searched as far down as we want to go
            s = board.piecesScore()
            if self.__debug:
                print(f'{spaces}Depth:{depth} Tree leaf:{self.leafCount}  score:{s}')
            else:
                # print(f'Seaching tree: {self.leafCount} depth: {depth} alpha: {alpha} beta: {beta}')
                print('\t\tSeaching tree: %s  score: %s' % (self.leafCount, s), end='\r')
            return (s, None)
        else:
            availableMoves = moves if moves else [m for m in self._calculator.possibleMoves(board, isBlack) if
                                                  not m.disallowed]
            if isBlack:
                # so negative is good
                score = 99999  # big positive number - so guaranteed all scores will be less than
                move = None
                for m in availableMoves:
                    if self.__debug:
                        if depth == 0:
                            self.moveCount += 1
                            print(f'Move {self.moveCount} of {len(availableMoves)} moves: checking {m} ')
                        print(f'{spaces} Depth {depth} checking black {m}')
                    copyBoard = board.copyOfBoard()  # CHECK - could do a lot of copies
                    copyBoard.move(m.fromSquare, m.toSquare)
                    newScore = self._bestScore(depth + 1, alpha, beta, copyBoard, False)[0]

                    if newScore < score:
                        score = newScore
                        move = m

                    # alpha beta pruning
                    beta = min(beta, newScore)
                    if beta <= alpha:
                        # if depth == 0:
                        #     if self.__debug:
                        #         print(f'{spaces} NOT PRUNED AT DEPTH {depth} after checking {self.moveCount} moves aplha:beta={alpha}:{beta}')
                        # else:
                        #     if self.__debug:
                        #         print(f'{spaces}PRUNED AT DEPTH {depth} aplha:beta={alpha}:{beta}')
                        #     break
                        print(f'{spaces}PRUNED AT DEPTH {depth} aplha:beta={alpha}:{beta}')
                        break

                if self.__debug:
                    print(f'{spaces}DEPTH:{depth} [Black] Returning {move} with score {score}')
                return (score, move)
            else:
                # white to positive is good
                score = -99999
                move = None
                for m in availableMoves:
                    if self.__debug:
                        if depth == 0:
                            self.moveCount += 1
                            print(f'Move {self.moveCount} of {len(availableMoves)} moves: checking {m} ')
                        print(f'{spaces}checking white {m}')
                    copyBoard = board.copyOfBoard()  # CHECK - could do a lot of copies
                    copyBoard.move(m.fromSquare, m.toSquare)
                    newScore = self._bestScore(depth + 1, alpha, beta, copyBoard, True)[0]

                    if newScore > score:
                        score = newScore
                        move = m

                    # alpha beta pruning
                    alpha = max(alpha, newScore)
                    if beta <= alpha:
                        # if depth == 0:
                        #     if self.__debug:
                        #         print(f'{spaces} NOT PRUNED AT DEPTH {depth} after checking {self.moveCount} moves aplha:beta={alpha}:{beta} ')
                        # else:
                        #     if self.__debug:
                        #         print(f'{spaces}PRUNED AT DEPTH {depth} aplha:beta={alpha}:{beta}')
                        #     break
                        print(f'{spaces}PRUNED AT DEPTH {depth} aplha:beta={alpha}:{beta}')
                        break

                if self.__debug:
                    print(f'{spaces}DEPTH:{depth} [White] Returning {move} with score {score}')
                return (score, move)


class AbstractHumanPlayer(AbstractPlayer):
    def isHuman(self):
        return True

    def validateMove(self, move, board, moves, observable, incheck ):
        # need to filter  moves for those that are allowed
        availableMoves = [m for m in moves if not m.disallowed]
        disallowedMoves = [m for m in moves if m.disallowed]
        if move.upper() in {'Q', 'H', 'D', 'A'}:
            return move.upper()
        fromTo = re.findall(board.movePattern(), move)
        if len(fromTo) > 1:
            fromTo = (fromTo[0].lower(), fromTo[1].lower())
            if len(fromTo) == 2:
                # check move is in available moves
                chosenMove = [m for m in availableMoves if m.fromSquare == fromTo[0] and m.toSquare == fromTo[1]]
                # check if move is in disallowed move
                moveDisallowed = [m for m in disallowedMoves if m.fromSquare == fromTo[0] and m.toSquare == fromTo[1]]
                if len(chosenMove) == 1:
                    return chosenMove[0]
                elif len(chosenMove) > 1:
                    # this is fundamental error as there shouldn't more than one
                    raise ValueError(
                        f'Should not be more than one valid move for {fromTo} but we somehow have {chosenMove}')
                else:
                    # user typed something incorrect lets see if we can say something useful
                    piece = board.pieceAtLabel(fromTo[0])
                    if piece == None:
                        observable.notify(
                            {ChessConstants.SHOW_WARNING: f'Please select a piece. {fromTo[0]} is an empty square '})
                    elif piece.isBlack() != self.isBlack:
                        observable.notify(
                            {ChessConstants.SHOW_WARNING: f'Please select one of your own pieces. The piece on {fromTo[0]} is {piece.colour()}.'})
                    elif len(moveDisallowed) == 1:
                        observable.notify({ChessConstants.SHOW_WARNING: moveDisallowed[0].warning})
                    else:
                        if incheck:
                            observable.notify(
                                {ChessConstants.SHOW_WARNING: f'You cannot make move: {fromTo[0]}->{fromTo[1]}. You are in check and need to make a move to get out of check. Remember: press "a" for available moves'})
                        else:
                            observable.notify({ChessConstants.SHOW_WARNING: f'You cannot make move: {fromTo[0]}->{fromTo[1]}. This {piece.description()} can only move to the following squares {piece.availableSquares(board)}'})
            else:
                observable.notify({ChessConstants.SHOW_WARNING: f'{move} is INVALID. Please try again...'})
        else:
            observable.notify({ChessConstants.SHOW_WARNING: f'{move} is INVALID. Please try again...'})

class HumanPlayerGUI(AbstractHumanPlayer):

    def __init__(self, isBlack, name='Human'):
        super().__init__(isBlack, name)
        self.chosenMove = None
        self.promotePawnChoice = None

    def setChosenMove(self, move):
        self.chosenMove = move

    def setPromotePawnChoice(self, promote, square):
        self.promotePawnChoice = PawnPromotion(square, self.isBlack, 'Q')
        if promote.upper() in ChessConstants.PROMOTION_OPTIONS:
            self.promotePawnChoice.choice = promote.upper()

    def choseMove(self, board, moves, observable=None, incheck=False):
        if self.chosenMove:
            validation = self.validateMove(self.chosenMove, board, moves, observable, incheck)
            if validation:
                return validation

    def promotePawnTo(self):
        return self.promotePawnChoice

class HumanPlayerTerminal(AbstractHumanPlayer):


    def choseMove(self, board, moves, observable=None, incheck=False):
        """
        Asks user to input a move. Checks validity of move choice and keeps asking till get a valid move
        :param availableMoves: can be supplied the moves that can be made.
        :param board: the game board being played
        :return: returns move to the game as list [fromPosition, toPosition]. It will make the move on the board so it can handle things like
        castling, en passant, pawn becoming a queen, check, checkmate
        """

        while True:
            print(f'{self.name} [{self.colour()}] please make your move [eg b2 b3]')
            print(f'("q" - quit "h" - help  "a" - possible moves "d" - redisplay board)')
            move = input('::>')
            validation = self.validateMove(move,board,moves,observable,incheck)
            if validation:
                return validation

    def promotePawnTo(self):
        choice = input(f'Please choice piece {ChessConstants.PROMOTION_OPTIONS} you want to promote pawn to:')
        if choice.upper() in ChessConstants.PROMOTION_OPTIONS:
            return choice
        else:
            return 'Q'
