#!/bin/bash
# copy_streaming_assets.sh
# Author: Dylan Cashman
# Date: 2021-09-10
# 
# Copies assets from submodule for ieeevisstreaming, renames them, and updates the filepaths in those files.

# Arguments
# $1 - site year (i.e. 2021)
# Example Usage from application root:
# 	sh scripts/copy_streaming_assets.sh  2021

# set -x #echo on

[ "$#" -eq 1 ] || exit "year argument required (i.e. 2021)"


echo "Copying assets from ieeevisstreaming into static/$1/streaming/"

mkdir -p "static/$1/streaming"
cp "ieeevisstreaming/bundle.js" "static/$1/streaming/bundle.js"
cp "ieeevisstreaming/styles.css" "static/$1/streaming/styles.css"

echo "Copying template from ieeevisstreaming into templates/$1/streaming.html"
cp "ieeevisstreaming/index.html" "templates/$1/streaming.html"

echo "changing paths in templates/$1/streaming.html"

perl -pi -e "s#styles.css#/static/$1/streaming/styles.css#g" "templates/$1/streaming.html"
perl -pi -e "s#bundle.js#/static/$1/streaming/bundle.js#g" "templates/$1/streaming.html"
# sed -i -e "s#styles.css#/static/$1/streaming/styles.css#g" "templates/$1/streaming.html"
# sed -i -e "s#bundle.js#/static/$1/streaming/bundle.js#g" "templates/$1/streaming.html"

