import fnmatch
import os
import types


def matching_files(root_path, file_patterns, test_file_path=None):
    """
    _matching_files returns all files in the root path that match the provided patterns.
    :param file_patterns: the iterable which contains the file name patterns
    :param root_path: is the root path in which should be searched
    :return matching files in a set:
    """
    s = []
    if isinstance(file_patterns, types.StringTypes):
        file_patterns = [file_patterns]
    if not test_file_path:
        test_file_path = ""
    elif test_file_path[-1:] == "/":
        test_file_path = test_file_path[:-1]
    if not root_path:
        root_path = os.path.abspath(os.curdir)
    for dirpath, _, filenames in os.walk(root_path):
        if test_file_path in dirpath:
            for f in filenames:
                for p in file_patterns:
                    if fnmatch.fnmatch(f, p):
                        s.append(dirpath + '/' + f)
    return frozenset(s)
