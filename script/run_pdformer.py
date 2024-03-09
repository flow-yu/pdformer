import os
import json
import sys
import argparse

PROJECT_NAME = "pdformer"
sys.path.append(os.path.join(os.getcwd()[:os.getcwd().find(PROJECT_NAME)], PROJECT_NAME))
from input.config.conf import *
from readers.pdfreader import PdfReader

def main():
    # parser = argparse.ArgumentParser()
    # parser.add_argument('--pdf_name', default=pdf_name, help='input file')    
    # parser.add_argument('--input_directory', default=input_directory, help='the input dir')
    # parser.add_argument('--output_directory', default=output_directory, help='the output dir')
    # args = parser.parse_args(
    reader = PdfReader()
    reader.read()

if __name__ == '__main__':
    main()