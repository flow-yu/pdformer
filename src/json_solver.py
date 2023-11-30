import os
from paddleocr import PaddleOCR, draw_ocr
from PIL import Image, ImageDraw, ImageFont
import pdfplumber
# import pytesseract
import numpy as np
import time
import sys
import argparse
import subprocess
import numpy as np
import pandas as pd
import json
import PyPDF2
import copy
import pix2text
from pix2text import Pix2Text, merge_line_texts
import re
import tensorflow as tf
import matplotlib.pyplot as plt
from transformers import TFBertModel, BertTokenizer
from sklearn.model_selection import train_test_split
from pdf2image import convert_from_path
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBoxHorizontal, LTTextLineHorizontal, LTFigure, LTImage
# from rich.progress import track
from src.utile import *

class JsonSolver():
    def __init__(self):
        self.alayout2 = None
        self.alayout3 = None

    def range_boxes(self, dictionary, new_dict):
        if "content" in dictionary:
            content = dictionary["content"]
            new_sub_dict = {}
            for sub_box in content:
                if (len(sub_box)>5):
                    ssection = sub_box[4]
                    sub_box.pop(4)
                    new_sub_dict.setdefault(ssection, []).append(sub_box)
            new_dict["content"] = new_sub_dict
        for key, value in dictionary.items():
            if isinstance(value, dict):
                self.range_boxes(value, new_dict[key])

    def tranform_json(self,main_instance):
        with open('output/alayout.txt', "r") as file:
            json_data = file.read()
        alayout = json.loads(json_data)
        alayout2 = copy.deepcopy(alayout)
        self.range_boxes(alayout, alayout2)

        json_data = json.dumps(alayout2, indent=2)
        with open('output/alayout2.txt', "w") as file:
            file.write(json_data)
        self.alayout2 = alayout2
        main_instance.alayout2 = alayout2

    def split_string(self, dictionary, new_dict):
        for key, value in dictionary.items():
            if key in ["text", "image","list","table","isolated formula"]:
                new_value = {}
                for index, item in enumerate(value):
                    position = tuple(item[:4])
                    content = item[5]
                    new_item = {"position": position, "content": content}
                    new_value[str(index)] = new_item
                new_dict[key] = new_value
            elif isinstance(value, dict):
                self.split_string(value, new_dict[key])

    def split_json(self, main_instance):
        with open('output/alayout2.txt', "r") as file:
            json_data = file.read()
            self.alayout2 = json.loads(json_data)

        alayout3 = copy.deepcopy(self.alayout2)
        self.split_string(self.alayout2,alayout3)
        json_data = json.dumps(alayout3, indent=2)
        with open('output/alayout3.txt', "w") as file:
            file.write(json_data)
        self.alayout3 = alayout3
        main_instance.alayout3 = alayout3

    def get_json(self, main_instance):
        self.tranform_json(main_instance)
        self.split_json(main_instance)