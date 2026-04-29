from __future__ import annotations

import argparse
from pathlib import Path
import time

import document
import utils


def print_pair_result(result: dict) -> None:
    print()
    print(f"{Path(result['file1']).name} vs {Path(result['file2']).name}")
    print(f"MinHash similarity: {result['minhash_similarity']:.4f} ({result['minhash_similarity'] * 100:.2f}%)")
    print(f"Jaccard similarity: {result['real_similarity']:.4f} ({result['real_similarity'] * 100:.2f}%)")
    print(f"Common shingles: {result['common_shingles']}")
    print(f"Vocabulary size: {result['vocab_size']}")
    if result.get("highlight_path"):
        print(f"Highlight map: {result['highlight_path']}")


def compare_library_documents(min_similarity: float) -> None:
    start_time = time.time()
    results = utils.compare_all_files("src/essays")
    results.sort(key=lambda item: (item["minhash_similarity"], item["real_similarity"]), reverse=True)

    suspicious_results = [result for result in results if result["minhash_similarity"] >= min_similarity]
    for result in suspicious_results:
        result["highlight_path"] = document.get_wordmap_doc(
            result["file1"],
            result["file2"],
            result["minhash_similarity"] * 100,
        )
        print_pair_result(result)

    print()
    print(f"Compared {len(results)} document pairs in {time.time() - start_time:.2f} seconds.")
    print(f"Pairs above threshold {min_similarity:.2f}: {len(suspicious_results)}")


def compare_single_file(file_path: str, top_n: int) -> None:
    report = utils.compare_with_library(file_path, "src/essays", top_n=top_n)
    if "error" in report:
        print(report["error"])
        return

    if report["duplicate_found"]:
        duplicate = report["duplicate_match"]
        print(f"Duplicate detected: {duplicate['file_name']} ({duplicate['file_path']})")
    else:
        print("No exact shingle duplicate found in the library.")

    print(f"Library size: {report['library_size']} documents")
    for result in report["results"]:
        print_pair_result(result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Plagiarism detector with cached library indexing.")
    parser.add_argument("--compare-file", help="Compare one file against the cached library.")
    parser.add_argument("--add-file", help="Add a file to the library if it does not already exist.")
    parser.add_argument("--rebuild-cache", action="store_true", help="Rebuild cached shingles/signatures for the library.")
    parser.add_argument("--top", type=int, default=5, help="Number of library matches to display.")
    parser.add_argument("--min-similarity", type=float, default=0.30, help="Threshold for batch reporting.")
    args = parser.parse_args()

    if args.rebuild_cache:
        index = utils.rebuild_library_cache("src/essays", force=True)
        print(f"Rebuilt cache for {len(index['documents'])} library documents.")

    if args.add_file:
        result = utils.add_file_to_library(args.add_file, "src/essays")
        if "error" in result:
            print(result["error"])
        elif result["duplicate_found"]:
            print(f"File already exists as {result['existing_file']} ({result['existing_path']})")
        else:
            print(f"Added {result['stored_file']} to library at {result['stored_path']}")

    if args.compare_file:
        compare_single_file(args.compare_file, top_n=args.top)
        return

    if not args.rebuild_cache and not args.add_file:
        compare_library_documents(args.min_similarity)


if __name__ == "__main__":
    main()
