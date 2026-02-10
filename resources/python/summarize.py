#!/usr/bin/env python3
"""Lightweight extractive summarizer for local use.
Usage: python summarize.py <input_file> [--n N] [--context "subject words"]
"""
import sys
import re
import argparse
from collections import defaultdict, Counter

# small spanish stopword set (not exhaustive)
SPANISH_STOPWORDS = set("""
que de la el en y a los del se las por un para con no una su al lo como más
pero sus le ya o este sí porque esta entre cuando muy sin sobre también
me hasta hay donde quien desde todo nos durante todos uno les ni contra
otros ese eso había ante ellos e esto mí hasta
""".split())

SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')
WORD_RE = re.compile(r"\w+", re.UNICODE)


def tokenize_sentences(text):
    sentences = [s.strip() for s in SENTENCE_SPLIT_RE.split(text) if s.strip()]
    return sentences


def tokenize_words(text):
    return [w.lower() for w in WORD_RE.findall(text)]


def score_sentences(sentences, context_words=None):
    words = tokenize_words(" ".join(sentences))
    freq = Counter(w for w in words if w not in SPANISH_STOPWORDS)
    if not freq:
        return {i: 1 for i in range(len(sentences))}

    # boost context words
    if context_words:
        for cw in tokenize_words(context_words):
            if cw in freq:
                freq[cw] *= 2

    scores = {}
    for i, s in enumerate(sentences):
        s_words = [w for w in tokenize_words(s) if w not in SPANISH_STOPWORDS]
        if not s_words:
            scores[i] = 0
            continue
        # sum normalized frequencies
        scores[i] = sum(freq[w] for w in s_words) / len(s_words)
    return scores


def summarize_text(text, n=5, context=None):
    sentences = tokenize_sentences(text)
    if len(sentences) <= n:
        return "\n".join(sentences)
    scores = score_sentences(sentences, context_words=context)
    # pick top n by score
    top_idxs = sorted(scores, key=lambda i: scores[i], reverse=True)[:n]
    top_idxs = sorted(top_idxs)
    summary = "\n".join(sentences[i] for i in top_idxs)
    return summary


def main():
    p = argparse.ArgumentParser()
    p.add_argument('input_file')
    p.add_argument('--n', type=int, default=5)
    p.add_argument('--context', type=str, default=None)
    args = p.parse_args()

    with open(args.input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    summary = summarize_text(text, n=args.n, context=args.context)
    print(summary)


if __name__ == '__main__':
    main()
