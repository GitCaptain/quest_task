import sys
from path_walker import PathWalker
import json
from gzip import GzipFile
from pprint import pprint


def get_formatted_dict(dct):

    VALUE = 'value'
    ID = 'id'

    user_info_list = dct[VALUE]
    dct.clear()

    for user_info in user_info_list:
        id = user_info.pop(ID)
        dct[id] = user_info

    return dct


def load_path(path):
    p = PathWalker(path)
    listfiles = p.walk()

    full_json = dict()

    for file in listfiles:
        gz = GzipFile(filename=file, mode='rb')
        cur_json = get_formatted_dict(json.load(gz))
        full_json.update(cur_json)

    return full_json


class Comparator:

    def __init__(self, path1, path2, path_res):
        self.path1 = path1
        self.path2 = path2
        self.path_res = path_res
        self.first_source_data = dict()
        self.second_source_data = dict()
        self.changes = dict()

    def do_compare(self):
        self.load_files_to_compare()
        self.compare_files()
        self.write_changes()

    def load_files_to_compare(self):
        self.first_source_data = load_path(self.path1)
        self.second_source_data = load_path(self.path2)


    def compare_files(self):
        pass

    def write_changes(self):

        CHANGES = 'changes.json'

        with open(self.path_res + '/' + CHANGES, 'w') as file:
            pprint(self.changes, stream=file)


if __name__ == '__main__':

    if len(sys.argv) < 4:
        pass

    first_source_path, second_source_path, target_path = sys.argv[1:]

    cmp = Comparator(first_source_path, second_source_path, target_path)
    cmp.do_compare()
