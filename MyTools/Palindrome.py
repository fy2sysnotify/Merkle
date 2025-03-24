counter = 0
while True:
    counter += 1
    if counter > 3:
        print('=' * 19)
        print('Толкова за без пари')
        print('=' * 19)
        break
    is_palindrome = input('Моля въведете число или дума: ')
    if len(is_palindrome) < 2:
        print('Къс ти е')
    elif is_palindrome.lower() == is_palindrome.lower()[::-1]:
        print('Това е палиндром')
    else:
        print('Това не е палиндром')