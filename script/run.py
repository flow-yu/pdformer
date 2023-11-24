import os
import json
import sys
import argparse

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from src.pdformer import Pdformer
# from src.utile import *

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', default='Input/example/test.pdf', help='input file')
    parser.add_argument('--section', default=None, help='Specify the section')
    parser.add_argument('--mode', default='normal', help='output mode')
    parser.add_argument('--anspath', default='ans/', help='the answer being asked')
    args = parser.parse_args()

    # 读取参数文件 setup.txt
    # setup_params = {}
    # with open('setup.txt', 'r') as f:
    #     for line in f:
    #         if line.strip():  # 忽略空行
    #             key, value = line.strip().split('=')
    #             setup_params[key.strip()] = value.strip()\
    with open('input/conf.json', 'r') as file:
        config = json.load(file)

    # TODO：logically wrong？
    if args.f:
        args.file = config['f']
    if args.section:
        args.section = config['section']
    if args.mode:
        args.mode = config['mode']
    # # 解析参数
    # (options, args) = parser.parse_args(params + sys.argv[1:])
    # 获取解析后的参数值
    filepath = config['f']
    section = config['section']
    mode =  config['mode']
    anspath = args.anspath

    pdf_object = Pdformer(filepath)
    pdf_object.pdf2json()

    with open('output/alayout3.txt', "r") as file:
            json_data = file.read()
    alayout3 = json.loads(json_data)

    if section != None:
        alayout3 = find_content(alayout3, section)

    json_data = json.dumps(alayout3, indent=2)
    os.makedirs(anspath, exist_ok=True)
    ans_section = os.path.join(anspath,"ans_section.txt" )
    with open(ans_section, "w") as file:
        file.write(json_data)

    part_list = ["text", "image","list","table","isolated formula"]
    if mode != 'normal':  #text
        remove_elements_from_list(part_list, mode)
        remove_keys_from_nested_dict(alayout3, part_list)
    json_data = json.dumps(alayout3, indent=2)
    ans = os.path.join(anspath,"ans.txt" )
    with open(ans, "w") as file:
        file.write(json_data)

if __name__ == '__main__':
    main()