import os
import string
from docx import Document
from docx.enum.text import WD_COLOR_INDEX
import spacy
import utils

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

def build_highlighted_doc(words, matching_pairs, file1name, file2name, similiarity, output_name):
    doc = Document()

    header = "Comparing: " + file1name + " vs. " + file2name 
    sim = " (" + str(similiarity) + "% similar)"
    header = header.upper()
    p = doc.add_paragraph() 
    runner = p.add_run(header)
    runner.bold = True
    p = p.add_run(sim) 
    p = doc.add_paragraph()

    i = 0
    while i < len(words):
        if i < len(words) - 1 and (words[i], words[i + 1]) in matching_pairs:
            run = p.add_run(words[i] + " " + words[i + 1] + " ")
            run.font.highlight_color = WD_COLOR_INDEX.RED
            i += 2
        else:
            p.add_run(words[i] + " ")
            i += 1

    full_path = os.path.join("src/highlight/", output_name)
    doc.save(full_path)


def get_wordmap_documents(file1: str, file2: str, similiarity):
    raw_doc1 = clean_document_data(file1)
    raw_doc2 = clean_document_data(file2)

    doc1_shingles = utils.shingles(raw_doc1)
    doc2_shingles = utils.shingles(raw_doc2)

    combined_shingles = doc1_shingles.intersection(doc2_shingles)

    wordlist1 = raw_doc1.split()
    wordlist2 = raw_doc2.split()

    file1name = file1.split('/').pop().split('.')[0]
    file2name = file2.split('/').pop().split('.')[0]

    file1_output = "highlight-" + file1name + ".docx"
    file2_output = "highlight-" + file2name + ".docx"

    build_highlighted_doc(wordlist1, combined_shingles, file1name, file2name, similiarity, file1_output)
    build_highlighted_doc(wordlist2, combined_shingles, file2name, file1name, similiarity, file2_output)