#!/bin/bash

#mydetectors
cd ..
#detectors
cd ..
#slither
cd ..

#python3 setup.py install
pip install .

cd slither
cd detectors
cd my_detectors
#cd 0.7.6
#./compile_git.sh

#slither --detect detect_round backdoor.sol
