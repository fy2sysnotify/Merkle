import difflib
from datetime import datetime

first_file = 'old_source_2022-06-30_09-19-11.html'
second_file = 'original_source.html'
first_file_lines = open(first_file, encoding='utf-8').readlines()
second_file_lines = open(second_file, encoding='utf-8').readlines()
difference = difflib.HtmlDiff().make_file(first_file_lines, second_file_lines, first_file, second_file)
with open(f'difference_report{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.html', 'w', encoding='utf-8') as difference_report:
    difference_report.write(difference)
