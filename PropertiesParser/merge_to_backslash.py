def merge_to_double_backslash(input_list):
    output_list = input_list[:1]
    for item in input_list[1:]:
        if output_list[-1].endswith('\\'):
            output_list[-1] += item
        else:
            output_list.append(item)

    return output_list
