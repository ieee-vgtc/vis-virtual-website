# python script to rename poster pdfs according to expected convention for CDN
# copy and paste it, change the folder paths, etc.
import glob
import shutil
import re
import os
# DIRECTORY_PATH = 'a-biomedvischallenge-posters'
# DIRECTORY_PATH = 'a-ldav-posters'
# DIRECTORY_PATH = 'a-sciviscontest-posters'
# DIRECTORY_PATH = 'a-vast-posters'
# DIRECTORY_PATH = 'a-vizsec-posters'
DIRECTORY_PATH = 'v-vis-posters'
cwd = os.getcwd()

for filename in glob.glob(DIRECTORY_PATH + "/*"):
	name, typ = filename.split("/")[-1].split(".")
	# print("filename is ", filename, " name is ", name, " and typ ", typ)
	# name, typ = filename.split(".")

	# For biomedvischallenge
	if typ == 'pdf':
		paper_id = re.findall('\d+', name )[0]
		dst = cwd + '/to_upload/' + DIRECTORY_PATH + '-' + paper_id + '.pdf'
		# print("pdf found dst is ", dst)
		shutil.copyfile(filename, dst)

	# For all others
	if 'doc' in name:
		paper_id = re.findall('\d{4}', name )[0]
		dst = cwd + '/to_upload/' + DIRECTORY_PATH + '-' + paper_id + '-summary.pdf'
		# print("pdf found dst is ", dst)
		shutil.copyfile(filename, dst)

	if ('file-i9' in name) or ('file-i10' in name) or ('file-i17' in name):
		paper_id = re.findall('\d{4}', name )[0]
		dst = cwd + '/to_upload/' + DIRECTORY_PATH + '-' + paper_id + '.pdf'
		# print("pdf found dst is ", dst)
		shutil.copyfile(filename, dst)
