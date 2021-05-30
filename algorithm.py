#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

class Bot:

    def __init__(self, ships):

        self._ships = ships

    def action(self, time_step):

        if time_step.is_last():
            return 0

        state = time_step.observation

        mask = np.zeros((10, 10), dtype=bool)

        sunk_ships = []
        sunk_tiles = []

        for y in range(10):
            for x in range(10):

                if state[x, y] in (1,2):
                    mask[x, y] = True
                elif state[x, y] == 3:
                    for mask_x in range(x-1, x+2):
                        for mask_y in range(y-1, y+2):
                            if 0 <= mask_x <= 9 \
                                and 0 <= mask_y <= 9:
                                    mask[mask_x, mask_y] = True

        for y in range(10):
            for x in range(10):
                if state[x, y] == 3 and (x, y) not in sunk_tiles:
                    sunk_tiles.append((x,y))
                    count = 1

                    right = x + 1
                    while right < 10 and state[right, y] == 3:
                        count += 1
                        sunk_tiles.append((right,y))
                        right += 1

                    down = y + 1

                    while down < 10 and state[x, down] == 3:
                        count += 1
                        sunk_tiles.append((x, down))
                        down += 1

                    sunk_ships.append(count)

        ships = []
        for ship in self._ships:
            if ship in sunk_ships:
                sunk_ships.remove(ship)
            else:
                ships.append(ship)

        smallest = min(ships)


        for y in range(10):
            for x in range(10):
                if state[x, y] == 2:

                    if(y < 9 and state[x, y + 1] == 2) \
                        or (y > 0 and state[x, y-1] == 2):

                        if y < 9:
                            up = y + 1
                            while up < 9 and state[x, up] == 2:
                                up += 1
                            if state[x, up] == 0:
                                return x * 10 + up

                        if y > 0:
                            down = y - 1
                            while down > 0 and state[x, down] == 2:
                                down -= 1
                            if state[x, down] == 0:
                                return x * 10 + down

                    if (x < 9 and state[x + 1, y] == 2) \
                        or (x > 0 and state[x-1, y] == 2):


                        if x < 9:
                            right = x + 1
                            while right < 9 and state[right, y] == 2:
                                right += 1
                            if state[right, y] == 0:
                                return right * 10 + y

                        if x > 0:
                            left = x - 1
                            while left > 0 and state[left, y] == 2:
                                left -= 1
                            if state[left, y] == 0:
                                return left * 10 + y

                    count = 1
                    up = y + 1
                    while up < 10 and state[x, up] != 1:
                        up += 1
                        count += 1
                    down = y - 1
                    while down >= 0 and state[x, down] != 1:
                        down -= 1
                        count += 1

                    if count >= smallest:

                        if y < 9:
                            up = y + 1
                            while up < 9 and state[x, up] == 2:
                                up += 1
                            if state[x, up] == 0:
                                return x * 10 + up

                        if y > 0:
                            down = y - 1
                            while down > 0 and state[x, down] == 2:
                                down -= 1
                            if state[x, down] == 0:
                                return x * 10 + down

                    if x < 9:
                        right = x + 1
                        while right < 9 and state[right, y] == 2:
                            right += 1
                        if state[right, y] == 0:
                            return right * 10 + y

                    if x > 0:
                        left = x - 1
                        while left > 0 and state[left, y] == 2:
                            left -= 1
                        if state[left, y] == 0:
                            return left * 10 + y



        possible_moves = {}

        for y in range(10):
            for x in range(10):
                if not mask[x, y]:
                    count = 1

                    right = x + 1
                    while right < 10 and not mask[right, y]:
                        count += 1
                        right += 1

                    if count >= smallest:
                        possible_moves[(x,y, 0)] = count

                    count = 1

                    down = y + 1
                    while down < 10 and not mask[x, down]:
                        count += 1
                        down += 1

                    if count >= smallest:
                        possible_moves[(x,y, 1)] = count



        # for move, count in possible_moves.items():
        #     for offset in range(1, count):

        #         for other_move, other_count in possible_moves.items():

        #             for other_offset in range(1, other_count):

        #                 if (move[0] + offset * (not move[2]),
        #                     move[1] + offset * move[2]) == \
        #                     (other_move[0] + other_offset * (not other_move[2]),
        #                      other_move[1] + other_offset * other_move[2]):

        #                         return (move[0] + offset * (not move[2])) * 10 \
        #                             + (move[1] + offset * move[2])

        move = list(possible_moves.keys())[0]
        x = move[0] + (smallest -1) * (not move[2])
        y = move[1] + (smallest -1) * (move[2])

        return x * 10 + y

if __name__ == "__main__":
    from env import PyBattleshipEnv

    game = PyBattleshipEnv()

    ts = game.reset()

    bot = Bot([5,4,3,3,2])

    game._ships = [
        PyBattleshipEnv.Ship((1,3), False, 5),
        PyBattleshipEnv.Ship((9,5), False, 4),
        PyBattleshipEnv.Ship((9,0), False, 3),
        PyBattleshipEnv.Ship((7,2), False, 3),
        PyBattleshipEnv.Ship((2,0), False, 2)
        ]



    scores = []
    while len(scores) < 1000:
        action = bot.action(ts)
        ts = game.step(action)
        # print(ts.observation, end="\n\n")

        if ts.is_last():
            scores.append(np.count_nonzero(ts.observation))

    print(sum(scores)/len(scores))
