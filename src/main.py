import os
import sys
import string
import numpy as np 

declaration_text = "src/data/declaration.txt"
declaration_variant = "src/data/declaration-variant.txt"

def clean_document_data(inputFile: str):
    text = ""
    try:
        with open(inputFile) as input:
            for line in input:
                if line == '\n':
                    continue
                for word in line:
                    if word == '\n':
                        text += ' '
                    else:
                        text += word
        
            translator = str.maketrans('', '', string.punctuation)    
            text = text.translate(translator)
            text = text.lower()
            return text

    except Exception as e:
        print(e)

def shingle(text: str, k=3):
    shingle_set = set()
    word_list = text.split()
    for w in range(len(word_list) - k + 1):
        shingle_set.add(tuple(word_list[w:w+k]))

    return shingle_set




doc1 = clean_document_data(declaration_text)
doc2 = clean_document_data(declaration_text)
a = shingle(doc1)
b = shingle(doc2)

vocab = a.union(b)


