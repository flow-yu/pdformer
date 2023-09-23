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

from src.title_detecter import TitleDetecter
from src.sort_and_group import SortGrouper
from src.json_solver import JsonSolver
from src.utile import *

current_directory = os.getcwd()
# 要创建的文件夹路径
output_directory = os.path.join(current_directory, 'output')

class Pdformer():
    def __init__(self, pdf_file, output_dir = output_directory, ):
        self.PDF_file = pdf_file  #  "test_files/papers/con5/weak.pdf"
        self.output_dir = output_dir

        self.pics_folder = os.path.join(self.output_dir, "pics")
        self.structurePath = os.path.join(self.output_dir, "structure")
        self.textbox_file = os.path.join(self.output_dir, "text_boxes.json")

        self.new_text_boxes = None
        self.bboxes = None

        self.new_bboxes = None
        self.layout = None

        self.new_layout = None
        self.final_layout = None
        self.left_boxes = None
        self.final_layout2 = None

        self.alayout = None
        self.alayout2 = None
        self.alayout3 = None


    def generate_pics(self):
        self.pics_folder = os.path.join(self.output_dir, "pics")
        if not os.path.exists(self.pics_folder):
            os.makedirs(self.pics_folder)

        images = convert_from_path(self.PDF_file)
        for i, image in enumerate(images):
            # 生成PNG文件的文件名
            filename = f"page-{i+1:06d}.png"  # 使用6位数字，左侧自动填充0
            # 保存PNG文件
            image_path = os.path.join(self.pics_folder, filename)
            image.save(image_path, "PNG")
            # image.save(pics_folder, "PNG")

    def generate_structured_pics(self):
        command = ["python", "structurer/infer.py",
                "--model_dir=" + "pretrained_model/picodet_lcnet_x1_0_fgd_layout_infer",
                "--image_dir=" + self.pics_folder,
                "--output_dir=" +  self.structurePath,
                "--save_results"]
        # ! python structurer/infer.py --model_dir=pretrained_model/picodet_lcnet_x1_0_fgd_layout_infer --self.pics_folder --device=CPU --self.output_dir --save_results
        result = subprocess.run(command, capture_output=True, text=True)

#self.text_boxes & textbox_file
    def extract_box_from_pdf(self, pdf_path):
        with open(pdf_path, 'rb') as file:
            pages = extract_pages(file)

            page_text_boxes = {}
            page_img_boxes = {}
            # 遍历每一页
            for i, page_layout in enumerate(pages):
                _, _, page_width, page_height = page_layout.bbox

                page_text_boxes[i] = []
                page_img_boxes[i] = []

                # 遍历每个元素
                for element in page_layout:
                    if isinstance(element, LTTextBoxHorizontal) or isinstance(element, LTTextLineHorizontal):
                        # 提取文本框位置信息
                        x0, y0, x1, y1 = element.bbox

                        # 提取文本内容
                        text = element.get_text().strip()

                        page_text_boxes[i].append(('text', text, x0, y0, x1, y1))

            return page_text_boxes, page_img_boxes

    def generate_test_boxes(self):
        page_text_boxes, page_img_boxes = self.extract_box_from_pdf(self.PDF_file)
        with open(os.path.join(self.output_dir, 'text_boxes.json'), 'w') as f:
            json.dump(page_text_boxes, f)


# classify the bboxes
    def apply_structure_box(self):
        page_height, page_width = get_page_size(self.PDF_file)
        print (page_width)

        bboxes = {}
        with open(os.path.join(self.structurePath, "bbox.json"), "r") as f:
                    sbbox = json.load(f)
        pages = os.listdir(self.pics_folder)
        for i,page in enumerate(pages):
            for box in sbbox:
                pageNum = box["file_name"]
                if (pageNum == page):
                    x_min = box['bbox'][0]-5
                    y_min = box['bbox'][1]
                    x_max = box['bbox'][0]+box['bbox'][2]+5
                    y_max = box['bbox'][1]+box['bbox'][3]
                    y = []
                    y.append(x_min)
                    y.append(y_min)
                    y.append(x_max)
                    y.append(y_max)
                    if (box["category_id"]==0):
                        y.append("text")
                    if (box["category_id"]==1):
                        y.append("title")
                    if (box["category_id"]==2):
                        y.append("list")
                    if (box["category_id"]==3):
                        y.append("table")
                    if (box["category_id"]==4):
                        y.append("figure")
                    if (box["category_id"]!=1):
                        bboxes.setdefault(str(i), []).append(y)  #####不可忘记str化！！否则在txt中看不出来！！！！

        json_data = json.dumps(bboxes, indent=2)
        # 将JSON数据写入文本文件
        with open('output/layout_bbox.txt', "w") as file:
            file.write(json_data)    

        self.bboxes = bboxes

