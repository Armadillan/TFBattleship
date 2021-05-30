#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Bot:

    def __init__(self, ships):

        self._ships = ships

    def action(state):

        smallest = min(self._ships)

        x = 0
        y = 0

        target = state[x][y]

        while target != 0:


        return (y + 1) * 10 + (x + 1)

