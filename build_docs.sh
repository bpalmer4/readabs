echo " "
echo "About to build the documentation ..."
cd ~/readabs
rm -rf ./docs
pdoc ./src/readabs -o ./docs 

