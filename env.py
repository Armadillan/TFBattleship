#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

from tf_agents.environments import py_environment
from tf_agents.environments import utils
from tf_agents.specs import array_spec
from tf_agents.trajectories import time_step as ts

class PyBattleshipEnv(py_environment.PyEnvironment):

    class Ship:

        def __init__(self, location, direction, length):

            self._sunk = False

            self._status = {}

            for offset in range(length):
                self._status[
                    tuple(np.add(
                        location,
                        np.array(
                            [offset * direction, offset * (not direction)]
                            )
                        ))
                    ] = True

        def attack(self, location):

            location = tuple(location)

            if self._sunk:
                return 0

            if self._status.get(location):
                self._status[location] = False

                if not any(self._status.values()):
                    self._sunk = True
                    return 2

                return 1

            return 0

        def check(self, location):

            location = tuple(location)

            return location in self._status.keys()

        @property
        def sunk(self):
            return self._sunk

        @property
        def locations(self):
            return tuple(self._status.keys())

        def __bool__(self):
            return not self.sunk

        def __repr__(self):
            return f"{sum(self._status.values)}/{len(self._status)}"

        def __len__(self):
            return len(self._status)


    def __init__(
            self, ships = None,
            skip_invalid_actions = False,
            punish_invalid_actions = False):

        if ships is None:
            ships = [5, 4, 3, 3, 2]

        self._action_spec = array_spec.BoundedArraySpec(
            shape=(), dtype=np.int32, minimum=0, maximum=99, name='action')

        self._observation_spec = array_spec.BoundedArraySpec(
            shape=(10,10), dtype=np.int32, minimum=0, maximum=3, name='observation')

        self._episode_ended = False

        self._state = np.zeros(shape=(10,10), dtype=np.int32)

        self._already_taken_actions = []
        self._skip_invalid_actions = skip_invalid_actions
        self._punish_invalid_actions = punish_invalid_actions

        self._ships = []

        mask = np.zeros((10,10), dtype=bool)

        for length in ships:

            coords = np.random.randint(0, 10, 2)
            direction = np.random.randint(0, 2)
            while coords[0] + (length - 1) * direction > 9 or coords[1] + (length - 1) * (not direction) > 9:
                coords = np.random.randint(0, 9, 2)
                direction = np.random.randint(0, 2)
            while any([mask[coords[0] + offset * direction, coords[1] + offset * (not direction)] for offset in range(length)]):
                coords = np.random.randint(0, 9, 2)
                direction = np.random.randint(0, 2)
                while coords[0] + (length - 1) * direction > 9 or coords[1] + (length - 1) * (not direction) > 9:
                    coords = np.random.randint(0, 9, 2)
                    direction = np.random.randint(0, 2)

            self._ships.append(self.Ship(coords, direction, length))

            for offset in range(-1, length + 1):
                try:
                    mask[coords[0] + offset * direction, coords[1] + offset * (not direction)] = True
                except IndexError:
                    pass
                try:
                    mask[coords[0] + offset * direction + (not direction), coords[1] + offset * (not direction) + direction] = True
                except IndexError:
                    pass
                try:
                    mask[coords[0] + offset * direction - (not direction), coords[1] + offset * (not direction) - direction] = True
                except IndexError:
                    pass

    def action_spec(self):
        return self._action_spec

    def observation_spec(self):
        return self._observation_spec

    def _reset(self):
        self.__init__(
            ships = [len(ship) for ship in self._ships],
            skip_invalid_actions = self._skip_invalid_actions,
            punish_invalid_actions=self._punish_invalid_actions
            )
        return ts.restart(self._state)

    def _step(self, action):
        if not isinstance(action, tuple):
            action = [int(action // 10), int(action % 10)]

        if self._punish_invalid_actions and action in self._already_taken_actions:
            return ts.transition(self._state, -1)

        if self._skip_invalid_actions:
            while action in self._already_taken_actions:
                if action[0] < 9:
                    action = [action[0] + 1, action[1]]
                elif action[1] < 9:
                    action = [0, action[1] + 1]
                else:
                    action = [0, 0]

            self._already_taken_actions.append(action)

        if self._episode_ended:
            return self._reset()

        self._state[action[0], action[1]] = 1

        for ship in self._ships:
            res = ship.attack(action)
            if res:
                self._state[action[0], action[1]] = 2
                if res == 2:
                    for location in ship.locations:
                        self._state[location[0], location[1]] = 3
                break

        if np.any(self._ships):
            return ts.transition(self._state, bool(res))

        self._episode_ended = True
        return ts.termination(self._state, bool(res))

if __name__ == "__main__":
    env = PyBattleshipEnv(skip_invalid_actions=True)
    utils.validate_py_environment(env)
