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
cp "static/$1/css/ZillaSlab-SemiBold.ttf" "static/$1/streaming/ZillaSlab-SemiBold.ttf"

echo "Copying template from ieeevisstreaming into templates/$1/streaming.html"
cp "ieeevisstreaming/index.html" "templates/$1/streaming.html"

echo "changing paths in templates/$1/streaming.html"

perl -pi -e "s#styles.css#/static/$1/streaming/styles.css#g" "templates/$1/streaming.html"
perl -pi -e "s#bundle.js#/static/$1/streaming/bundle.js#g" "templates/$1/streaming.html"


echo "injecting auth0 into streaming page for authentication"
awk "
/<\/body>/ {
    print \"{% if config.use_auth0 and requires_auth %}\"
    print \"<-- Injected auth0 code from copy_streaming_assets.sh -->\"
    print \"<script src='https://cdn.jsdelivr.net/npm/jquery@3.4.1/dist/jquery.min.js'\"
	print \"integrity='sha256-CSXorXvZcTkaix6Yvo6HppcZGetbYMGWSFlBw8HfCJo='\"
	print \"crossorigin='anonymous'></script>\"
    print \"<script src='https://cdn.auth0.com/js/auth0-spa-js/1.12/auth0-spa-js.production.js'></script>\"
    print \"<script>\"
    print \"const auth0_domain = '{{config.auth0_domain}}';\"
    print \"const auth0_client_id = '{{config.auth0_client_id}}';\"
    print \"</script>\"
    print \"<script src='/static/$1/js/modules/auth0protect.js'></script>\"
    print \"{% endif %}\"
}
{ print }
" "templates/$1/streaming.html" > tempfile; mv tempfile "templates/$1/streaming.html"

# sed -i -e "s#styles.css#/static/$1/streaming/styles.css#g" "templates/$1/streaming.html"
# sed -i -e "s#bundle.js#/static/$1/streaming/bundle.js#g" "templates/$1/streaming.html"

