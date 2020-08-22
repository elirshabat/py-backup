from argparse import ArgumentParser
import yaml
import os.path
from tqdm import tqdm
from shutil import copyfile
from zipfile import ZipFile, ZIP_DEFLATED
from datetime import datetime
from pybackup.tools import is_newer, relative_path, list_subtree, get_hist_time, list_files


def remove_deleted_files(dest_root, src_root, recursive):
    """
    Remove destination files that were deleted from source.
    Args:
        dest_root: Destination root.
        src_root: Source root.
        recursive: Whether or not to operate recursively.
    """
    dest_subtree = list_subtree(dest_root, recursive=recursive)
    src_root_dir = os.path.split(src_root)[0] if os.path.isfile(src_root) else src_root
    for dest_file in dest_subtree:
        rel_path = relative_path(dest_file, dest_root)
        src_file = os.path.join(src_root_dir, rel_path)
        if not os.path.exists(src_file):
            os.remove(dest_file)


def sync_files(src_root, dest_root, recursive, sync_type):
    """
    Synchronizing files from the source to destination.
    Args:
        src_root: Source root.
        dest_root: Destination root.
        recursive: Whether or not to operate recursively.
        sync_type: Type of synchronization to perform (variable, incremental).
    """
    if sync_type == "variable":
        remove_deleted_files(dest_root, src_root, recursive)

    src_root_dir = os.path.split(src_root)[0] if os.path.isfile(src_root) else src_root
    src_files = list_subtree(src_root, recursive=recursive)

    for src_path in tqdm(src_files, desc="Synchronize {} -> {}".format(src_root, dest_root)):
        rel_path = relative_path(src_path, src_root_dir)
        dest_path = os.path.abspath(os.path.join(dest_root, rel_path))
        if is_newer(src_path, dest_path):
            dest_dir = os.path.split(dest_path)[0]
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)

            if os.path.exists(dest_path) and sync_type != "variable":
                # TODO: use log instead of print
                print(f"WARNING - destination file already exists in a non-variable backup - {src_path} -> {dest_path}")
                continue

            copyfile(src_path, dest_path)


def remove_old_history(hist_dir, keep_last=3, expired_days=365):
    """
    Remove old history files from the given directory.
    Args:
        hist_dir: history directory.
        keep_last: number of minimum files to keep.
        expired_days: files older than this number of days will be removed in case it does not violate the minimum
            history instances.
    """
    zip_files = [os.path.join(hist_dir, f) for f in list_files(hist_dir) if f.endswith(".zip")]
    zip_files = sorted(zip_files, reverse=True, key=lambda f: get_hist_time(f))[keep_last:]

    now = datetime.now()

    for f in zip_files:
        td = now - get_hist_time(f)
        if td.days > expired_days:
            os.remove(f)


def run_backup(cfg, dest_root, src_root):
    """
    Run backup.
    Args:
        cfg: Backup configuration.
        dest_root: Destination root.
        src_root: Source root.
    """
    content_dir = os.path.join(dest_root, "content")
    history_dir = os.path.join(dest_root, "history")
    if not os.path.exists(history_dir):
        os.mkdir(history_dir)
    if not os.path.exists(content_dir):
        os.mkdir(content_dir)

    archive_filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.zip")
    with ZipFile(os.path.join(history_dir, archive_filename), "w", compression=ZIP_DEFLATED) as zip_f:
        for dest_name in cfg['backup_sources']:
            dest_dir = os.path.join(content_dir, dest_name)
            if not os.path.exists(dest_dir):
                os.mkdir(dest_dir)
            src_cfg = cfg['backup_sources'][dest_name]
            src_dir = os.path.abspath(os.path.join(src_root, src_cfg['path']))
            sync_files(src_root=src_dir, recursive=src_cfg['recursive'], dest_root=dest_dir,
                       sync_type=src_cfg['backup_type'])
            if src_cfg['backup_type'] == 'variable':
                dest_subtree = list_subtree(dest_dir, recursive=True)
                for file in tqdm(dest_subtree, desc="Save {} to history".format(dest_dir)):
                    rel_path = relative_path(file, content_dir)
                    zip_f.write(file, rel_path)

    remove_old_history(history_dir)


def _main():
    config_file = args.config_file
    dest_root = args.dest_dir
    src_root = args.src_root

    if not os.path.isdir(dest_root):
        raise IOError("Destination dir does not exists: {}".format(dest_root))

    with open(config_file, "rt") as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)

    run_backup(cfg, dest_root, src_root)


if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument("--config-file", "-c", required=True, help="Path to backup config file")
    arg_parser.add_argument("--dest-dir", "-o", required=True, help="Path to destination directory")
    arg_parser.add_argument("--src-root", "-s", default="",
                            help="Path to root of source directory. "
                                 "Assumes that all source paths in config file are relative w.r.t. this path")
    args = arg_parser.parse_args()

    _main()
