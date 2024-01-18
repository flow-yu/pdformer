# Pdformer

This is the readme file for the Pdformer.

## Introduction

> **When everyone digs for gold, sell shovels.**

When different kinds of large models are attached great importance to, we want to buiild a data loader and cleaner for different kinds of information formats (among which, PDF is one of the most complex ones) with relevant experts(Mixture of Experts), before inputed into LLMs. Our object is that users can diy their input and prompt, namely Retrieval Augmented Generation(RAG).

This is mainly a PDF document content extractor at present. Our work is based on existing open-source projects, combining techs like OCR and layout analysis. The pipeline is as follows:

![image](https://github.com/heartflow-yu/pdformer/assets/80616172/9325c663-9b0c-4519-9f08-5008d13e2cdf)
## Install

python==3.8

```python
pip install -r requirements.txt
apt-get install poppler-utils
```
