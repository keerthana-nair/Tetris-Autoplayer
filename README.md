# Tetris Autoplayer
I built a Python autoplayer for a coursework version of Tetris. The coursework starter code provides the game engine and interfaces. My contribution is the autoplayer logic in player.py.

## How the autoplayer chooses its moves:
- **Right side well**: The autoplayer tries to keep the rightmost column clear for a vertical I-piece. This lets it clear four rows at once when the rest of those rows are filled. In this version, a four-line clear earns 1,600 points, compared with 25 for a single line, so the autoplayer weights a 4 row clear much more highly.
- **Weighted heuristics**: Possible moves are scored based on the scoring function, which rewards points gained and penalises the number of holes, aggregate and maximum height, bumpiness and blocks added to the well. 
- **Two piece lookahead**: The autoplayer simulates rotations and drops on copies of the board by creating a sandbox clone of the board. It uses depth-first search to evaluate placements for the current piece and the next piece when available.
- **Special features**: This version of Tetris varies from the original due to the addition of a limited number of discards and bombs. The autoplayer uses board evaluations to decide when those actions could improve its position, and can discard a piece to try for an I-piece when enough rows are ready.

## Running the autoplayer:

The autoplayer uses Python 3 and the supplied coursework game files. The autoplayer is implemented in player.py and uses the coursework board engine in board.py.

Place player.py in the coursework game directory, open a terminal there, and run:
*python visual.py*

To play manually in the same interface, run:
*python visual.py -m*

The coursework also provides a terminal interface (python cmdline.py) and a Pygame interface (python visual-pygame.py, which requires Pygame). I have found Pygame to have the fastest gameplay. Use python3 or py in these commands if that’s how Python is installed on your system.

Note: If getting errors when using pygame on a python version later than 3.13, I have found that installing python 3.13 and using the command *py -3.13 visual-pygame.py* fixes this issue.
