import string
from random import shuffle
import numpy as np
import spacy

def lemma(text: str):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    lemmatized_text = " ".join([token.lemma_ for token in doc])
    return lemmatized_text

def clean_document_data(inputFile: str):
    text = ""
    try:
        with open(inputFile, encoding="utf-8") as input:
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
            text = lemma(text)
            return text

    except Exception as e:
        print(e)
        return ""

def shingles(text: str, k=2):
    shingle_set = set()
    word_list = text.split()
    for w in range(len(word_list) - k + 1):
        shingle_set.add(tuple(word_list[w:w+k]))

    return shingle_set

def create_minhash_func(vocab_size: int, minhash_size: int):
    hashes = []

    for _ in range(minhash_size):
        vocab_shuffle = list(range(1, vocab_size + 1))
        shuffle(vocab_shuffle)
        hashes.append(vocab_shuffle)

    return hashes

def compare_signatures(sig1, sig2):
    if len(sig1) != len(sig2) or len(sig1) == 0:
        return 0
    
    matches = 0
    for x, y in zip(sig1, sig2):
        if x == y:
            matches += 1

    return matches / len(sig1)

def jaccard_similarity(set1, set2):
    union = set1.union(set2)
    if len(union) == 0:
        return 0
    
    intersection = set1.intersection(set2)
    return len(intersection) / len(union)

