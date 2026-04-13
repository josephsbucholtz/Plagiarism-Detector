import os
import sys
import itertools
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

    #Create k-shingling for each doc
    a = utils.shingles(doc1)
    b = utils.shingles(doc2)

    #Create our Vocab
    vocab = a.union(b)

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


if __name__ == "__main__":
    results = compare_all_files("src/data/")

    # Sort by highest estimated similarity
    results.sort(key=lambda x: x["minhash_similarity"], reverse=True)

    if "error" in results:
        print(results["error"])
    
    for result in results:
        print("\n")
        print(f"{os.path.basename(result['file1'])} vs {os.path.basename(result['file2'])}")
        print("Estimated similarity:", result["minhash_similarity"])
        print("Estimated similarity (%):", result["minhash_similarity"] * 100)
        print("Jaccard similarity (REAL):", result["real_similarity"])
        print("Jaccard similarity (REAL %):", result["real_similarity"] * 100)
        print("\n")
        print("-------------------------------------------------")
        print("\n")