#isolated公式引入 速度慢
    def isolated_formula(self):
        new_bboxes=copy.deepcopy(self.bboxes)
        pages = os.listdir(self.pics_folder)
        for i,page in enumerate(pages):
            img_fp = os.path.join(self.pics_folder, pages[i])
            p2t = Pix2Text(analyzer_config=dict(model_name='mfd'))
            outs = p2t(img_fp, resized_shape=600)
        #####out的格式：左上角起顺时针 y为到图片上方的距离
        #####铭记：除了text_boxes y都为到图片上方的距离！！！！！！！！！

            for formula in outs:
                if (formula['type'] == 'isolated'):
                    new_box = formula['position']
                    new_box1 = new_box[[0, 2]].flatten().tolist()
                    new_box1.append('isolated formula')
                    new_bboxes[str(i)].append(new_box1)

        json_data = json.dumps(new_bboxes, indent=2)
        # 将JSON数据写入文本文件
        with open('output/layout_bbox2.txt', "w") as file:
            file.write(json_data)

        self.new_bboxes = new_bboxes

    def Pix2Text_ocr(self):
        pages = os.listdir(self.pics_folder)
        for i, box in enumerate(pages): ##某一页
            img_fp = os.path.join(self.pics_folder, pages[i])
            image = Image.open(img_fp)

            for fsection in self.final_layout2[str(i)]:
                for ffbox in fsection[1]:
                    left, top, right, bottom = ffbox[:4]
                    ybox = (left, top, right, bottom)
                    cropped_img = image.crop(ybox)
                    p2t = Pix2Text(analyzer_config=dict(model_name='mfd'))
                    outs = p2t(cropped_img, resized_shape=600)
                    only_text = merge_line_texts(outs, auto_line_break=True)
                    ffbox.append(only_text)

        json_data = json.dumps(self.final_layout2, indent=2)
        # 将JSON数据写入文本文件
        with open('output/final_layout2.txt', "w") as file:
            file.write(json_data)

    def supplement_title(self):
        with open('output/final_layout2.txt', "r") as file:
            json_data = file.read()
        self.final_layout2 = json.loads(json_data)
        alayout = {}
        temp_title = {}
        temp_title["0"] = ""
        temp_title["1"] = ""
        temp_title["2"] = ""
        temp_title["3"] = ""
        temp_title["4"] = ""
        ##4 更新了 但4.1没更新 导致错位3.4
        # titleset = []
        # for i, box in enumerate(pages): ##某一页
        #     for titlef in final_layout2[str(i)]:
        #         ptitle = titlef[0][4]
        #         titleset.append(ptitle)
        pages = os.listdir(self.pics_folder)
        for i, box in enumerate(pages): ##某一页
            for titlef in self.final_layout2[str(i)]:
                ptitle = titlef[0][4]
                title_level = get_title_level(ptitle)
                if (title_level==0):
                    temp_title[str(title_level)] = ptitle
                    alayout[ptitle]= {}
                    for pbox in titlef[1]:
                        alayout[ptitle].setdefault("content", []).append(pbox)
                else:
                    if temp_title[str(title_level-1)] != "":
                        temp_title[str(title_level)] = ptitle
                        parentl = alayout
                        for t in range(title_level):  ###找到上一级 导致错位
                            if temp_title[str(t)] in parentl:
                                parentl = parentl[temp_title[str(t)]]
                        parentl[ptitle]= {}
                        for pbox in titlef[1]:
                            parentl[ptitle].setdefault("content", []).append(pbox)

        json_data = json.dumps(alayout, indent=2)
        with open('output/alayout.txt', "w") as file:
            file.write(json_data)
        self.alayout = alayout


    def pdf2json(self):
        self.generate_pics()
        self.generate_structured_pics()
        self.generate_test_boxes()

        TitleDetecter(self.PDF_file, self.textbox_file, self.pics_folder, self.output_dir).detector(self)
        # self.bert_title()
        # self.merge_title()
        
        self.apply_structure_box()
        self.isolated_formula()

        SortGrouper(self.PDF_file, self.textbox_file, self.pics_folder,self.new_bboxes,self.layout, self.output_dir).sort_and_group(self)
        # self.sort_boxes()
        # self.possible_section()
        # self.sort_boxes2()
        
        self.Pix2Text_ocr()
        self.supplement_title()
        
        JsonSolver().get_json(self)
        # self.tranform_json()
        # self.split_json()

    def modify_dict(self, dictionary,new_dict):
        new_dict["content"] = {}