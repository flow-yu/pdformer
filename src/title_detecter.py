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

class TitleDetecter():
    def __init__(self, pdf_file, textbox_file, pics_folder, output_dir ):
        self.PDF_file = pdf_file
        self.textbox_file = textbox_file
        self.pics_folder = pics_folder
        self.new_text_boxes = None
        self.layout = None


    def encoder(self, sentences):
        ids = []
        PRE_TRAINED_MODEL_NAME = 'bert-base-uncased'
        tokenizer = BertTokenizer.from_pretrained(PRE_TRAINED_MODEL_NAME,do_lower_case = True)
        for sentence in sentences:
            # 文本编码+添加编码id
            encoding = tokenizer.encode_plus(
            sentence,
            max_length=16,
            truncation = True,
            add_special_tokens=True,
            return_token_type_ids=False,
            pad_to_max_length=True,
            return_attention_mask=False)
            ids.append(encoding['input_ids'])
        return ids

    def bert_title(self, main_instance):
        with open(self.textbox_file, 'r') as f:
        #不同pdf被pdfminer解析出的box信息存放在对应的textbox
             text_boxes = json.load(f)
        bert_encoder = TFBertModel.from_pretrained('bert-base-uncased') #可以将输入的文本转换为高维向量表示
#模型构建
        input_word_ids = tf.keras.Input(shape=(16,), dtype=tf.int32, name="input_word_ids") #input层
        embedding = bert_encoder([input_word_ids])  #[batch_size, sequence_length, hidden_size]

        dense = tf.keras.layers.Lambda(lambda seq: seq[:, 0, :])(embedding[0])
        dense = tf.keras.layers.Dense(128, activation='relu')(dense)
        dense = tf.keras.layers.Dropout(0.2)(dense)
        output = tf.keras.layers.Dense(1, activation='sigmoid')(dense)
        model = tf.keras.Model(inputs=[input_word_ids], outputs=output)

        pages = os.listdir(self.pics_folder)
        filtered_list=[]
        new_text_boxes={}

        print(pages)
        del pages[0]

        for i,page in enumerate(pages):
        #######针对某一页的分析结果out
            for box in text_boxes[str(i)]:
                split_string_to_boxes(box, new_text_boxes.setdefault(str(i), []))

        copied_dict = copy.deepcopy(new_text_boxes)
        for i,page in enumerate(pages):
        #######针对某一页的分析结果out
            for box in copied_dict[str(i)]:
                if is_word(box[0]) or string_filter(box[0]):
                    filtered_list.append(box[0])
                else:
                    new_text_boxes[str(i)].remove(box)

        with open('output/origin_list2.txt', 'w') as f:
            for item in filtered_list:
                f.write("%s\n" % item)

        filtered_list = np.array(filtered_list)
        text_list = filtered_list
        filtered_list = self.encoder(filtered_list)
        filtered_list = tf.convert_to_tensor(filtered_list)

        model.load_weights('pretrained_model/model_4epoch.h5')
        prediction = model.predict(filtered_list)

        merged_array = np.concatenate(( text_list.reshape(-1, 1), prediction), axis=1)
        with open('output/ans_list.txt', 'w') as f:
            for item in merged_array:
                f.write("%s\n" % item)

        ans_array = np.empty((0, 2))
        for i in range(len(merged_array)):
            if float(merged_array[i][1]) > 0.958:
                ans_array = np.vstack((ans_array, merged_array[i]))
        with open('output/ans_title_list.txt', 'w') as f:
            for item in ans_array:
                f.write("%s\n" % item)

        box_index=0
        copied_dict2 = copy.deepcopy(new_text_boxes)
        for i,page in enumerate(pages):
            for box in copied_dict2[str(i)]:
                if float(merged_array[box_index][1]) <= 0.958:
                    new_text_boxes[str(i)].remove(box)
                box_index = box_index+1
        print(box_index)

        json_data = json.dumps(new_text_boxes, indent=2)
        # 将JSON数据写入文本文件
        with open('output/new_text_boxes.txt', "w") as file:
            file.write(json_data)
        self.new_text_boxes = new_text_boxes
        main_instance.new_text_boxes = new_text_boxes

    def merge_title(self, main_instance):
        layout={}
        page_height, page_width = get_page_size(self.PDF_file)

        num=-1
        pages = os.listdir(self.pics_folder)
        for i,page in enumerate(pages):
            layout.setdefault(str(i), [])
            temp=["", -1,-1,-1,-1]  ##防止不同page的同一位置
            img_fp = os.path.join(self.pics_folder, pages[i])
            #字典的键为当前页面的索引"i"，值为标题信息列表。
            image = Image.open(img_fp)
            cood_h = image.size[1] / page_height
            cood_w = image.size[0] / page_width

            if str(i) in self.new_text_boxes:
                for box in self.new_text_boxes[str(i)]:
                    if (box_compare(temp,box)==1 ):  ##相同或b包含
                        layout[str(i)][-1].append(box[0])
                        temp = box
                    elif (box_compare(temp,box)==2 ):  ##相同或a包含
                        layout[str(i)][-1].append(box[0])
                    else: ####和前不同的情况
                        new_box = [cood_w*box[1], image.size[1]-cood_h*box[4], cood_w*box[3], image.size[1]-cood_h*box[2]]
                        new_box.append(box[0])
                        layout[str(i)].append(new_box)
                        temp = box

        json_data = json.dumps(layout, indent=2)
        # 将JSON数据写入文本文件
        with open('output/layout_title.txt', "w") as file:
            file.write(json_data)
        self.layout = layout
        main_instance.layout = layout

    def detector(self, main_instance):
        self.bert_title(main_instance)
        self.merge_title(main_instance)