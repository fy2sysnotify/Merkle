from typing import Any

dt: dict[int | Any, str | Any] = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December"
}


def month(idx: object) -> object:
    return dt.get(idx, f"There is no {idx} month")


print(month(11))
