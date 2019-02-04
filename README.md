# README #

## Necessary Packages ##

* Python 2.7.10+

        sudo add-apt-repository ppa:fkrull/deadsnakes-python2.7
        sudo apt-get update
        sudo apt-get install python2.7

* OpenCV

        sudo pip install opencv-python==3.4.2.16
        sudo pip install opencv-contrib-python==3.4.2.16

* fuzzywuzzy, python-Levenshtein

        sudo pip install Fuzzywuzzy
        sudo pip install python-Levenshtein

* pdftoppm

        sudo apt-get install poppler-utils

* commonregex

        sudo pip install commonregex

* requests

        sudo pip install requests


## Configuration ##

#### - Receipt Extractor ####

* receipt_extractor.py

    Format:

            python receipt_extractor.py file_name [country]
            
    Default value:
    
            country:    DU
