# python script to rename poster pdfs according to expected convention for CDN
# copy and paste it, change the folder paths, etc.
# 1. download the posters folder from google drive, put each type of poster in its own directory
# 2. copy this file (rename_poster_pdfs.py) into the posters directory
# 3. create a folder /to_upload/ in each of the poster directories
# 4. run this script in that posters directory for each of the subdirectories
import glob
import os
import re
import shutil
import subprocess

DIRECTORY_PATH = 'a-biomedchallenge'
# DIRECTORY_PATH = 'a-ldav-posters'
# DIRECTORY_PATH = 'a-scivis-contest'
# DIRECTORY_PATH = 'a-vast-challenge'
# DIRECTORY_PATH = 'v-vis-posters'
# DIRECTORY_PATH = 'w-cityvis'
# DIRECTORY_PATH = 'w-energyvis'
# DIRECTORY_PATH = 'w-vahc'
cwd = os.getcwd()

for filename in glob.glob(DIRECTORY_PATH + "/*"):
    # print("filename is ", filename)
    name, typ = filename.split("/")[-1].split(".")
    paper_id = re.findall("\d{4}", name)[0]
    print("filename is ", filename, " name is ", name, " and typ", typ)
    # name, typ = filename.split(".")

    if "doc" in name:
        dst = cwd + "/to_upload/" + DIRECTORY_PATH + "-" + paper_id + "-summary.pdf"
        # print("pdf found dst is ", dst)
        shutil.copyfile(filename, dst)

    if ("file-i9" in name) or ("file-i10" in name) or ("file-i17" in name):
        dst = cwd + "/to_upload/" + DIRECTORY_PATH + "-" + paper_id + ".pdf"
        # print("pdf found dst is ", dst)
        shutil.copyfile(filename, dst)

    if typ == "png":
        # Copy full size image
        dst = (
            cwd + "/to_upload/paper_images/" + DIRECTORY_PATH + "-" + paper_id + ".png"
        )
        shutil.copyfile(filename, dst)

        # Generate thumbnail image
        dst = (
            cwd
            + "/to_upload/paper_images_small/"
            + DIRECTORY_PATH
            + "-"
            + paper_id
            + ".png"
        )
        cmd = "convert '" + filename + "' -resize 600x '" + str(dst) + "'"
        # print("for imagemagick, dst is ", dst)
        # print(cmd)
        subprocess.call(cmd, shell=True)

    # For biomedvischallenge
    if typ == "pdf":
        dst = cwd + "/to_upload/" + DIRECTORY_PATH + "-" + paper_id + ".pdf"
        # print("pdf found dst is ", dst)
        shutil.copyfile(filename, dst)
