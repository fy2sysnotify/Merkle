from functools import lru_cache


@lru_cache(maxsize=1000)
def fibonacci(n: int) -> int:
    """
    Calculates the n-th Fibonacci number with a
    recursive approach and lru_cache decorator
    from the functools module to implement memoization.

    :param n:
    :return:
    """
    if type(n) != int:
        raise TypeError('n must be a positive integer')
    if n < 1:
        raise ValueError('n must be a positive integer')
    if n in {1, 2}:
        return 1
    elif n > 2:
        return fibonacci(n-1) + fibonacci(n-2)


for n in range(1, 1001):
    print(n, ':', fibonacci(n))
