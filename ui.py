#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import time
# import os

import pygame
import numpy as np

class Game:

    SQUARE = True

    BACKGROUND_COLOR = "#005EB8"
    HOVERING_COLOR = "#006FDD"
    LINE_COLOR = "#C9E5FF"
    MISS_COLOR = "#000000"
    HIT_COLOR = "#E50000"
    SUNK_COLOR = "#A80606"

    def __init__(self, env):

        self.env = env

        self.w = 600
        self.h = 600

        pygame.init()

    def main(self):

        ts = self.env.reset()

        scores = []

        def state():
            try:
                return ts.observation.numpy()[0]
            except AttributeError:
                return ts.observation

        line_x_width = self.w / 200
        line_y_width = self.h / 200

        field_x_width = (self.w - line_x_width * 11) / 10
        field_y_width = (self.h - line_y_width * 11) / 10

        win = pygame.display.set_mode((self.w, self.h),  pygame.RESIZABLE)
        surface = win.copy()

        playing = True

        while playing:

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    playing = False
                    break

                if not playing:
                    break

                if event.type == pygame.VIDEORESIZE:

                        self.w, self.h = win.get_size()

                        if self.SQUARE:
                            if self.w > self.h:
                                self.w = self.h
                            else:
                                self.h = self.w

                        line_x_width = self.w / 200
                        line_y_width = self.h / 200

                        field_x_width = (self.w - line_x_width * 11) / 10
                        field_y_width = (self.h - line_y_width * 11) / 10

                        surface = win.copy()

                surface.fill(self.BACKGROUND_COLOR)

                for x in range(11):
                    pygame.draw.rect(
                        surface=surface,
                        color=self.LINE_COLOR,
                        rect = pygame.Rect(
                            x * (line_x_width + field_x_width),
                            0,
                            line_x_width,
                            self.h
                        )
                    )

                for y in range(11):
                    pygame.draw.rect(
                        surface=surface,
                        color=self.LINE_COLOR,
                        rect = pygame.Rect(
                            0,
                            y * (line_y_width + field_y_width),
                            self.w,
                            line_y_width
                        )
                    )

                mouse = pygame.mouse.get_pos()

                mouse = [
                    mouse[0] - (win.get_width()-self.w)/2,
                    mouse[1] - (win.get_height()-self.h)/2
                    ]

                for x in range(10):
                    for y in range(10):

                        if (x + 1) * line_x_width + x * field_x_width <= mouse[0] <= \
                            (x+1) * line_x_width + (x+1) * field_x_width and \
                                not state()[x, y] and \
                                    (y+1) * line_y_width + y * field_y_width <= mouse[1] <= \
                                       (y+1) * line_y_width + (y+1) * field_y_width:
                            pygame.draw.rect(
                                surface=surface,
                                color=self.HOVERING_COLOR,
                                rect=pygame.Rect(
                                    (x + 1) * line_x_width + x * field_x_width,
                                    (y+1) * line_y_width + y * field_y_width,
                                    field_x_width,
                                    field_y_width
                                )
                            )
                        #TODO DRAW Xes or Symbols
                        elif state()[x, y] == 1:
                            pygame.draw.rect(
                                surface=surface,
                                color=self.MISS_COLOR,
                                rect=pygame.Rect(
                                    (x + 1) * line_x_width + x * field_x_width,
                                    (y+1) * line_y_width + y * field_y_width,
                                    field_x_width,
                                    field_y_width
                                    )
                            )
                        elif state()[x,y] == 2:
                            pygame.draw.rect(
                                surface=surface,
                                color=self.HIT_COLOR,
                                rect=pygame.Rect(
                                    (x + 1) * line_x_width + x * field_x_width,
                                    (y+1) * line_y_width + y * field_y_width,
                                    field_x_width,
                                    field_y_width
                                    )
                            )
                        elif state()[x,y] == 3:
                            pygame.draw.rect(
                                surface=surface,
                                color=self.SUNK_COLOR,
                                rect=pygame.Rect(
                                    (x + 1) * line_x_width + x * field_x_width,
                                    (y+1) * line_y_width + y * field_y_width,
                                    field_x_width,
                                    field_y_width
                                    )
                            )

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        for x in range(10):
                            for y in range(10):

                                if (x + 1) * line_x_width + x * field_x_width <= mouse[0] <= \
                                    (x+1) * line_x_width + (x+1) * field_x_width and \
                                        not state()[x, y] and \
                                            (y+1) * line_y_width + y * field_y_width <= mouse[1] <= \
                                            (y+1) * line_y_width + (y+1) * field_y_width:
                                    ts = self.env.step((x,y))
                                    if ts.is_last():
                                        scores.append(np.count_nonzero(state()))


                win.fill(self.BACKGROUND_COLOR)
                w, h = win.get_size()
                if w > h:
                    win.blit(surface, ((w-self.w)/2,0))
                else:
                    win.blit(surface, (0, (h-self.h)/2))
                pygame.display.update()

        pygame.quit()

        return scores


if __name__ == "__main__":
    from env import PyBattleshipEnv
    import pickle
    import time
    game = Game(PyBattleshipEnv())
    scores = game.main()
    if scores:
        print("Number of games played: ",
            len(scores),
            "\nAverage score: ",
            sum(scores) / len(scores),
            sep=""
            )
        tm = time.localtime()
    with open(
            f"{tm.tm_year}-{tm.tm_mon}-{tm.tm_mday}-"\
                 + "{tm.tm_hour}_{tm.tm_min}_{tm.tm_sec}.pkl"
            ) as file:
                pickle.dump(scores, file)

