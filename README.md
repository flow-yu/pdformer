# Pdformer

This is the readme file for the Pdformer.

## Introduction

> **When everyone digs for gold, sell shovels.**

When different kinds of large models are attached great importance to, we want to buiild a data loader and cleaner for different kinds of information formats (among which, PDF is one of the most complex ones) with relevant experts(Mixture of Experts), before inputed into LLMs. Our object is that users can diy their input and prompt, namely Retrieval Augmented Generation(RAG).

This is mainly a PDF document content extractor at present. Our work is based on existing open-source projects, combining techs like OCR and layout analysis. The pipeline is as follows:

![image](https://github.com/heartflow-yu/pdformer/assets/80616172/9325c663-9b0c-4519-9f08-5008d13e2cdf)
## Install

python == 3.10

```python
pip install -r requirements.txt
```

Also need to install the PaddlePaddle for the layout analysis.

```python
python3 -m pip install paddlepaddle -i https://mirror.baidu.com/pypi/simple
```

## How to use

Find the ***conf.py*** under **"input/config/"**, and freely modify the default values.

#### **Loading a PDF and run**

**`input_directory`**: the default input directory is under **`"input/"`**.

Put the pdf file under **`"input/example/"`**, change the value of pdf_name to the name of the pdf (ex: for **test.pdf**, pdf_name = "test")

Run the ***run_pdformer.py*** under **`"script/"`**

#### **Outputs**

- **`output_directory`**: the default output directory is under **`"output/pdf_name/"`**.
- ***result.json*** (structured json) is under **`"output/pdf_name/results/"`**, which also contains the meta_csv collected from the pdf file, namely **title, text, list, table and figure**. The data form in csv is shown below:

![image-20240308022610361](./README_pics/image-20240308022610361.png)

- **`pics_directory`**: the default pics directory is under **`"output/pdf_name/pics/"`**, which contains pictures of the pdf file.

- **`structure_directory`**: the default structure directory is under **`"output/pdf_name/structure/"`**, which contains the result of the layout analysis.

