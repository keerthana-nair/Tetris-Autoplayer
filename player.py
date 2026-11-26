from board import Direction, Rotation, Action, Shape, Block
from random import Random
import time


class Player:
    def choose_action(self, board):
        raise NotImplementedError

class TetrisAI(Player):
    def __init__(self, seed=None):
        #initialise heuristic weights
        self.random= Random(seed)
        self.heuristicWeights= {
            "holes": -45.0,
            "bumpiness": -5.0,
            "height":-0.4,
            "maxHeight":-5.0,
            "scoreGain":0.05,
            "well": -60.0,

        }

    def choose_action(self, board):
        _, heights= self.findHoles(board)
        emergencyHeight= max(heights)>= 12
        if self.shouldTryForIPiece(board):
            return Action.Discard
        if self.shouldDiscard(board, emergencyHeight):
            return Action.Discard
        if self.shouldBomb(board, emergencyHeight):
            return Action.Bomb
        else:
            return self.findBestMoves(board)

    def countReadyforIPieceRows(self, board): #rows where all blocks are filled apart from last column
        well= board.width -1
        ready= 0
        for y in range(board.height):
            if (well, y) in board.cells:
                continue
            if all((x, y) in board.cells for x in range(well)):
                ready+= 1
        return ready

    def shouldTryForIPiece(self, board):
        threshold= 12
        if board.discards_remaining <= 0 or board.next is None:
            return False
        if board.falling.shape== Shape.B or board.next.shape== Shape.B:
            return False
        if board.falling.shape== Shape.I or board.next.shape== Shape.I:
            return False
        return (self.countReadyforIPieceRows(board)>= threshold)

    def shouldBomb(self, board, emergencyHeight):
        shouldBomb= 25
        if board.bombs_remaining <= 0 or board.next is None:
            return False
        if board.falling.shape== Shape.B or board.next.shape== Shape.B:
            return False

        dontBombScore= self.scoreBoard(board, board, emergencyHeight, 0)

        boardAfter= board.clone()
        boardAfter.falling= Block(Shape.B)
        boardAfter.next= None
        bombScore, _= self.dfs(boardAfter, board, emergencyHeight, 1, 0)

        if bombScore == float("-inf"):
            return False
        return ((bombScore- dontBombScore)>shouldBomb)

    def shouldDiscard(self, board, emergencyHeight):
        shouldDiscard= 50 #score threshold
        if board.discards_remaining <= 0 or board.next is None:
            return False
        if board.falling.shape== Shape.B or board.next.shape== Shape.B:
            return False

        dontDiscardScore, _= self.dfs(board, board, emergencyHeight, 1, 0)

        boardAfter= board.clone()
        boardAfter.discard()
        if boardAfter.next== Block(Shape.I):
            return True
        if boardAfter.falling is None:
            return False
        discardScore, _= self.dfs(boardAfter, board, emergencyHeight, 1, 0)

        if discardScore== float("-inf"):
            return False
        return ((discardScore-dontDiscardScore)>shouldDiscard)

    def findBlockPlacements(self, board, emergencyHeight):
        shape= board.falling.shape
        if shape == Shape.I or emergencyHeight:
            maxX= board.width-1
        else:
            maxX= board.width-2

        if shape == Shape.I or shape == Shape.S or shape ==Shape.Z:
            rotations= 2
        elif shape== Shape.O or shape ==Shape.B:
            rotations= 1
        else:
            rotations= 4

        placements= []
        for rotationCount in range(rotations):
            for targetX in range(board.width):
                sandbox= board.clone()
                moves= self.steerAndDrop(sandbox, rotationCount, targetX, maxX)
                if moves is not None:
                    placements.append((moves, sandbox))
        return placements
    
    def findBestMoves(self, board):

        _, heights= self.findHoles(board)
        emergencyHeight= max(heights)>= 12

        _, moves= self.dfs(board, board, emergencyHeight, 2, 1)
        if moves is None:
            return [Direction.Drop]
        return moves

    def dfs(self, board, root, emergencyHeight, depth, pieces):
        possibleMoves= []
        for moves, sandbox in self.findBlockPlacements(board, emergencyHeight):
            score= self.scoreBoard(sandbox, root, emergencyHeight, pieces)
            possibleMoves.append((score, moves, sandbox))
        if not possibleMoves:
            return float("-inf"), None

        possibleMoves.sort(key= lambda move: move[0], reverse= True) #take best move
        if depth==1:
            return possibleMoves[0][0], possibleMoves[0][1]

        bestScore= float("-inf")
        bestMoves=possibleMoves[0][1]

        for score, moves, sandbox in possibleMoves:
            if score == float("-inf"):
                continue
            if sandbox.falling is None:
                val= score
            else:
                val,_= self.dfs(sandbox, root, emergencyHeight, depth- 1, pieces +1)
            if val > bestScore:
                bestScore= val
                bestMoves= moves
        return bestScore, bestMoves

    def steerAndDrop(self, sandbox, rotationCount, targetX, maxX=None): 
        if maxX is None:
            maxX = sandbox.width -1

        moves= []

        if rotationCount== 3:
            turns= [Rotation.Anticlockwise]
        else:
            turns= [Rotation.Clockwise]*rotationCount
        for turn in turns:
            if sandbox.rotate(turn):
                return None
            moves.append(turn)

        reached= False
        for i in range(sandbox.width):
            left= sandbox.falling.left
            if left== targetX:
                reached= True
                break
            if left>targetX:
                direction= Direction.Left
                step= -1
            else:
                direction= Direction.Right
                step= 1

            if sandbox.move(direction): #landed
                return None
            newLeft= sandbox.falling.left
            if newLeft != left+step: #blocked by wall/object
                return None
            moves.append(direction)

        if not reached:
            return None #never reached target

        if sandbox.falling.right >maxX:
            return None

        sandbox.move(Direction.Drop)
        moves.append(Direction.Drop)
        return moves

    def findHoles(self, board):
        heights = [0] * board.width
        holes = 0
        for x in range(board.width):
            seen_block = False
            for y in range(board.height):
                if (x, y) in board.cells:
                    if not seen_block:
                        heights[x] = board.height - y
                        seen_block = True
                elif seen_block:
                    holes += 1
        return holes, heights

    def findCellsinWellColumn(self, board):
        well= board.width -1
        count= 0
        for (x,y) in board.cells:
            if x== well:
                count+=1
        return count

    def getBumpiness(self, aggregateHeights):
        bumpiness= 0
        for i in range(len(aggregateHeights)-1):
            difference= aggregateHeights[i]- aggregateHeights[i+1]
            bumpiness+=abs(difference)

        return bumpiness

    def scoreBoard(self, sandbox, board, emergencyHeight= False, pieces= 1):
            #score= w1(Score gained)-w2(Avg/Max column height)-w3(holes)- w4(bumpiness)- w5Ncells
            #need to have functions to calculate all of these
            w=self.heuristicWeights

            if not sandbox.alive:
                return float("-inf")

            rowsCleared= (len(board.cells)+ 4*pieces - len(sandbox.cells))// board.width
            holes, heights= self.findHoles(sandbox)
            aggregateHeights=  heights[:-1] #column except right
            
            bumpiness= self.getBumpiness(aggregateHeights)
            wellCells= self.findCellsinWellColumn(sandbox)- self.findCellsinWellColumn(board)

            score= 0.0
            safeHeight= 10
                            
            scoreGain= sandbox.score- board.score
            score+= w["scoreGain"]*scoreGain
            score+= w["holes"]*holes
            score+= w["bumpiness"]*bumpiness
            score+=w["height"]*sum(aggregateHeights)
            score+= w["maxHeight"]*max(0, max(heights)- safeHeight)

            unsafeHeight= 13
            if emergencyHeight:
                score += unsafeHeight*rowsCleared
            elif rowsCleared < 3:
                score += w["well"]* max(0, wellCells)
            return score
            

class RandomPlayer(Player):
    def __init__(self, seed=None):
        self.random = Random(seed)

    def print_board(self, board):
        print("--------")
        for y in range(24):
            s = ""
            for x in range(10):
                if (x,y) in board.cells:
                    s += "#"
                else:
                    s += "."
            print(s, y)
                

            

    def choose_action(self, board):
        #self.print_board(board)
        #time.sleep(0.5)
        if self.random.random() > 0.97:
            # 3% chance we'll discard or drop a bomb
            return self.random.choice([
                Action.Discard,
                Action.Bomb,
            ])
        else:
            # 97% chance we'll make a normal move
            return self.random.choice([
                Direction.Left,
                Direction.Right,
                Direction.Down,
                Rotation.Anticlockwise,
                Rotation.Clockwise,
            ])


SelectedPlayer = TetrisAI #RandomPlayer
