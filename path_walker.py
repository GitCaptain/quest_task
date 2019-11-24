from pathlib import Path
from collections import deque


class PathWalker:

    """
    Traverses the specified directory and all its subdirectories, and returns a list of the files contained therein
    """

    def __init__(self, root_path):
        self.root_path = Path(root_path)

        if not self.root_path.is_dir():
            raise NotADirectoryError("root_path should be a path to directory")

    def walk(self, path=None):

        if not path:
            path = self.root_path

        listdirs = deque()
        listdirs.append(path)

        while listdirs:
            dir = listdirs.popleft()
            for file in dir.iterdir():
                if file.is_dir():
                    listdirs.append(file)
                if file.is_file():
                    yield file


if __name__ == '__main__':

    p = PathWalker('.')

    listdir = p.walk()
    for file in listdir:
        print(file)
