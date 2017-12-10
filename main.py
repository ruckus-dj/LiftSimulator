import getopt
import sys
from enum import Enum
from multiprocessing import Process, Queue, Value, Array, Lock
from time import sleep
import builtins
from datetime import datetime
from threading import Thread


class Direction(Enum):
    UP = 1
    DOWN = 2


def print(val):
    builtins.print(datetime.now(), val)


class WayFinder(Process):

    def __init__(self, target, flour, flour_count):
        super().__init__()
        self.call = Array('i', [0 for _ in range(flour_count)])
        self.move = Array('i', [0 for _ in range(flour_count)])
        self._flour_count = flour_count
        self._target = target
        self._stop = True
        self._flour = flour
        self._need_update = Value('b', False)
        self._direction = Direction.UP

    def empty(self):
        return (sum(self.call) + sum(self.move)) == 0

    def updated(self):
        self._need_update.value = True

    def run(self):
        while True:
            while self._need_update.value:
                self._need_update.value = False
                self.call[self._flour.value - 1] = 0
                self.move[self._flour.value - 1] = 0
                if self._direction == Direction.UP:
                    for i in range(self._flour.value, self._flour_count):
                        if self.call[i] or self.move[i]:
                            self._target.value = i + 1
                            break
                        self._direction = Direction.DOWN
                if self._direction == Direction.DOWN:
                    for i in range(0, self._flour.value):
                        if self.call[i] or self.move[i]:
                            self._target.value = i + 1
                            break
                        self._direction = Direction.UP
            sleep(0.0001)


class Lift(Process):

    def __init__(self, flour_count, flour_height, speed, doors_delay):
        super().__init__()
        self._queue_call = Queue()
        self._queue_move = Queue()
        self._flour_count = flour_count
        self._flour_height = flour_height
        self._speed = speed
        self._doors_delay = doors_delay
        self._flour_pass_time = flour_height / speed
        self._flour = Value('i', 1)
        self._target = Value('i', 1)
        self._way_finder = WayFinder(self._target, self._flour, flour_count)
        self._way_finder.start()

    def call(self, flour):
        if flour < 1 or flour > self._flour_count:
            print('Error: Lift called to the {} flour, but we have flours from 1 to {}'
                  .format(flour, self._flour_count))
            return
        self._way_finder.call[flour - 1] = 1
        self._way_finder.updated()

    def move(self, flour):
        if flour < 1 or flour > self._flour_count:
            print('Error: Lift called to the {} flour, but we have flours from 1 to {}'
                  .format(flour, self._flour_count))
            return
        self._way_finder.move[flour - 1] = 1
        self._way_finder.updated()

    def _print_flour(self):
        print('{} flour'.format(self._flour.value))

    def _print_doors(self):
        print('Doors opened')
        sleep(self._doors_delay)
        print('Doors closed')

    def run(self):
        try:
            while True:
                while not self._way_finder.empty():
                    if self._target.value != self._flour.value:
                        sleep(self._flour_pass_time)
                        self._flour.value += 1 if self._target.value > self._flour.value else -1
                        self._print_flour()
                    if self._target.value == self._flour.value:
                        self._way_finder.updated()
                        self._print_doors()
                sleep(0.0001)

        except KeyboardInterrupt:
            pass


def main():
    args = sys.argv[1:]
    try:
        opts, args = getopt.getopt(args, 'c:f:s:d:', ['flour_count=', 'flour_height=', 'speed=', 'doors_delay='])
    except getopt.GetoptError:
        print('usage: {} -c <flour_count> -f <flour_height> -s <speed> -d <doors_delay>'.format(sys.argv[1]))
        sys.exit(2)
    if len(opts) != 4:
        print('usage: {} -c <flour_count> -f <flour_height> -s <speed> -d <doors_delay>'.format(sys.argv[1]))
        sys.exit(2)
    flour_count = 0
    flour_height = 0
    speed = 0
    doors_delay = 0
    for opt, arg in opts:
        if opt in ['-c', '--flour_count']:
            if int(arg) < 5 or int(arg) > 20:
                print('Error: Incorrect flour count. Must be from 5 to 20.')
                sys.exit(2)
            flour_count = int(arg)
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
                    lift.move(int(flour))
                elif order == 'c':
                    lift.call(int(flour))
            except ValueError:
                pass
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
