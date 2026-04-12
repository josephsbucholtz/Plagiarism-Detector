import os
import sys
import utils

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

# ---------------------- TESTING -------------------------------------

#Texts
declaration_text = "src/data/declaration.txt"
declaration_variant = "src/data/declaration-variant.txt"
repeated_text = "src/data/repeated.txt"


def run_comparison(file1, file2):
    global vocab
    global minhash_func

    #Clean Documents for processing data
    doc1 = utils.clean_document_data(file1)
    doc2 = utils.clean_document_data(file2)

    if not doc1 or not doc2:
        return {"error": "Could not read one or both files."}

    #Create k-shingling for each doc
    a = utils.shingles(doc1)
    b = utils.shingles(doc2)

    #Create our Vocab
    vocab = a.union(b)
    vocab_list = list(vocab)

    if len(vocab) == 0:
        return {"error": "Documents are too short or empty."}

    #Create our sparse vectors (later will become dense vectors)
    a1_hot = [1 if x in a else 0 for x in vocab]
    b1_hot = [1 if x in b else 0 for x in vocab]

    #Create dense vector
    minhash_func = utils.create_minhash_func(len(vocab), 200)

    #Create Signatures
    a_sig = create_hash(a1_hot, len(vocab))
    b_sig = create_hash(b1_hot, len(vocab))

    minhash_similarity = utils.compare_signatures(a_sig, b_sig)
    real_similarity = utils.jaccard_similarity(a, b)

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


if __name__ == "__main__":
    result = run_comparison(declaration_text, declaration_variant)

    if "error" in result:
        print(result["error"])
    else:
        print(result["a_sig"])
        print(result["b_sig"])
        print("Estimated similarity:", result["minhash_similarity"])
        print("Estimated similarity (%):", result["minhash_similarity"] * 100)
        print("Jaccard similarity (REAL):", result["real_similarity"])
        print("Jaccard similarity (REAL %):", result["real_similarity"] * 100)