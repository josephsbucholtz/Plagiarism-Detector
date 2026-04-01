import os
import sys
import string
from random import shuffle
import numpy as np 


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

def shingles(text: str, k=3):
    shingle_set = set()
    word_list = text.split()
    for w in range(len(word_list) - k + 1):
        shingle_set.add(tuple(word_list[w:w+k]))

    return shingle_set

def create_hash(one_hot: list):
    signature = []

    for func in minhash_func:
        for i in range(1, len(vocab)+1):
            idx = func.index(i)
            sig_val = one_hot[idx]
            if sig_val == 1:
                signature.append(idx)
                break

    return signature

def create_minhash_func(vocab_size: int, minhash_size: int):
    hashes = []

    for _ in range(minhash_size):
        vocab_shuffle = list(range(1, vocab_size + 1))
        shuffle(vocab_shuffle)
        hashes.append(vocab_shuffle)

    return hashes


# ---------------------- TESTING -------------------------------------

#Texts
declaration_text = "src/data/declaration.txt"
declaration_variant = "src/data/declaration-variant.txt"
repeated_text = "src/data/repeated.txt"

#Clean Documents for processing data
doc1 = clean_document_data(declaration_text)
doc2 = clean_document_data(declaration_variant)

#Create k-shingling for each doc
a = shingles(doc1)
b = shingles(doc2)

#Create our Vocab
vocab = a.union(b)
vocab_list = list(vocab) 

#Create our sparse vectors (later will become dense vectors)
a1_hot = [1 if x in a else 0 for x in vocab] 
b1_hot = [1 if x in b else 0 for x in vocab] 

#Create dense vector
minhash_func = create_minhash_func(len(vocab), 20)

#Create Signatures
a_sig = create_hash(a1_hot)
b_sig = create_hash(b1_hot)

print(a_sig)
print(b_sig)

