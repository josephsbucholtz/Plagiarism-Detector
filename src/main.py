import os
import sys
import document
import utils

# ---------------------- TESTING -------------------------------------

#Texts
declaration_text = "src/data/declaration.txt"
declaration_variant = "src/data/declaration-variant.txt"
reorded_declaration = "src/data/declaration-reordered.txt"
short_declaration = "src/data/declaration-short.txt"
declaration_sumary = "src/data/declaration-summary.txt"
repeated_text = "src/data/repeated.txt"
lincoln_text = "src/data/lincoln-address.txt"


if __name__ == "__main__":
    # results = utils.compare_all_files("src/data/")

    # # Sort by highest estimated similarity
    # results.sort(key=lambda x: x["minhash_similarity"], reverse=True)

    # for result in results:
    #     if "error" in results:
    #         print(results["error"])

    #     if result["minhash_similarity"] < 0.05:
    #         continue 

    #     print("\n")
    #     print(f"{os.path.basename(result['file1'])} vs {os.path.basename(result['file2'])}")
    #     print("Estimated similarity:", result["minhash_similarity"])
    #     print("Estimated similarity (%):", result["minhash_similarity"] * 100)
    #     print("Jaccard similarity (REAL):", result["real_similarity"])
    #     print("Jaccard similarity (REAL %):", result["real_similarity"] * 100)
    #     print("\n")
    #     print("-------------------------------------------------")
    #     print("\n")

    result = utils.run_comparison(declaration_text, declaration_variant)
    document.get_wordmap_documents(declaration_text, declaration_variant, result["minhash_similarity"] * 100)
    
    