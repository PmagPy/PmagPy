#!/bin/bash

# usage: ./release_guis.sh github_username new_release_name
# new_release_name should be in format 1.1.1 (major.minor.patch)
# publishes a new release to PmagPy-Standalone-OSX
# you will have to enter your github credentials after starting this script

## see documentation here:
## https://gist.github.com/caspyin/2288960
##"POST /repos/:owner/:repo/releases"

version="$2"
curl --user "$1" --data "{
    \"tag_name\": \"$version\",
    \"target_commitish\": \"master\",
    \"name\": \"Pmag GUI and MagIC GUI $version\",
    \"body\": \"Pmag GUI & MagIC GUI are standalone graphical user interfaces that provide tools for uploading, downloading, and analyzing data from the [MagIC database](http://earthref.org/MagIC).  This download is for OSX only - click [here](https://github.com/PmagPy/PmagPy-Standalone-Windows/releases/latest) for the Windows download.\n\nFor complete documentation on using the GUIs, see the [PmagPy Cookbook](http://earthref.org/PmagPy/cookbook/).\n\nTo download full PmagPy functionality, see the [PmagPy repository](https://github.com/ltauxe/PmagPy#what-is-it).\n\nGet started by downloading the zip file (see links below) and putting the resulting folder on your desktop. Inside the PmagPy-Standalone folder you will find icons for Pmag GUI and MagIC GUI. Double click the program you wish to run (depending on your security settings, you may have to right click the icon and then select ok the first time you open it).  Please be patient!  Both GUIs need a minute to initialize.\n\n[Click here to download](https://github.com/PmagPy/PmagPy-Standalone-OSX/archive/$version.zip)\",
    \"draft\": false,
    \"prerelease\": false}"  https://api.github.com/repos/PmagPy/PmagPy-Standalone-OSX/releases
echo "done -- new release created"
