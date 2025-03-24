import codecs
the_file = codecs.open('TheFile.txt', 'r', encoding='utf-8')
for line in the_file:
    line = line.rstrip()
    if not line.startswith('azxdgasdfgdsnvhkmcvaz'):
        continue
    print(line)
