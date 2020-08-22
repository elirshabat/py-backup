import os
from pathlib import Path
from datetime import datetime


def relative_path(path, root):
    return str(Path(path).relative_to(root))


def list_files(dir_path):
    return [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]


def is_newer(src_file, dest_file):
    src_stat = os.stat(src_file)
    try:
        target_ts = os.stat(dest_file).st_mtime
    except FileNotFoundError:
        target_ts = 0
    return src_stat.st_mtime > target_ts + 1


def list_subtree(root_dir, recursive):
    if os.path.isfile(root_dir):
        return [root_dir]
    elif recursive:
        subtree_files = []
        for dir, _, files in os.walk(root_dir):
            for file in files:
                subtree_files.append(os.path.abspath(os.path.join(dir, file)))
        return subtree_files
    else:
        return [os.path.join(root_dir, filename) for filename in os.listdir(root_dir)]


def get_hist_time(filepath):
    filename = os.path.basename(filepath)
    time_string = os.path.splitext(filename)[0]
    return datetime.strptime(time_string, "%Y-%m-%d_%H-%M-%S")
