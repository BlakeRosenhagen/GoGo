# tag::randombotimports[]
import random
from dlgo.agent.base import Agent
#import dlgo.helpers 
from dlgo.goboard_slow import Move
from dlgo.gotypes import Point
# end::randombotimports[]


__all__ = ['RandomBot']


# tag::random_bot[]
class RandomBot(Agent):
    def select_move(self, game_state):
        candidates = []
        for r in range(1, game_state.board.num_rows + 1):
            for c in range(1, game_state.board.num_cols + 1):
                candidate = Point(row=r, col=c)
                if game_state.is_valid_move(Move.play(candidate)):
                    candidates.append(candidate)
        if not candidates:
            return Move.pass_turn()
        return Move.play(random.choice(candidates))
