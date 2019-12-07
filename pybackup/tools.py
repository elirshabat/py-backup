import os
from pathlib import Path


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


def get_files_to_copy(src_dir, dest_dir):
	ls_src = list_files(src_dir)
	src_to_copy = []
	for src_file in ls_src:
		src_path = os.path.join(src_dir, src_file)
		rel_path = relative_path(src_path, src_dir)
		dest_path = os.path.join(dest_dir, rel_path)
		if is_newer(src_path, dest_path):
			src_to_copy.append(src_path)
	return src_to_copy


def list_subtree(root_dir):
	subtree_files = []
	for dir, _, files in os.walk(root_dir):
		for file in files:
			subtree_files.append(os.path.abspath(os.path.join(dir, file)))
	return subtree_files
