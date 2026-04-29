from __future__ import annotations

from pathlib import Path

import document
import library_manager
import similarity
import text_processing


def shingles(text: str, k: int = library_manager.DEFAULT_SHINGLE_SIZE):
    return text_processing.shingles(text, k=k)


def compare_signatures(signature_1, signature_2):
    return similarity.compare_signatures(signature_1, signature_2)


def jaccard_similarity(set_1, set_2):
    return similarity.jaccard_similarity(set_1, set_2)


def run_comparison(file1, file2, generate_highlight: bool = False):
    result = library_manager.compare_files(file1, file2)
    if generate_highlight and "error" not in result:
        highlight_path = document.get_wordmap_doc(file1, file2, result["minhash_similarity"] * 100)
        result["highlight_path"] = highlight_path
    return result


def compare_all_files(folder_path):
    folder = Path(folder_path).resolve()
    if folder.is_dir():
        return library_manager.compare_all_library_documents(folder)

    files = sorted(folder.glob("*.txt"))
    results = []

    for left_index in range(len(files)):
        for right_index in range(left_index + 1, len(files)):
            result = run_comparison(files[left_index], files[right_index])
            if "error" not in result:
                results.append(result)

    return results


def compare_with_library(file_path: str, library_dir: str | Path | None = None, top_n: int = 10):
    return library_manager.compare_against_library(file_path, library_dir=library_dir, top_n=top_n)


def rebuild_library_cache(library_dir: str | Path | None = None, force: bool = True):
    return library_manager.rebuild_library_cache(library_dir=library_dir, force=force)


def add_file_to_library(file_path: str, library_dir: str | Path | None = None):
    return library_manager.add_document_to_library(file_path, library_dir=library_dir)


def get_library_summary(library_dir: str | Path | None = None):
    return library_manager.get_library_summary(library_dir=library_dir)
