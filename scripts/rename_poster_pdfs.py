# python script to rename poster pdfs according to expected convention for CDN
# copy and paste it, change the folder paths, etc.
import glob
import shutil
import re
import os
import subprocess
# DIRECTORY_PATH = 'a-biomedvischallenge-posters'
# DIRECTORY_PATH = 'a-ldav-posters'
# DIRECTORY_PATH = 'a-sciviscontest-posters'
# DIRECTORY_PATH = 'a-vast-posters'
# DIRECTORY_PATH = 'a-vizsec-posters'
DIRECTORY_PATH = 'v-vis-posters'
cwd = os.getcwd()

for filename in glob.glob(DIRECTORY_PATH + "/*"):
	name, typ = filename.split("/")[-1].split(".")
	paper_id = re.findall('\d{4}', name )[0]
	print("filename is ", filename, " name is ", name, " and typ", typ)
	# name, typ = filename.split(".")

	if 'doc' in name:
		dst = cwd + '/to_upload/' + DIRECTORY_PATH + '-' + paper_id + '-summary.pdf'
		# print("pdf found dst is ", dst)
		shutil.copyfile(filename, dst)

	if ('file-i9' in name) or ('file-i10' in name) or ('file-i17' in name):
		dst = cwd + '/to_upload/' + DIRECTORY_PATH + '-' + paper_id + '.pdf'
		# print("pdf found dst is ", dst)
		shutil.copyfile(filename, dst)

	if typ == 'png':
		# Copy full size image
		dst = cwd + '/to_upload/paper_images/' + DIRECTORY_PATH + '-' + paper_id + '.png'
		shutil.copyfile(filename, dst)

		# Generate thumbnail image
		dst = cwd + '/to_upload/paper_images_small/' + DIRECTORY_PATH + '-' + paper_id + '.png'
		cmd = "convert '" + filename + "' -resize 600x '" + str(dst) + "'"
		# print("for imagemagick, dst is ", dst)
		# print(cmd)
		subprocess.call(cmd, shell=True)

	# For biomedvischallenge
	if typ == 'pdf':
		dst = cwd + '/to_upload/' + DIRECTORY_PATH + '-' + paper_id + '.pdf'
		# print("pdf found dst is ", dst)
		shutil.copyfile(filename, dst)

	
