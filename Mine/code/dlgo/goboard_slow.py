import numpy as np
# tag::imports[]
import copy
from dlgo.gotypes import Player
# end::imports[]
from dlgo.gotypes import Point
from dlgo.scoring import compute_game_result

__all__ = [
    'Board',
    'GameState',
    'Move',
]


class IllegalMoveError(Exception):
    pass


class DiskString():
    def __init__(self, color, disks, liberties):
        self.color = color
        self.disks = set(disks)
        self.liberties = set(liberties)
    
    def flip(self):
        return DiskString(self.color.other, self.disks, self.liberties)

    def remove_liberty(self, point):
        self.liberties.remove(point)

    def add_liberty(self, point):
        self.liberties.add(point)

    @property
    def num_liberties(self):
        return len(self.liberties)

    @property
    def is_locked(self):
        return len(self.liberties) == 0

    def __eq__(self, other):
        return isinstance(other, DiskString) and \
            self.color == other.color and \
            self.disks == other.disks and \
            self.liberties == other.liberties

class Board():
    def __init__(self, num_rows, num_cols):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self._grid = {}

    def place_stone(self, player, point):
        assert self.is_on_grid(point)
        assert self._grid.get(point) is None
        vectors = [(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]
        for vector in vectors:
            disk_line = flipable(player, point, vector)
            if len(disk_line) == 0:
                continue
            if len(disk_line) > 0:
                for disk_string in disk_line:
                    #might need to replace each in Board
                    #
                    #
                    flipped_string = disk_string.flip()
                    for point in flipped_string.disks:
                        self._grid[point] = flipped_string
        liberties = []
        for neighbor in point.neighbors():
            if not self.is_on_grid(neighbor):
                continue
            neighbor_string = self._grid.get(neighbor)
            if neighbor_string is None:
                liberties.append(neighbor)
           
            if neighbor_string is not None:
                neighbor_string.remove_liberty(point)
        new_string = DiskString(player, [point], liberties)
        for new_string_point in new_string.disks:
            self._grid[new_string_point] = new_string

    def flipable(self, player, point, vector, disk_line={}, count=0):
        count = count
        disk_line = disk_line
        next_point = self._grid.get(point.next_in_line(vector))
        if next_point.color == player.other:
            disk_line[str(count)] = next_point
        elif next_point.color == player:
            return disk_line
        elif next_point.color is None:
            disk_line = {}
            return disk_line
        count += 1
        flipable(self, player, point, vector, disk_line, count)

    """
    def _remove_string(self, string):
        for point in string.disks:
            for neighbor in point.neighbors():  # <1>
                neighbor_string = self._grid.get(neighbor)
                if neighbor_string is None:
                    continue
                if neighbor_string is not string:
                    neighbor_string.add_liberty(point)
            del(self._grid[point])
    """
        

    def is_on_grid(self, point):
        return 1 <= point.row <= self.num_rows and \
            1 <= point.col <= self.num_cols

    def get(self, point):  # <1>
        string = self._grid.get(point)
        if string is None:
            return None
        return string.color

    def get_go_string(self, point):  # <2>
        string = self._grid.get(point)
        if string is None:
            return None
        return string

    def count_disks(self):
        black_disks = 0
        white_disks = 0
        no_disks = 0
        for row in range(self.num_cols):
            for col in range(self.num_rows):
                disk = board.get(gotypes.Point(row=row, col=col))
                if disk == Player.black:
                    black_disks += 1
                elif disk == Player.white:
                    white_disks += 1
                else:
                    no_disks += 1
        return black_disks, white_disks, no_disks


    def __eq__(self, other):
        return isinstance(other, Board) and \
            self.num_rows == other.num_rows and \
            self.num_cols == other.num_cols and \
            self._grid == other._grid


# tag::moves[]
class Move():  # <1>
    def __init__(self, point=None, is_pass=False):
        assert (point is not None) ^ is_pass
        self.point = point
        self.is_play = (self.point is not None)
        self.is_pass = is_pass

    @classmethod
    def play(cls, point):  # <2>
        return Move(point=point)

    @classmethod
    def pass_turn(cls):  # <3>
        return Move(is_pass=True)

# tag::game_state[]
class GameState():
    def __init__(self, board, next_player, previous, move):
        self.board = board
        self.next_player = next_player
        self.previous_state = previous
        self.last_move = move

    def apply_move(self, move):  # <1>
        if move.is_play:
            next_board = copy.deepcopy(self.board)
            next_board.place_stone(self.next_player, move.point)
        else:
            next_board = self.board
        #in future to save a list of moves, modify what happens in return
        # or use the last generated gamestate and recersively bring out data
        return GameState(next_board, self.next_player.other, self, move)

    @classmethod
    def new_game(cls, board_size):
        if isinstance(board_size, int):
            board_size = (board_size, board_size)
        board = Board(*board_size)
        return GameState(board, Player.black, None, None)

    def is_move_self_capture(self, player, move):
        if not move.is_play:
            return False
        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, move.point)
        new_string = next_board.get_go_string(move.point)
        return new_string.num_liberties == 0

    @property
    def situation(self):
        return (self.next_player, self.board)

    def does_move_capture(self, player, move):
        if not move.is_play:
            return False
        captured = 0
        vectors = [(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]
        for vector in vectors:
            disk_line = self.board.flipable(player, move.point, vector)
            captured += len(disk_line)
        return captured >= 0

    """ next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, move.point)
        if player == Player.black:
            return self.board.count_disks[1] + 1 < next_board.count_disks[1]
        elif player == Player.white:
            return self.board.count_disks[2] + 1 < next_board.count_disks[2]
    """
    def is_valid_move(self, move):
        if self.is_over():
            return False
        if move.is_pass:
            return True
        return (
            self.board.get(move.point) is None and
            self.does_move_capture(self.next_player, move))

    def is_over(self):
        if self.last_move is None:
            return False
        second_last_move = self.previous_state.last_move
        if second_last_move is None:
            return False
        return self.last_move.is_pass and second_last_move.is_pass

    def legal_moves_narrowed(self):
        "narrow down the search to oppornent's disk's liberties"
        moves = []
        opponents_liberties = []
        for  string in self.board._grid:
            if string.color == self.next_player:
                continue
            elif string.color == self.next_player.other:
                for liberty in string.liberties:
                    opponents_liberties.append(liberty)
        
        #for liberty in opponents_liberties:
        #    move = Move.play(liberty)
        #    if is_valid_move(move):
        #        moves.append(move)
        #for row in self.board.num_rows:
        #    for col in self.board.num_col:
        #        move = Move.play(Point(row, col))
        #        if self.is_valid_move(move):
        #            moves.append(move)
        #moves.append(Move.pass_turn())

        return moves

    #def legal_moves(self):
    #    moves = []
    #    for row in range(1, self.board.num_rows + 1):
    #        for col in range(1, self.board.num_cols + 1):
    #            move = Move.play(Point(row, col))
    #            if self.is_valid_move(move):
    #                moves.append(move)
    #    # These two moves are always legal.
    #    moves.append(Move.pass_turn())
    #    moves.append(Move.resign())

    #    return moves

    def winner(self):
        if not self.is_over():
            return None
        if self.last_move.is_resign:
            return self.next_player
        game_result = compute_game_result(self)
        return game_result.winner
