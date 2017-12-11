import getopt
import sys
from enum import Enum
from time import sleep
import builtins
from datetime import datetime
from threading import Thread


class Direction(Enum):
    UP = 1
    DOWN = 2
    STOP = 3
    OPEN_DOORS = 4


def print(val):
    builtins.print(datetime.now(), val)


class WayFinder(Thread):

    def __init__(self, flour, flour_count):
        super().__init__()
        self._call = [0 for _ in range(flour_count)]
        self._move = [0 for _ in range(flour_count)]
        self._flour_count = flour_count
        self._target = 0
        self._stop = True
        self._flour = flour
        self._direction = Direction.UP

    def empty(self):
        return (sum(self._call) + sum(self._move)) == 0

    def call(self, flour):
        self._call[flour] = 1

    def move(self, flour):
        self._move[flour] = 1

    def arrived(self):
        self._call[self._flour.value] = 0
        self._move[self._flour.value] = 0

    def get_action(self):
        return self._direction


class Lift(Thread):

    def __init__(self, flour_count, flour_height, speed, doors_delay):
        super().__init__()
        self._flour_count = flour_count
        self._doors_delay = doors_delay
        self._flour_pass_time = flour_height / speed
        self._flour = 0
        self._direction = Direction.UP

    def call(self, flour):
        if flour < 0 or flour >= self._flour_count:
            print('Error: Lift called to the {} flour but we have flours from 1 to {}'
                  .format(flour + 1, self._flour_count))
            return
        self._way_finder.call(flour)

    def move(self, flour):
        if flour < 0 or flour >= self._flour_count:
            print('Error: Lift called to the {} flour but we have flours from 1 to {}'
                  .format(flour + 1, self._flour_count))
            return
        self._way_finder.move(flour)

    def _print_flour(self):
        print('{} flour'.format(self._flour + 1))

    def _print_doors(self):
        print('Doors opened')
        sleep(self._doors_delay)
        print('Doors closed')

    def run(self):
        try:
            while True:
                action = self._way_finder.get_action()

                if action == Direction.DOWN:
                    sleep(self._flour_pass_time)
                    self._flour -= 1
                    self._print_flour()
                elif action == Direction.UP:
                    sleep(self._flour_pass_time)
                    self._flour += 1
                    self._print_flour()
                elif action == Direction.OPEN_DOORS:
                    self._print_doors()
                else:
                    sleep(0.0001)
        except KeyboardInterrupt:
            pass


def main():
    args = sys.argv[1:]
    try:
        opts, args = getopt.getopt(args, 'c:f:s:d:', ['flour_count=', 'flour_height=', 'speed=', 'doors_delay='])
    except getopt.GetoptError:
        print('usage: python {} -c <flour_count> -f <flour_height> -s <speed> -d <doors_delay>'.format(sys.argv[0]))
        sys.exit(2)
    if len(opts) != 4:
        print('usage: python {} -c <flour_count> -f <flour_height> -s <speed> -d <doors_delay>'.format(sys.argv[0]))
        sys.exit(2)
    flour_count = 0
    flour_height = 0
    speed = 0
    doors_delay = 0
    for opt, arg in opts:
        if opt in ['-c', '--flour_count']:
            try:
                if int(arg) < 5 or int(arg) > 20:
                    print('Error: Incorrect flour count. Must be integer from 5 to 20.')
                    sys.exit(2)
                flour_count = int(arg)
            except ValueError:
                print('Error: Incorrect flour count. Must be integer from 5 to 20.')
        if opt in ['-f', '--flour_height']:
            if float(arg) <= 0:
                print('Error: Incorrect flour height. Must be greater then 0.')
                sys.exit(2)
            flour_height = float(arg)
        if opt in ['-s', '--speed']:
            if float(arg) <= 0:
                print('Error: Incorrect speed. Must be greater then 0.')
                sys.exit(2)
            speed = float(arg)
        if opt in ['-d', '--doors_delay']:
            if float(arg) <= 0:
                print('Error: Incorrect doors delay. Must be greater then 0.')
                sys.exit(2)
            doors_delay = float(arg)
    lift = Lift(flour_count, flour_height, speed, doors_delay)
    lift.start()
    try:
        while True:
            try:
                order, flour = input().split()
                if order == 'm':
                    lift.move(int(flour) - 1)
                elif order == 'c':
                    lift.call(int(flour) - 1)
            except ValueError:
                pass
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
