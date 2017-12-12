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
    CLOSE_DOORS = 5


class Direction(Enum):
    UP = 1
    DOWN = 2


class DoorsState(Enum):
    OPENED = 1
    CLOSED = 2


class Lift(Thread):

    def __init__(self, flour_count, flour_height, speed, doors_delay):
        super().__init__()
        self._flour_count = flour_count
        self._doors_delay = doors_delay
        self._flour_pass_time = flour_height / speed
        self._flour = 0
        self._action = Action.STOP
        self._direction = Direction.UP.value
        self._doors_state = DoorsState.CLOSED
        self._call = [0 for _ in range(flour_count)]
        self._move = [0 for _ in range(flour_count)]
        self._btn_lock = Lock()
        self._move_lock = Lock()
        self._recalculate_needed = Event()
        self._moving = False

    def call(self, flour, direction):
        if flour < 0 or flour >= self._flour_count:
            print('Error: Lift called to the {} flour but we have flours from 1 to {}'
                  .format(flour + 1, self._flour_count))
        else:
            with self._btn_lock:
                self._call[flour] = direction
            self._recalculate_needed.set()

    def move(self, flour):
        if flour < 0 or flour >= self._flour_count:
            print('Error: Lift called to the {} flour but we have flours from 1 to {}'
                  .format(flour + 1, self._flour_count))
        else:
            with self._btn_lock:
                self._move[flour] = 1
            self._recalculate_needed.set()

    def _print_flour(self):
        print('{} flour'.format(self._flour + 1))

    def _recalculate_next_step(self):
        with self._move_lock, self._btn_lock:
            if sum(self._move) + sum(self._call) == 0:
                self._action = Action.STOP
                return
            if self._direction == Direction.UP.value and \
                    sum(self._move[self._flour:]) + sum(self._call[self._flour + 1:]) == 0 and \
                    self._call[self._flour] != self._direction:
                self._direction = Direction.DOWN.value
            elif self._direction == Direction.DOWN.value and \
                    sum(self._move[:self._flour - 1]) + sum(self._call[:self._flour - 1]) == 0 and \
                    self._call[self._flour] != self._direction:
                self._direction = Direction.UP.value
            if self._direction == Direction.UP.value:
                if self._move[self._flour] or self._call[self._flour] == self._direction:
                    if self._doors_state == DoorsState.CLOSED:
                        self._action = Action.OPEN_DOORS
                    else:
                        self._move[self._flour] = 0
                        self._call[self._flour] = 0
                        self._action = Action.CLOSE_DOORS
                else:
                    for i in range(self._flour + 1, self._flour_count):
                        if self._move[i] or self._call[i] == self._direction:
                            self._action = Action.UP
            if self._direction == Direction.DOWN.value:
                if self._move[self._flour] or self._call[self._flour] == self._direction:
                    if self._doors_state == DoorsState.CLOSED:
                        self._action = Action.OPEN_DOORS
                    else:
                        self._move[self._flour] = 0
                        self._call[self._flour] = 0
                        self._action = Action.CLOSE_DOORS
                else:
                    for i in range(self._flour - 1, 0, -1):
                        if self._move[i] or self._call[i] == self._direction:
                            self._action = Action.DOWN

    def run(self):
        try:
            next_time = time()
            while True:
                start_time = time()
                if start_time >= next_time:
                    if self._moving:
                        self._print_flour()
                    with self._move_lock:
                        if self._action == Action.DOWN:
                            self._moving = True
                            self._flour -= 1
                            next_time += self._flour_pass_time
                        elif self._action == Action.UP:
                            self._moving = True
                            self._flour += 1
                            next_time += self._flour_pass_time
                        elif self._action == Action.OPEN_DOORS:
                            self._moving = False
                            print('Doors opened')
                            self._doors_state = DoorsState.OPENED
                            next_time += self._doors_delay
                        elif self._action == Action.CLOSE_DOORS:
                            self._moving = False
                            print('Doors closed')
                            self._doors_state = DoorsState.CLOSED
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
                elif order == 'cu':
                    lift.call(int(flour) - 1, Direction.UP.value)
                elif order == 'cd':
                    lift.call(int(flour) - 1, Direction.DOWN.value)
            except ValueError:
                pass
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
