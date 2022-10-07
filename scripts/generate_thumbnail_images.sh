# bash script using imagemagick to resize to 600 pixel width images.  
# copy and paste it, change the folder paths, etc.
for filename in *.png; do
	convert "$filename" -resize 600x "paper_images_small/$filename"
done