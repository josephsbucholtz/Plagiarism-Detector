from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import similarity
import text_processing


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_LIBRARY_DIR = BASE_DIR / "essays"
CACHE_DIR = BASE_DIR / "cache"
LIBRARY_CACHE_DIR = CACHE_DIR / "libraries"
HIGHLIGHT_DIR = BASE_DIR / "highlight-docs"
DEFAULT_SHINGLE_SIZE = 3
USE_LEMMA = True


def resolve_library_dir(library_dir: str | Path | None = None) -> Path:
    if library_dir is None:
        return DEFAULT_LIBRARY_DIR.resolve()
    return Path(library_dir).resolve()


def ensure_runtime_directories(library_dir: str | Path | None = None) -> Path:
    resolved_library_dir = resolve_library_dir(library_dir)
    resolved_library_dir.mkdir(parents=True, exist_ok=True)
    LIBRARY_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    HIGHLIGHT_DIR.mkdir(parents=True, exist_ok=True)
    return resolved_library_dir


def _path_digest(path: Path) -> str:
    return hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()[:16]


def _text_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _shingle_digest(shingles: set[str]) -> str:
    serialized = "\n".join(sorted(shingles))
    return _text_digest(serialized)


def _library_cache_bundle(library_dir: str | Path | None = None) -> dict[str, Path]:
    resolved_library_dir = resolve_library_dir(library_dir)
    library_key = _path_digest(resolved_library_dir)
    bundle_dir = LIBRARY_CACHE_DIR / library_key
    documents_dir = bundle_dir / "documents"
    index_file = bundle_dir / "library_index.json"
    return {
        "library_dir": resolved_library_dir,
        "library_key": Path(library_key),
        "bundle_dir": bundle_dir,
        "documents_dir": documents_dir,
        "index_file": index_file,
    }


def _cache_path_for(source_path: Path, library_dir: str | Path | None = None) -> Path:
    bundle = _library_cache_bundle(library_dir)
    return bundle["documents_dir"] / f"{_path_digest(source_path)}.json"


def _load_index_for_library(library_dir: str | Path | None = None) -> dict | None:
    index_file = _library_cache_bundle(library_dir)["index_file"]
    if not index_file.exists():
        return None
    return json.loads(index_file.read_text(encoding="utf-8"))


def _save_index_for_library(index: dict, library_dir: str | Path | None = None) -> None:
    bundle = _library_cache_bundle(library_dir)
    ensure_runtime_directories(bundle["library_dir"])
    bundle["documents_dir"].mkdir(parents=True, exist_ok=True)
    bundle["index_file"].write_text(json.dumps(index, ensure_ascii=True, indent=2), encoding="utf-8")


def _current_index_settings() -> dict:
    return {
        "shingle_size": DEFAULT_SHINGLE_SIZE,
        "use_lemma": USE_LEMMA,
        "num_permutations": similarity.DEFAULT_NUM_PERMUTATIONS,
        "seed": similarity.DEFAULT_RANDOM_SEED,
    }


def _index_matches_current_config(index: dict | None, library_dir: str | Path | None = None) -> bool:
    if not index:
        return False

    if index.get("library_dir") != str(resolve_library_dir(library_dir)):
        return False

    return index.get("settings") == _current_index_settings()


def _unique_library_path(file_name: str, library_dir: str | Path | None = None) -> Path:
    resolved_library_dir = ensure_runtime_directories(library_dir)
    target = resolved_library_dir / file_name
    if not target.exists():
        return target

    stem = target.stem
    suffix = target.suffix
    counter = 1
    while True:
        candidate = resolved_library_dir / f"{stem}-{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def build_document_profile(
    file_path: str | Path,
    shingle_size: int = DEFAULT_SHINGLE_SIZE,
    use_lemma: bool = USE_LEMMA,
) -> dict:
    source_path = Path(file_path).resolve()
    raw_text = text_processing.read_text(source_path)
    normalized_text = text_processing.normalize_text(raw_text, use_lemma=use_lemma)
    shingles = text_processing.shingles(normalized_text, k=shingle_size)
    signature = similarity.minhash_signature(shingles)

    return {
        "file_name": source_path.name,
        "file_path": str(source_path),
        "raw_text": raw_text,
        "normalized_text": normalized_text,
        "shingles": sorted(shingles),
        "signature": signature,
        "num_tokens": len(normalized_text.split()),
        "num_shingles": len(shingles),
        "shingle_size": shingle_size,
        "normalized_hash": _text_digest(normalized_text),
        "shingle_fingerprint": _shingle_digest(shingles),
        "source_size": source_path.stat().st_size,
        "source_mtime_ns": source_path.stat().st_mtime_ns,
    }


