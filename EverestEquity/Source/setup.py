from distutils.core import setup
import py2exe
import pyodbc
import csv
import chardet
from shutil import copyfile
from datetime import datetime
#from typing import Any
import configparser
from pathlib import Path
import os
import sys

setup(
    options = {'py2exe':{'bundle_files':1,'compressed':True}},
    console=['LoadFile.py'],
    zipfile = None,
    data_files=[(".",["LoadFile.config"])]
    )