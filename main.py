import json
import sys
from gzip import GzipFile, open as gzopen

from path_walker import PathWalker


class Constants:
    VALUE = 'value'
    ID = 'id'
    DELETED_USER = 'Deleted'
    ADDED_USER = 'Added'
    CHANGED_ATTRIBUTE = 'ChangedAttribute'
    DELETED_ATTRIBUTE = 'DeletedAttribute'
    ADDED_ATTRIBUTE = 'AddedAttribute'
    USER_TYPE = 'userType'
    OLD_VALUE = 'oldValue'
    NEW_VALUE = 'newValue'
    ATTRIBUTE = 'attribute'


def get_formatted_dict(dct):

    """
    formats dct which returned from json.load function into more suitable form
    :param dct: dict to format
    :return: dct - formatted dict
    """

    user_info_list = dct[Constants.VALUE]
    dct.clear()

    for user_info in user_info_list:
        uid = user_info.pop(Constants.ID)
        dct[uid] = user_info

    return dct


def load_path(path):

    """
    loads all json files from archives in the path folder and all its subdirectories into one big dictionary full_json
    :param path: dir to load from
    :return: full_json - dict containing all loaded json data
    """

    p = PathWalker(path)
    listfiles = p.walk()

    full_json = dict()

    for file in listfiles:
        try:
            gz = GzipFile(filename=file, mode='rb')
        except Exception:
            raise Exception("cant open file", str(file))
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

        self.changes[Constants.ADDED_USER] = list()
        self.changes[Constants.DELETED_USER] = list()
        self.changes[Constants.DELETED_ATTRIBUTE] = list()
        self.changes[Constants.ADDED_ATTRIBUTE] = list()
        self.changes[Constants.CHANGED_ATTRIBUTE] = list()

    def do_compare(self):
        self.load_files_to_compare()
        self.compare_files()
        self.clear_changes()
        self.write_changes()

    def load_files_to_compare(self):
        """
        load all json files from given paths
        :return:
        """
        self.first_source_data = load_path(self.path1)
        self.second_source_data = load_path(self.path2)

    def compare_id(self, user_id):
        """
        compare attributes for id from first source path with the same id from second source path
        :param user_id: id to compare
        :return:
        """
        start_user = self.first_source_data[user_id]
        end_user = self.second_source_data[user_id]

        first_user_attributes = set(start_user.keys())
        second_user_attributes = set(end_user.keys())

        added_attributes = second_user_attributes - first_user_attributes
        deleted_atributes = first_user_attributes - second_user_attributes
        common_attributes = first_user_attributes.intersection(second_user_attributes)

        for attribute in added_attributes:
            self.changes[Constants.ADDED_ATTRIBUTE]\
                .append({
                    Constants.ID: user_id,
                    Constants.ADDED_ATTRIBUTE: attribute
                })

        for attribute in deleted_atributes:
            self.changes[Constants.DELETED_ATTRIBUTE]\
                .append({
                    Constants.ID: user_id,
                    Constants.DELETED_ATTRIBUTE: attribute
                })

        for attribute in common_attributes:
            if start_user[attribute] != end_user[attribute]:
                self.changes[Constants.CHANGED_ATTRIBUTE]\
                    .append({
                        Constants.ID: user_id,
                        Constants.ATTRIBUTE: attribute,
                        Constants.OLD_VALUE: start_user[attribute],
                        Constants.NEW_VALUE: end_user[attribute]
                    })

    def clear_changes(self):

        """
        if some attribute wasnt changed we dont add it in output
        :return:
        """
        possible_changes = [Constants.ADDED_USER,
                            Constants.DELETED_USER,
                            Constants.DELETED_ATTRIBUTE,
                            Constants.ADDED_ATTRIBUTE,
                            Constants.CHANGED_ATTRIBUTE]

        for change in possible_changes:
            if not self.changes.get(change):
                self.changes.pop(change)

    def compare_files(self):
        """
        compare user in files, checks whether new user was added or some old user was deleted
        :return:
        """

        first_backup_ids = set(self.first_source_data.keys())
        second_backup_ids = set(self.second_source_data.keys())

        for deleted_user_id in first_backup_ids.difference(second_backup_ids):
            self.changes[Constants.DELETED_USER]\
                .append({
                    Constants.ID: deleted_user_id,
                    Constants.USER_TYPE: self.first_source_data[deleted_user_id][Constants.USER_TYPE]
                })

        for added_user_id in second_backup_ids.difference(first_backup_ids):
            self.changes[Constants.ADDED_USER]\
                .append({
                    Constants.ID: added_user_id,
                    Constants.USER_TYPE: self.second_source_data[added_user_id][Constants.USER_TYPE]
                })

        for id in first_backup_ids.intersection(second_backup_ids):
            self.compare_id(id)

    def write_changes(self):

        """
        write changes between 2 backups into target file
        :return:
        """

        ENCODING = 'UTF-8'

        json_str = json.dumps(self.changes, indent=2)
        json_bytes = bytes(json_str, encoding=ENCODING)

        try:
            with gzopen(self.path_res, 'wb') as gzfile:
                gzfile.write(json_bytes)
        except Exception:
            raise Exception("Cant open file to write compressed data")


if __name__ == '__main__':

    if len(sys.argv) < 4:
        raise ValueError("using: first_backup_folder_path second_backup_folder_path target_backup_path")

    first_source_path, second_source_path, target_path = sys.argv[1:]

    cmp = Comparator(first_source_path, second_source_path, target_path)
    cmp.do_compare()
