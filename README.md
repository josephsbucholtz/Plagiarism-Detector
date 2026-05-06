# Plagiarism-Detector  
**CS 122 Advanced Python Project: Locality Sensitive Hashing and MinHash**

A plagiarism detection project that uses **MinHash** with cached shingles/signatures to measure similarity between documents and manage a reusable comparison library.

---

## Setup

Clone Repo
```bash
git clone https://github.com/josephsbucholtz/Plagiarism-Detector.git
```

CD into repo
```bash
cd Plagiarism-Detector
```

Setup virtual environment
```bash
python3 -m venv .venv
```

Source venv
```bash
Mac/Linux: source .venv/bin/activate  
Windows: .venv\Scripts\activate
```

install dependencies
```bash
pip install -r requirements.txt
```

## Features

- Compare two text files directly.
- Compare a new file against the default library in `src/essays` or any folder you choose in the UI.
- Cache preprocessed shingles and MinHash signatures in `src/cache` for faster repeated comparisons.
- Add a file into the library only if its shingle set is not already present.
- Generate Word highlight maps in `src/highlight-docs` for suspicious matches.

## Run

Launch the desktop UI:

```bash
python src/ui.py
```

Useful CLI commands:

```bash
python src/main.py --rebuild-cache
python src/main.py --compare-file path/to/new-file.txt --top 5
python src/main.py --add-file path/to/new-file.txt
python src/main.py
```
