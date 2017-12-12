import getopt
import sys
from enum import Enum
from time import sleep, time
from threading import Thread, Lock, Event


class Action(Enum):
    UP = 1
    DOWN = 2
    STOP = 3
    OPEN_DOORS = 4


class Direction(Enum):
    UP = 1
    DOWN = 2


class DoorsState(Enum):
    OPENED = 1
    CLOSED = 2


class Lift(Thread):

    def __init__(self, floor_count, floor_height, speed, doors_delay):
        super().__init__()
        self._floor_count = floor_count
        self._doors_delay = doors_delay
        self._floor_pass_time = floor_height / speed
        self._floor = 0
        self._action = Action.STOP
        self._direction = Direction.UP.value
        self._doors_state = DoorsState.CLOSED
        self._call = [0 for _ in range(floor_count)]
        self._move = [0 for _ in range(floor_count)]
        self._btn_lock = Lock()
        self._move_lock = Lock()
        self._recalculate_needed = Event()
        self._moving = False

    def call(self, floor, direction):
        if floor < 0 or floor >= self._floor_count:
            print('Error: Lift called to the {} floor but we have floors from 1 to {}'
                  .format(floor + 1, self._floor_count))
        else:
            with self._btn_lock:
                self._call[floor] |= direction
            self._recalculate_needed.set()

    def move(self, floor):
        if floor < 0 or floor >= self._floor_count:
            print('Error: Lift called to the {} floor but we have floors from 1 to {}'
                  .format(floor + 1, self._floor_count))
        else:
            with self._btn_lock:
                self._move[floor] = 1
            self._recalculate_needed.set()

    def _print_floor(self):
        print('{} floor'.format(self._floor + 1))

    def _recalculate_next_step(self):
        with self._move_lock, self._btn_lock:
            if self._doors_state == DoorsState.OPENED:
                self._move[self._floor] = 0
                self._call[self._floor] &= ~self._direction

            if sum(self._move) + sum(self._call) == 0:
                self._action = Action.STOP
                return

            if self._direction == Direction.UP.value and \
                    sum(self._move[self._floor:]) + sum(self._call[self._floor + 1:]) == 0 and \
                    self._call[self._floor] & self._direction == 0:
                self._direction = Direction.DOWN.value
            elif self._direction == Direction.DOWN.value and \
                    sum(self._move[:self._floor - 1]) + sum(self._call[:self._floor - 1]) == 0 and \
                    self._call[self._floor] & self._direction == 0:
                self._direction = Direction.UP.value

            if self._direction == Direction.UP.value:
                if self._move[self._floor] or self._call[self._floor] & self._direction != 0:
                    if self._doors_state == DoorsState.CLOSED:
                        self._action = Action.OPEN_DOORS
                else:
                    for i in range(self._floor + 1, self._floor_count):
                        if self._move[i] or self._call[i] & self._direction != 0:
                            self._action = Action.UP
            elif self._direction == Direction.DOWN.value:
                if self._move[self._floor] or self._call[self._floor] & self._direction != 0:
                    if self._doors_state == DoorsState.CLOSED:
                        self._action = Action.OPEN_DOORS
                else:
                    for i in range(self._floor - 1, -1, -1):
                        if self._move[i] or self._call[i] & self._direction != 0:
                            self._action = Action.DOWN

    def run(self):
        try:
            next_time = time()
            while True:
                start_time = time()
                if start_time >= next_time:
                    if self._moving:
                        self._print_floor()
                    if self._doors_state == DoorsState.OPENED:
                        print('Doors closed')
                        self._doors_state = DoorsState.CLOSED
                    with self._move_lock:
                        if self._action == Action.DOWN:
                            self._moving = True
                            self._floor -= 1
                            next_time += self._floor_pass_time
                        elif self._action == Action.UP:
                            self._moving = True
                            self._floor += 1
                            next_time += self._floor_pass_time
                        elif self._action == Action.OPEN_DOORS:
                            self._moving = False
                            print('Doors opened')
                            self._doors_state = DoorsState.OPENED
                            next_time += self._doors_delay
                        else:
                            self._moving = False
                            next_time = start_time
                            sleep(0.0001)
                with self._btn_lock:
                    Thread(target=self._recalculate_next_step).start()
                self._recalculate_needed.clear()
                self._recalculate_needed.wait(next_time - time())
        except KeyboardInterrupt:
            pass


def main():
    args = sys.argv[1:]
    try:
        opts, args = getopt.getopt(args, 'c:f:s:d:', ['floor_count=', 'floor_height=', 'speed=', 'doors_delay='])
    except getopt.GetoptError:
        print('usage: python {} -c <floor_count> -f <floor_height> -s <speed> -d <doors_delay>'.format(sys.argv[0]))
        sys.exit(2)
    if len(opts) != 4:
        print('usage: python {} -c <floor_count> -f <floor_height> -s <speed> -d <doors_delay>'.format(sys.argv[0]))
        sys.exit(2)
    floor_count = 0
    floor_height = 0
    speed = 0
    doors_delay = 0
    for opt, arg in opts:
        if opt in ['-c', '--floor_count']:
            try:
                if int(arg) < 5 or int(arg) > 20:
                    print('Error: Incorrect floor count. Must be integer from 5 to 20.')
                    sys.exit(2)
                floor_count = int(arg)
            except ValueError:
                print('Error: Incorrect floor count. Must be integer from 5 to 20.')
        if opt in ['-f', '--floor_height']:
            try:
                if float(arg) <= 0:
                    print('Error: Incorrect floor height. Must be float value greater then 0.')
                    sys.exit(2)
                floor_height = float(arg)
            except ValueError:
                print('Error: Incorrect floor height. Must be float value greater then 0.')
        if opt in ['-s', '--speed']:
            try:
                if float(arg) <= 0:
                    print('Error: Incorrect speed. Must be float value greater then 0.')
                    sys.exit(2)
                speed = float(arg)
            except ValueError:
                print('Error: Incorrect speed. Must be float value greater then 0.')
        if opt in ['-d', '--doors_delay']:
            try:
                if float(arg) <= 0:
                    print('Error: Incorrect doors delay. Must be float value greater then 0.')
                    sys.exit(2)
                doors_delay = float(arg)
            except ValueError:
                print('Error: Incorrect doors delay. Must be float value greater then 0.')
    lift = Lift(floor_count, floor_height, speed, doors_delay)
    lift.start()
    try:
        while True:
            try:
                order, floor = input().split()
                if order == 'm':
                    lift.move(int(floor) - 1)
                elif order == 'cu':
                    lift.call(int(floor) - 1, Direction.UP.value)
                elif order == 'cd':
                    lift.call(int(floor) - 1, Direction.DOWN.value)
            except ValueError:
                pass
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
