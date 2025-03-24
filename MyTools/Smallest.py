smallest = None
for value in [3, 2, 4, 1, 5, 6]:
    if smallest is None or value < smallest:
        smallest = value
print(smallest)