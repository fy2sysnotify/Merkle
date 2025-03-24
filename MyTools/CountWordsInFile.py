filename = input('Enter File: ')
if len(filename) < 1:
    filename = 'clown.txt'
handle = open(filename)

dictionary = dict()
for line in handle:
    line = line.rstrip()
    words = line.split()
    for w in words:
        dictionary[w] = dictionary.get(w, 0) + 1

largest = -1
the_word = None
for k, v in dictionary.items():
    if v > largest:
        largest = v
        the_word = k
print('I have counted', largest, 'times', 'the word', '(', the_word, ')')