def _profile_to_metadata(profile: dict, cache_path: Path) -> dict:
    return {
        "file_name": profile["file_name"],
        "file_path": profile["file_path"],
        "cache_path": str(cache_path),
        "normalized_hash": profile["normalized_hash"],
        "shingle_fingerprint": profile["shingle_fingerprint"],
        "num_tokens": profile["num_tokens"],
        "num_shingles": profile["num_shingles"],
        "source_size": profile["source_size"],
        "source_mtime_ns": profile["source_mtime_ns"],
    }


def save_profile_cache(profile: dict, library_dir: str | Path | None = None, cache_path: Path | None = None) -> Path:
    resolved_library_dir = ensure_runtime_directories(library_dir)
    bundle = _library_cache_bundle(resolved_library_dir)
    bundle["documents_dir"].mkdir(parents=True, exist_ok=True)
    destination = cache_path or _cache_path_for(Path(profile["file_path"]), resolved_library_dir)
    destination.write_text(json.dumps(profile, ensure_ascii=True, indent=2), encoding="utf-8")
    return destination


def load_profile_cache(cache_path: str | Path) -> dict:
    return json.loads(Path(cache_path).read_text(encoding="utf-8"))


def rebuild_library_cache(library_dir: str | Path | None = None, force: bool = False) -> dict:
    resolved_library_dir = ensure_runtime_directories(library_dir)
    bundle = _library_cache_bundle(resolved_library_dir)
    existing_index = _load_index_for_library(resolved_library_dir) or {"documents": []}
    existing_documents = {item["file_path"]: item for item in existing_index.get("documents", [])}
    document_entries = []
    active_cache_paths = set()

    bundle["documents_dir"].mkdir(parents=True, exist_ok=True)

    for source_path in sorted(resolved_library_dir.glob("*.txt")):
        source_key = str(source_path.resolve())
        cache_path = _cache_path_for(source_path, resolved_library_dir)
        previous_entry = existing_documents.get(source_key)
        source_stat = source_path.stat()

        is_current = (
            not force
            and previous_entry is not None
            and previous_entry.get("source_mtime_ns") == source_stat.st_mtime_ns
            and previous_entry.get("source_size") == source_stat.st_size
            and cache_path.exists()
        )

        if is_current:
            document_entries.append(previous_entry)
            active_cache_paths.add(Path(previous_entry["cache_path"]))
            continue

        profile = build_document_profile(source_path)
        cache_path = save_profile_cache(profile, resolved_library_dir, cache_path=cache_path)
        document_entries.append(_profile_to_metadata(profile, cache_path))
        active_cache_paths.add(cache_path)

    for cached_file in bundle["documents_dir"].glob("*.json"):
        if cached_file not in active_cache_paths:
            cached_file.unlink()

    index = {
        "library_dir": str(resolved_library_dir),
        "settings": _current_index_settings(),
        "documents": sorted(document_entries, key=lambda item: item["file_name"].lower()),
    }
    _save_index_for_library(index, resolved_library_dir)
    return index


def ensure_library_index(library_dir: str | Path | None = None) -> dict:
    resolved_library_dir = ensure_runtime_directories(library_dir)
    index = _load_index_for_library(resolved_library_dir)
    if not _index_matches_current_config(index, resolved_library_dir):
        return rebuild_library_cache(resolved_library_dir, force=True)
    return rebuild_library_cache(resolved_library_dir, force=False)


def compare_profiles(profile_1: dict, profile_2: dict) -> dict:
    shingles_1 = set(profile_1["shingles"])
    shingles_2 = set(profile_2["shingles"])
    common_shingles = shingles_1.intersection(shingles_2)
    vocabulary = shingles_1.union(shingles_2)

    return {
        "file1": profile_1["file_path"],
        "file2": profile_2["file_path"],
        "file1_name": profile_1["file_name"],
        "file2_name": profile_2["file_name"],
        "minhash_similarity": similarity.compare_signatures(profile_1["signature"], profile_2["signature"]),
        "real_similarity": similarity.jaccard_similarity(shingles_1, shingles_2),
        "num_shingles_doc1": len(shingles_1),
        "num_shingles_doc2": len(shingles_2),
        "common_shingles": len(common_shingles),
        "vocab_size": len(vocabulary),
        "shared_shingles": sorted(common_shingles),
        "shingle_size": profile_1.get("shingle_size", DEFAULT_SHINGLE_SIZE),
        "identical_shingles": profile_1["shingle_fingerprint"] == profile_2["shingle_fingerprint"],
    }


