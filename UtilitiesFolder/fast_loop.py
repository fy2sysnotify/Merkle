from itertools import repeat


def execute_loop(n: int) -> None:
    """
    Executes a loop that repeats a given number of times.

    Args:
        n: The number of times to repeat the loop.
    """

    for _ in repeat(None, n):
        # do something
        pass


my_number: int = 100_000

if __name__ == '__main__':
    execute_loop(my_number)
