from argparse import ArgumentParser
import yaml
import os.path
from tqdm import tqdm
from shutil import copyfile
from zipfile import ZipFile, ZIP_DEFLATED
from datetime import datetime
from pybackup.tools import is_newer, get_files_to_copy, relative_path, list_subtree


def get_src_to_copy(src_root, dest_root, recursive):
	src_to_copy = []
	if os.path.isfile(src_root):
		src_path = src_root
		src_filename = os.path.split(src_path)[1]
		dest_path = os.path.join(dest_root, src_filename)
		if is_newer(src_path, dest_path):
			src_to_copy.append(src_path)
	elif recursive:
		for curr_src_path, _, files in os.walk(src_root):
			curr_dest_path = os.path.abspath(os.path.join(dest_root, relative_path(curr_src_path, src_root)))
			curr_src_files = get_files_to_copy(curr_src_path, curr_dest_path)
			src_to_copy.extend(curr_src_files)
	else:
		src_dir = src_root
		curr_src_to_copy = get_files_to_copy(src_dir, dest_root)
		src_to_copy.extend(curr_src_to_copy)

	return src_to_copy


def sync_files(src_root, dest_root, recursive):
	src_to_copy = get_src_to_copy(src_root, dest_root, recursive)
	src_root = os.path.split(src_root)[0] if os.path.isfile(src_root) else src_root
	for src_path in tqdm(src_to_copy, desc="{} -> {}".format(src_root, dest_root)):
		rel_path = relative_path(src_path, src_root)
		dest_path = os.path.abspath(os.path.join(dest_root, rel_path))
		dest_dir = os.path.split(dest_path)[0]
		if not os.path.isdir(dest_dir):
			os.makedirs(dest_dir)
		copyfile(src_path, dest_path)


def run_backup(cfg, dest_root):
	content_dir = os.path.join(dest_root, "content")
	history_dir = os.path.join(dest_root, "history")
	if not os.path.exists(history_dir):
		os.mkdir(history_dir)
	archive_filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.zip")
	with ZipFile(os.path.join(history_dir, archive_filename), "w", compression=ZIP_DEFLATED) as zip_f:
		for src_name in cfg['backup_sources']:
			dest_dir = os.path.join(content_dir, src_name)
			src_cfg = cfg['backup_sources'][src_name]
			sync_files(src_root=src_cfg['path'], recursive=src_cfg['recursive'], dest_root=dest_dir)
			if src_cfg['backup_type'] == 'variable':
				dest_subtree = list_subtree(dest_dir)
				for file in dest_subtree:
					rel_path = relative_path(file, content_dir)
					zip_f.write(file, rel_path)


def _main():
	config_file = args.config_file
	dest_root = args.dest_dir

	if not os.path.isdir(dest_root):
		raise IOError("Destination dir does not exists: {}".format(dest_root))

	with open(config_file, "rt") as f:
		cfg = yaml.load(f, Loader=yaml.FullLoader)

	run_backup(cfg, dest_root)


if __name__ == '__main__':
	arg_parser = ArgumentParser()
	arg_parser.add_argument("--config-file", "-c", required=True, help="Path to backup config file")
	arg_parser.add_argument("--dest-dir", "-o", required=True, help="Path to destination directory")
	args = arg_parser.parse_args()

	_main()
