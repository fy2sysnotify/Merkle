from typing import List


def get_largest_number(numbers: List[int]) -> int:
    """
    Returns the largest number in a list of integers.

    :param: numbers (List[int]): A list of integers.
    :return: int: The largest number in the list.    """

    return max(numbers)


print(get_largest_number([3, 2, 8, 1, 5, 3]))
