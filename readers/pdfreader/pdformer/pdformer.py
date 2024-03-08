import os
from PIL import Image
import subprocess
import json
import copy
from pix2text import Pix2Text, merge_line_texts
from pdf2image import convert_from_path
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBoxHorizontal, LTTextLineHorizontal
from tqdm import tqdm
import csv
# from PIL import ImageDraw

from .model.title_detecter import TitleDetecter
from .util.sort_and_group import SortGrouper
from .util.json_solver import JsonSolver
from .util.util import *
from .util.categories_solver import *

from input.config.conf import *


class Pdformer():
    def __init__(self,):
        self.pdf_file = pdf_file  #  "test_files/papers/con5/weak.pdf"

        self.output_dir = output_directory
        self.pics_dir = pics_directory
        self.structure_dir = structure_directory
        self.temp_dir = temp_directory
        self.results_dir = results_directory
        # if not os.path.exists(self.temp_dir):
        #     os.makedirs(self.temp_dir)

        for category in categories:
            folder_path = os.path.join(self.results_dir, category)
        # 动态设置属性名称，例如：figure_dir  figure_id figure_entries
            setattr(self, f"{category}_dir", folder_path)
            os.makedirs(folder_path, exist_ok=True)
            setattr(self, f"{category}_id", 0)
            setattr(self, f"{category}_entries", [])
            #使用 globals() 函数获取当前全局作用域的字典; 并通过字符串作为键，从字典中获取对应的类对象
            # setattr(self, f"{folder_type}_solver", globals()[f"{folder_type.capitalize()}Solver"]())

        self.solvers = {
            "text": TextSolver(),
            "title": TitleSolver(),
            "list": ListSolver(),
            "table": TableSolver(),
            "figure": FigureSolver()
        }

        self.textbox_file = os.path.join(self.temp_dir, "text_boxes.json")
        self.text_boxes_from_miner = None
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
        if not os.path.exists(self.pics_dir):
            os.makedirs(self.pics_dir)
        print(self.pdf_file)
        images = convert_from_path(self.pdf_file)
        for i, image in enumerate(images):
            # 生成PNG文件的文件名
            filename = f"page-{i+1:06d}.png"  # 使用6位数字，左侧自动填充0
            # 保存PNG文件
            image_path = os.path.join(self.pics_dir, filename)
            image.save(image_path, "PNG")
            # image.save(pics_folder, "PNG")


    def generate_structured_pics(self):
        print("############################")
        #TODO
        if os.path.exists(self.structure_dir):
            print("Structure already generated")
            return
        command = ["python", INFER_PATH,
                "--model_dir=" + LCNET_PATH,
                "--image_dir=" + self.pics_dir,
                "--output_dir=" +  self.structure_dir,
                "--save_results"]
        # ! python structurer/infer.py --model_dir=pretrained_model/picodet_lcnet_x1_0_fgd_layout_infer --self.pics_folder --device=CPU --self.output_dir --save_results
        result = subprocess.run(command, capture_output=True, text=True)

#self.text_boxes & textbox_file
    def extract_box_from_pdf(self):
        with open(self.pdf_file, 'rb') as file:
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
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        page_text_boxes, page_img_boxes = self.extract_box_from_pdf()
        self.text_boxes_from_miner = page_text_boxes

        with open(os.path.join(self.temp_dir, 'text_boxes.json'), 'w') as f:
            json.dump(page_text_boxes, f)

# classify the bboxes
    def apply_structure_box(self):
        # page_height, page_width = get_page_size(self.pdf_file)
        bboxes = {}
        with open(os.path.join(self.structure_dir, "bbox.json"), "r") as f:
                    sbbox = json.load(f)
        pages = os.listdir(self.pics_dir)
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

                    if (box["category_id"] in category_id2name):
                        y.append(category_id2name[box["category_id"]])
                    if (box["category_id"]!=1):
                        bboxes.setdefault(str(i), []).append(y)  #####不可忘记str化！！否则在txt中看不出来！！！！

        self.bboxes = bboxes
        with open(os.path.join(self.temp_dir, 'layout_bbox.json'), "w") as f:
            json.dump(bboxes, f, indent=2)
        
