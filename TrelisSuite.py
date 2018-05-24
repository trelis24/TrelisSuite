from requests import get
from zipfile import ZipFile
from os.path import abspath
from shutil import copyfileobj

import sys
import os
import tarfile

class bcolors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def download_file(url, path):
	res = get(url.strip(), stream=True)
	if res.status_code != 200:
		raise Exception('URL not found!')
	with open(path, 'wb') as out:
		copyfileobj(res.raw, out)
	return res.headers['content-type']

def has_folder(ref, file_type):
	if 'zip' in file_type:
		content = ref.namelist()
	elif 'tar' in file_type:
		content = ref.getnames()
	return len(content[0].split('/')) == 2

def extract_file(file_path, path, file_type):
	if 'zip' in file_type:
		zip_ref = ZipFile(file_path, 'r')
		if not has_folder(zip_ref, file_type):
			path = os.path.join(path,file_path.split('/')[-1])
		zip_ref.extractall(path)
		zip_ref.close()
	elif 'tar' in file_type:
		tar = tarfile.open(file_path)
		if not has_folder(tar, file_type):
			path = os.path.join(path,file_path.split('/')[-1])
		tar.extractall(path)
		tar.close()
	else:
		raise Exception('error while extracting!')

def delete_file(path):
	os.remove(path)

def main(args):
	path = abspath(sys.argv[1])
	print 'Files downloaded in: ' + path
	links = abspath(sys.argv[2])
	
	with open(links,"r") as f:
		files = f.readlines()
		for line in files:
			if not ';' in line:
				folder = line.strip()
			else:
				name, url = line.split(';')
				file_path = '/tmp/{0}'.format(name.replace(' ','_').lower())
				try: 
					file_type = download_file(url, file_path)
					extract_file(file_path, os.path.join(path,folder),file_type)	
					delete_file(file_path)				
				except Exception as e:
					print bcolors.FAIL + name + " " + str(e) + bcolors.ENDC
					continue
				print bcolors.OKGREEN + name + " downloaded!" + bcolors.ENDC


if __name__ == '__main__':
	if len(sys.argv) < 3:
		print 'Usage: TrelisSuite.py downloadPath linksPath'
		sys.exit(-1)
	main(sys.argv)	
	