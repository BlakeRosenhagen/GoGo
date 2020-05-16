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


# tag::strings[]
class DiskString():  # <1>
    def __init__(self, color, disks):
        self.color = color
        self.disks = set(disks)

    def merged_with(self, disk_string):  # <2>
        assert disk_string.color == self.color
        combined_disks = self.disks | disk_string.disks
        return DiskString(self.color, combined_disks)

    @property
    def num_disks(self):
        return len(self.disks)

    def __eq__(self, other):
        return isinstance(other, DiskString) and \
            self.color == other.color and \
            self.disks == other.disks

class Board():  # <1>
    def __init__(self, num_rows, num_cols):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self._grid = {}


    def place_stone(self, player, point):
        assert self.is_on_grid(point)
        assert self._grid.get(point) is None
        adjacent_same_color = []
        adjacent_opposite_color = []
        liberties = []
        for neighbor in point.neighbors():  # <1>
            if not self.is_on_grid(neighbor):
                continue
            neighbor_string = self._grid.get(neighbor)
            if neighbor_string is None:
                liberties.append(neighbor)
            elif neighbor_string.color == player:
                if neighbor_string not in adjacent_same_color:
                    adjacent_same_color.append(neighbor_string)
            else:
                if neighbor_string not in adjacent_opposite_color:
                    adjacent_opposite_color.append(neighbor_string)
        new_string = DiskString(player, [point], liberties)

        for same_color_string in adjacent_same_color:  # <1>
            new_string = new_string.merged_with(same_color_string)
        for new_string_point in new_string.stones:
            self._grid[new_string_point] = new_string
        for other_color_string in adjacent_opposite_color:  # <2>
            other_color_string.remove_liberty(point)
        for other_color_string in adjacent_opposite_color:  # <3>
            if other_color_string.num_liberties == 0:
                self._remove_string(other_color_string)

    def _remove_string(self, string):
        for point in string.stones:
            for neighbor in point.neighbors():  # <1>
                neighbor_string = self._grid.get(neighbor)
                if neighbor_string is None:
                    continue
                if neighbor_string is not string:
                    neighbor_string.add_liberty(point)
            del(self._grid[point])

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
        return GameState(next_board, self.next_player.other, self, move)

    @classmethod
    def new_game(cls, board_size):
        if isinstance(board_size, int):
            board_size = (board_size, board_size)
        board = Board(*board_size)
        return GameState(board, Player.black, None, None)
# <1> Return the new GameState after applying the move.
# end::game_state[]

# tag::self_capture[]
    def is_move_self_capture(self, player, move):
        if not move.is_play:
            return False
        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, move.point)
        new_string = next_board.get_go_string(move.point)
        return new_string.num_liberties == 0
# end::self_capture[]

# tag::is_ko[]
    @property
    def situation(self):
        return (self.next_player, self.board)

    def does_move_violate_ko(self, player, move):
        if not move.is_play:
            return False
        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, move.point)
        next_situation = (player.other, next_board)
        past_state = self.previous_state
        while past_state is not None:
            if past_state.situation == next_situation:
                return True
            past_state = past_state.previous_state
        return False
# end::is_ko[]

    def does_move_capture(self, move):
        pass

# tag::is_valid_move[]
    def is_valid_move(self, move):
        if self.is_over():
            return False
        if move.is_pass or move.is_resign:
            return True
        return (
            self.board.get(move.point) is None and
            not does_move_capture)
# end::is_valid_move[]

# tag::is_over[]
    def is_over(self):
        if self.last_move is None:
            return False
        if self.last_move.is_resign:
            return True
        second_last_move = self.previous_state.last_move
        if second_last_move is None:
            return False
        return self.last_move.is_pass and second_last_move.is_pass
# end::is_over[]

    def legal_moves(self):
        moves = []
        for row in range(1, self.board.num_rows + 1):
            for col in range(1, self.board.num_cols + 1):
                move = Move.play(Point(row, col))
                if self.is_valid_move(move):
                    moves.append(move)
        # These two moves are always legal.
        moves.append(Move.pass_turn())
        moves.append(Move.resign())

        return moves

    def winner(self):
        if not self.is_over():
            return None
        if self.last_move.is_resign:
            return self.next_player
        game_result = compute_game_result(self)
        return game_result.winner
