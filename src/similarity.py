from __future__ import annotations

from functools import lru_cache
from hashlib import blake2b
from random import Random


DEFAULT_NUM_PERMUTATIONS = 128
DEFAULT_RANDOM_SEED = 42
_LARGE_PRIME = 2_305_843_009_213_693_951


def stable_hash(value: str) -> int:
    digest = blake2b(value.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, byteorder="big", signed=False)


@lru_cache(maxsize=None)
def _hash_coefficients(num_permutations: int, seed: int):
    random_generator = Random(seed)
    return [
        (
            random_generator.randrange(1, _LARGE_PRIME - 1),
            random_generator.randrange(0, _LARGE_PRIME - 1),
        )
        for _ in range(num_permutations)
    ]


def minhash_signature(
    shingles: set[str],
    num_permutations: int = DEFAULT_NUM_PERMUTATIONS,
    seed: int = DEFAULT_RANDOM_SEED,
) -> list[int]:
    if not shingles:
        return []

    shingle_hashes = [stable_hash(shingle) for shingle in shingles]
    signature = []

    for coefficient_a, coefficient_b in _hash_coefficients(num_permutations, seed):
        minimum_hash = min(
            ((coefficient_a * shingle_hash + coefficient_b) % _LARGE_PRIME)
            for shingle_hash in shingle_hashes
        )
        signature.append(minimum_hash)

    return signature


def compare_signatures(signature_1: list[int], signature_2: list[int]) -> float:
    if not signature_1 or not signature_2 or len(signature_1) != len(signature_2):
        return 0.0

    matches = sum(1 for left, right in zip(signature_1, signature_2) if left == right)
    return matches / len(signature_1)


def jaccard_similarity(set_1: set[str], set_2: set[str]) -> float:
    union = set_1.union(set_2)
    if not union:
        return 0.0
    return len(set_1.intersection(set_2)) / len(union)
