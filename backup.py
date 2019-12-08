from argparse import ArgumentParser
import yaml
import os.path
from tqdm import tqdm
from shutil import copyfile
from zipfile import ZipFile, ZIP_DEFLATED
from datetime import datetime
from pybackup.tools import is_newer, relative_path, list_subtree


def get_src_to_copy(src_root, dest_root, recursive):
	src_subtree = list_subtree(src_root, recursive=recursive)
	src_root_dir = os.path.split(src_root)[0] if os.path.isfile(src_root) else src_root
	src_to_copy = []
	for src_file in src_subtree:
		rel_path = relative_path(src_file, src_root_dir)
		dest_file = os.path.join(dest_root, rel_path)
		if is_newer(src_file, dest_file):
			src_to_copy.append(src_file)
	return src_to_copy


def remove_deleted_files(dest_root, src_root, recursive):
	dest_subtree = list_subtree(dest_root, recursive=recursive)
	src_root_dir = os.path.split(src_root)[0] if os.path.isfile(src_root) else src_root
	for dest_file in dest_subtree:
		rel_path = relative_path(dest_file, dest_root)
		src_file = os.path.join(src_root_dir, rel_path)
		if not os.path.exists(src_file):
			os.remove(dest_file)


def sync_files(src_root, dest_root, recursive, backup_type):
	if backup_type == "variable":
		remove_deleted_files(dest_root, src_root, recursive)
	src_to_copy = get_src_to_copy(src_root, dest_root, recursive)
	src_root_dir = os.path.split(src_root)[0] if os.path.isfile(src_root) else src_root
	for src_path in tqdm(src_to_copy, desc="{} -> {}".format(src_root, dest_root)):
		rel_path = relative_path(src_path, src_root_dir)
		dest_path = os.path.abspath(os.path.join(dest_root, rel_path))
		dest_dir = os.path.split(dest_path)[0]
		if not os.path.isdir(dest_dir):
			os.makedirs(dest_dir)
		copyfile(src_path, dest_path)


def run_backup(cfg, dest_root, src_root):
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
			sync_files(src_root=src_dir, recursive=src_cfg['recursive'], dest_root=dest_dir, backup_type=src_cfg['backup_type'])
			if src_cfg['backup_type'] == 'variable':
				dest_subtree = list_subtree(dest_dir, recursive=True)
				for file in dest_subtree:
					rel_path = relative_path(file, content_dir)
					zip_f.write(file, rel_path)


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
	arg_parser.add_argument("--src-root", "-s", default="", help="Path to root of source directory. Assumes that all source paths in config file are relative w.r.t. this path")
	args = arg_parser.parse_args()

	_main()
