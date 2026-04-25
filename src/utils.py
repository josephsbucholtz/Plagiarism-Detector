import itertools
import os
from random import shuffle
import numpy as np
import document

def shingles(text: str, k=2):
    shingle_set = set()
    word_list = text.split()
    for w in range(len(word_list) - k + 1):
        shingle_set.add(tuple(word_list[w:w+k]))

    return shingle_set

def create_hash(one_hot: list, vocab_size: int):
    signature = []

    for func in minhash_func:
        for i in range(1, vocab_size + 1):
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


def run_comparison(file1, file2):
    global vocab
    global minhash_func

    #Clean Documents for processing data
    doc1 = document.lemma_clean_document_data(file1)
    doc2 = document.lemma_clean_document_data(file2)

    #Create k-shingling for each doc
    a = shingles(doc1)
    b = shingles(doc2)

    #Create our Vocab
    vocab = a.union(b)

    if len(vocab) == 0:
        return {"error": "Documents are too short or empty."}

    #Create our sparse vectors (later will become dense vectors)
    a1_hot = [1 if x in a else 0 for x in vocab]
    b1_hot = [1 if x in b else 0 for x in vocab]

    #Create dense vector
    minhash_func = create_minhash_func(len(vocab), 200)

    #Create Signatures
    a_sig = create_hash(a1_hot, len(vocab))
    b_sig = create_hash(b1_hot, len(vocab))

    minhash_similarity = compare_signatures(a_sig, b_sig)
    real_similarity = jaccard_similarity(a, b)

    return {
        "file1": file1,
        "file2": file2,
        "a_sig": a_sig,
        "b_sig": b_sig,
        "minhash_similarity": minhash_similarity,
        "real_similarity": real_similarity,
        "num_shingles_doc1": len(a),
        "num_shingles_doc2": len(b),
        "common_shingles": len(a.intersection(b)),
        "vocab_size": len(vocab)
    }

def compare_all_files(folder_path):
    files = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.endswith(".txt")
    ]

    results = []

    for file1, file2 in itertools.combinations(files, 2):
        result = run_comparison(file1, file2)
        if "error" not in result:
            results.append(result)

    return results

    