def compare_files(file_1: str | Path, file_2: str | Path) -> dict:
    profile_1 = build_document_profile(file_1)
    profile_2 = build_document_profile(file_2)

    if not profile_1["shingles"] or not profile_2["shingles"]:
        return {"error": "Documents are too short or empty after preprocessing."}

    return compare_profiles(profile_1, profile_2)


def compare_all_library_documents(library_dir: str | Path | None = None) -> list[dict]:
    index = ensure_library_index(library_dir)
    documents = [load_profile_cache(item["cache_path"]) for item in index.get("documents", [])]
    results = []

    for left_index in range(len(documents)):
        for right_index in range(left_index + 1, len(documents)):
            results.append(compare_profiles(documents[left_index], documents[right_index]))

    return results


def get_library_summary(library_dir: str | Path | None = None) -> dict:
    resolved_library_dir = ensure_runtime_directories(library_dir)
    index = ensure_library_index(resolved_library_dir)
    return {
        "library_dir": str(resolved_library_dir),
        "document_count": len(index.get("documents", [])),
        "cache_ready": all(Path(item["cache_path"]).exists() for item in index.get("documents", [])),
        "documents": index.get("documents", []),
    }


def compare_against_library(file_path: str | Path, library_dir: str | Path | None = None, top_n: int = 10) -> dict:
    resolved_library_dir = ensure_runtime_directories(library_dir)
    index = ensure_library_index(resolved_library_dir)
    query_profile = build_document_profile(file_path)

    if not query_profile["shingles"]:
        return {"error": "Document is too short or empty after preprocessing."}

    results = []
    duplicate_match = None

    for item in index.get("documents", []):
        cached_profile = load_profile_cache(item["cache_path"])
        comparison = compare_profiles(query_profile, cached_profile)
        results.append(comparison)

        if comparison["identical_shingles"] and duplicate_match is None:
            duplicate_match = item

    results.sort(
        key=lambda result: (result["minhash_similarity"], result["real_similarity"], result["common_shingles"]),
        reverse=True,
    )

    return {
        "query_file": str(Path(file_path).resolve()),
        "library_dir": str(resolved_library_dir),
        "library_size": len(index.get("documents", [])),
        "duplicate_found": duplicate_match is not None,
        "duplicate_match": duplicate_match,
        "results": results[:top_n],
    }


def add_document_to_library(file_path: str | Path, library_dir: str | Path | None = None) -> dict:
    resolved_library_dir = ensure_runtime_directories(library_dir)
    source_path = Path(file_path).resolve()
    if not source_path.exists():
        return {"error": f"File not found: {source_path}"}

    comparison_report = compare_against_library(source_path, resolved_library_dir, top_n=1_000_000)
    if "error" in comparison_report:
        return comparison_report

    if comparison_report["duplicate_found"]:
        duplicate = comparison_report["duplicate_match"]
        return {
            "added": False,
            "duplicate_found": True,
            "existing_file": duplicate["file_name"],
            "existing_path": duplicate["file_path"],
            "library_dir": str(resolved_library_dir),
        }

    target_path = _unique_library_path(source_path.name, resolved_library_dir)
    shutil.copy2(source_path, target_path)

    profile = build_document_profile(target_path)
    cache_path = save_profile_cache(profile, resolved_library_dir)
    index = ensure_library_index(resolved_library_dir)
    documents = [item for item in index.get("documents", []) if item["file_path"] != str(target_path.resolve())]
    documents.append(_profile_to_metadata(profile, cache_path))
    index["documents"] = sorted(documents, key=lambda item: item["file_name"].lower())
    _save_index_for_library(index, resolved_library_dir)

    return {
        "added": True,
        "duplicate_found": False,
        "stored_file": target_path.name,
        "stored_path": str(target_path.resolve()),
        "library_dir": str(resolved_library_dir),
        "library_size": len(index["documents"]),
    }
