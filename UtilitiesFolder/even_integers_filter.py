from typing import List


def is_even(value: int) -> bool:
    """Check if a value is even.

    Args:
        value: An integer value.

    Returns:
        True if the value is even, False otherwise.
    """
    return value % 2 == 0


def filter_list(input_list: List[int]) -> None:
    """Filter a list to keep only even values.

    Modifies the input_list in-place, removing all elements that are not even.

    Args:
        input_list: A list of integers.
    """
    input_list[:] = filter(is_even, input_list)


def main() -> None:
    """Main function to demonstrate filtering a list of numbers."""
    my_list: List[int] = list(range(200))
    print(id(my_list))
    filter_list(my_list)
    print(id(my_list))
    print(my_list)


if __name__ == "__main__":
    main()


# def is_even(value: int) -> bool:
#     """Check if a value is even.
#
#     Args:
#         value: An integer value.
#
#     Returns:
#         True if the value is even, False otherwise.
#     """
#     return value % 2 == 0
#
#
# def filter_list(input_list: List[int]) -> List[int]:
#     """Filter a list to keep only even values.
#
#     Returns a new list containing only the even values from the input list.
#
#     Args:
#         input_list: A list of integers.
#
#     Returns:
#         A new list with only the even values from the input list.
#     """
#     return [num for num in input_list if is_even(num)]
#
#
# def main() -> None:
#     """Main function to demonstrate filtering a list of numbers."""
#     my_list: List[int] = list(range(200))
#     print(id(my_list))
#     filtered_list = filter_list(my_list)
#     print(id(filtered_list))
#     print(filtered_list)
#
#
# if __name__ == "__main__":
#     main()
