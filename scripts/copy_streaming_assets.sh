#!/bin/bash
# copy_streaming_assets.sh
# Author: Dylan Cashman
# Date: 2021-09-10
# 
# Takes as first argument the path to the streaming repo ieeevisstreaming.  
# Copies assets into this repository, renames them, and updates the filepaths in those files.

# Arguments
# $1 - path to the ieeevisstreaming repo, to copy files from
# $2 - site year (i.e. 2021)
# Example Usage from application root:
# 	sh scripts/copy_streaming_assets.sh ../ieeevisstreaming 2021

set -x #echo on

echo "Copying assets from $1 into static/$2/streaming/"

mkdir -p "static/$2/streaming"
cp "$1/bundle.js" "static/$2/streaming/bundle.js"
cp "$1/styles.css" "static/$2/streaming/styles.css"

echo "Copying template from $1 into templates/$2/streaming.html"
cp "$1/index.html" "templates/$2/streaming.html"

echo "changing paths in templates/$2/streaming.html"

perl -pi -e "s#styles.css#/static/$2/streaming/styles.css#g" "templates/$2/streaming.html"
perl -pi -e "s#bundle.js#/static/$2/streaming/bundle.js#g" "templates/$2/streaming.html"
# sed -i -e "s#styles.css#/static/$2/streaming/styles.css#g" "templates/$2/streaming.html"
# sed -i -e "s#bundle.js#/static/$2/streaming/bundle.js#g" "templates/$2/streaming.html"