#isolated公式引入 速度慢###############
    def isolated_formula(self):
        print("####################")
        print("isolated_formula start")
        new_bboxes=copy.deepcopy(self.bboxes)
        pages = os.listdir(self.pics_dir)
        p2t = Pix2Text(analyzer_config=dict(model_name='mfd'), device='cpu')
        for i,page in enumerate(pages):
            img_fp = os.path.join(self.pics_dir, pages[i])
            outs = p2t(img_fp, resized_shape=600)
        #####out的格式：左上角起顺时针 y为到图片上方的距离
        #####铭记：除了text_boxes y都为到图片上方的距离！！！！！！！！！

            for formula in outs:
                if (formula['type'] == 'isolated'):
                    new_box = formula['position']
                    new_box1 = new_box[[0, 2]].flatten().tolist()
                    new_box1.append('isolated formula')
                    new_bboxes[str(i)].append(new_box1)

        with open(os.path.join(self.temp_dir, 'layout_bbox2.json'), "w") as f:
            json.dump(new_bboxes, f, indent=2)

        self.new_bboxes = new_bboxes

    def Pix2Text_ocr(self):
        pages = os.listdir(self.pics_dir)
        p2t = Pix2Text(analyzer_config=dict(model_name='mfd'), device='cpu')
        all_image = [Image.open(os.path.join(self.pics_dir, pages[i])) for i in range(len(pages))]
        for i, box in tqdm(enumerate(pages)): ##某一页
            for fsection in self.final_layout2[str(i)]:
                for ffbox in fsection[1]:
                    left, top, right, bottom = ffbox[:4]
                    ybox = (left, top, right, bottom)
                    cropped_img = all_image[ffbox[5]].crop(ybox)
                    try:
                        outs = p2t(cropped_img, resized_shape=600)
                    except Exception as e:
                        print(f"Skipping box outside image bounds: {ffbox}")
                        continue
                    only_text = merge_line_texts(outs, auto_line_break=True)
                    ffbox.append(only_text)
                    
        #TODO final_layout2 去掉页码
        #TODO 处理多行问题
        with open(os.path.join(self.temp_dir, 'final_layout2.json'), "w") as file:
            json.dump(self.final_layout2, file, indent=2)
        

    def list2node_csv(self, dirtydict):
        """将形似final_layout2 的dict转化为各类csv & node (先不插入level)
        Args:
            dirtydict: 一个形似final_layout2的dict

        Returns:
            node_list: all the nodes in sequence 
        """
        node_list = []
        for i, title_content_pairs in dirtydict.items():  
            for title_content in title_content_pairs:          
                samebox_tile_num = len(title_content[0]) - 4
                for j in range(samebox_tile_num):
                    title_text = title_content[0][j+4]
                    category = "title"
                    solver = self.solvers[category]
                    current_id = getattr(self, f"{category}_id")
                    node_list.append(solver.get_newnode(current_id,title_text))
                    current_entries = getattr(self, f"{category}_entries")
                    current_entries.append(solver.get_newentry(current_id, i, title_content[0][:4], title_text))
                    setattr(self, f"{category}_id", current_id + 1)
                
                for box in title_content[1]:
                    category = box[4]
                    if category in self.solvers:
                        solver = self.solvers[category]
                        current_id = getattr(self, f"{category}_id")
                        node_list.append(solver.get_newnode(current_id))
                        current_entries = getattr(self, f"{category}_entries")
                        current_entries.append(solver.get_newentry(current_id, i, box[:4], box[6]))
                        setattr(self, f"{category}_id", current_id + 1)

        for category in categories:
            current_entries = getattr(self, f"{category}_entries")
            columns = self.solvers[category].get_columns()
            with open(os.path.join(self.results_dir, category, f"meta_{category}.csv"), 'w') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                for entry in current_entries:
                    writer.writerow(entry)
        
        return node_list

    def clean_title_level(self, all_nodes):
        for node in all_nodes:
            if node['node_type'] == 1:  # 标题  
                title_words = node['text'].split(" ")

            first_word = ""   
            for i in title_words:
                if i != "":
                    first_word = i
                    break    # 4.1   (1)   Abstract

            nums = first_word.split(".")   
            is_num = True
            for i in nums:# 4 1   (
                if not i.isdigit():   
                    is_num = False  #abstract  （1）？

            if is_num:
                #TODO 改级别？
                # node['level'] = len(nums) + 1  ########数字个数加1为级别 
                if (len(nums)>0):
                    node['level'] = len(nums)   ###########数字个数为级别 1级开始   
        return all_nodes

    def build_tree(self, root_node, nodes, start_idx, current_level): #递归建树
        idx = start_idx
        while idx < len(nodes):
            node = nodes[idx]
            if node['node_type'] == 1:  # paragraph
                root_node['children'].append(node)
                idx += 1
            else:
                if node['level'] <= current_level:  # 遇高级/同级标题 递归结束 
                    break
                else:
                    root_copy = node.copy()
                    child_tree, idx = self.build_tree(root_copy, nodes, idx + 1, current_level=node['level'])
                    root_node['children'].append(child_tree)
        return root_node, idx

    def organize_tokens(self,nodes):
        root = nodes[0]
        root_tree, _ = self.build_tree(root, nodes, 1, 1) #从大标题开始
        return root_tree

    def pdf2json(self):
        self.generate_pics()
        self.generate_structured_pics()
        self.generate_test_boxes() #'text_boxes.json'

        TitleDetecter(self.textbox_file).detector(self)
        # self.bert_title()  new_text_boxes.json
        # self.merge_title()  layout_title.txt
        
        self.apply_structure_box()
        # layout_bbox.json

        self.isolated_formula()
        # layout_bbox2.json

        SortGrouper(self.textbox_file, self.new_bboxes,self.layout).sort_and_group(self)
        # self.sort_boxes()  layout_title2.json
        # self.possible_section()  final_layout.json
        # self.sort_boxes2()  final_layout2.json
        
        self.Pix2Text_ocr()
        all_nodes = self.list2node_csv(self.final_layout2)
        all_nodes = self.clean_title_level(all_nodes)
        root_tree = self.organize_tokens(all_nodes)
        # self.Layout2Text()

        # self.supplement_title()  alayout.json
        
        # JsonSolver(self.output_dir, self.temp_folder).get_json(self)
        # self.tranform_json()
        # self.split_json()
        return root_tree