import pytest
from app.services.rag.semantic_chunker import SemanticChunker


def test_chunker_normal_document():
    chunker = SemanticChunker(target_chunk_words=100, min_chunk_words=20, overlap_words=15)
    sample_text = """
CHAPTER 1: INTRODUCTION TO COMPILERS
A compiler is a computer program that translates computer code written in one programming language into another language.
Compilers perform front-end scanning, parsing, semantic analysis, intermediate representation, optimization, and code generation.

CHAPTER 2: LEXICAL ANALYSIS
Lexical analysis is the process of converting a sequence of characters into a sequence of tokens.
A program that performs lexical analysis may be termed a lexer, tokenizer, or scanner.
    """
    chunks = chunker.chunk_text(sample_text, document_title="Compiler Principles")
    assert len(chunks) >= 2
    assert chunks[0].section_title is not None
    assert chunks[0].word_count > 0
    assert chunks[0].token_count > 0


def test_chunker_short_document():
    chunker = SemanticChunker(target_chunk_words=350, min_chunk_words=5, overlap_words=10)
    short_text = "Quicksort is an efficient sorting algorithm based on divide-and-conquer strategy."
    chunks = chunker.chunk_text(short_text, document_title="Sorting Note")
    assert len(chunks) == 1
    assert chunks[0].word_count > 0


def test_chunker_empty_document():
    chunker = SemanticChunker()
    assert chunker.chunk_text("") == []
    assert chunker.chunk_text("   \n\t  ") == []


def test_chunker_heading_and_page_preservation():
    chunker = SemanticChunker(target_chunk_words=30, min_chunk_words=5, overlap_words=5)
    text = """
--- PAGE 5 ---
CHAPTER 3: PARSING
Parsing or syntactic analysis is the process of analyzing a string of symbols.

--- PAGE 6 ---
SECTION 3.1: CONTEXT FREE GRAMMARS
Context-free grammars provide a formal mechanism for describing the syntax of programming languages.
    """
    chunks = chunker.chunk_text(text, document_title="Parsing Document")
    assert len(chunks) >= 2
    assert chunks[0].page_number in (5, 6)
    assert chunks[0].section_title is not None
