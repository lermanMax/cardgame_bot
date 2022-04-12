from os import rename


def get_text_from(path):
    with open(path, 'r') as file:
        one_string = ''
        for line in file.readlines():
            one_string += line
    return one_string


def find_line_for_id(new_id: int, path_to_file: str):
    """Бинарный поиск линии для нового айди в списке

    Args:
        new_id (int): _description_
        path_to_file (str): _description_

    Returns:
        line, byte_before - номер линии и последний байт перед этой линией
    """
    with open(path_to_file, 'r') as file:
        first_line = 0  # номер строчки
        first_id = int(file.readline())
        first_byte = 0  # byte before first line

        last_line = sum(1 for _ in file)
        file.seek(0)
        for _ in range(last_line):
            file.readline()
        last_byte = file.tell()
        last_id = int(file.readline())

        full_size = file.tell()

        mid_line = (last_line - first_line)//2 + first_line
        mid_id = None
        mid_byte = None

        first_iter = True
        while last_line-first_line > 1 or first_iter:
            first_iter = False

            file.seek(0)
            for _ in range(mid_line):
                file.readline()
            mid_byte = file.tell()
            mid_id = int(file.readline())

            if mid_id < new_id:
                first_line, first_id, first_byte = mid_line, mid_id, mid_byte
            elif mid_id > new_id:
                last_line, last_id, last_byte = mid_line, mid_id, mid_byte
            else:  # mid_id == new_id
                return mid_line, None

            mid_line = (last_line - first_line)//2 + first_line

        if first_id < new_id < last_id:
            return last_line, last_byte
        elif new_id < first_id:
            return first_line, first_byte
        elif last_id < new_id:
            return last_line+1, full_size
        else:
            print('total_error_fuck_my_brain_blyt')
            return None, None


def put_id_in_file(new_user_id: int, path_to_file: str) -> str:
    """Сохранение айди в файле в порядке возрастания

    Args:
        new_user_id (int): _description_
        path_to_file (str): _description_

    Returns:
        str: _description_
    """
    line, byte_before = find_line_for_id(new_user_id, path_to_file)
    if byte_before is None:
        return 'exist'

    with open(path_to_file, 'r') as subscribers:
        with open('tempfile.txt', 'w') as temp:
            temp.write(subscribers.read(byte_before))
            temp.write(str(new_user_id)+'\n')
            temp.write(subscribers.read())

    rename('tempfile.txt', path_to_file)
    return 'done'


def get_id(path_to_file):
    with open(path_to_file, 'r') as file:
        for line in file:
            yield int(line)
