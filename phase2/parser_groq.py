# phase2/parser_groq.py
# ------------------------------------------------------
# DEPRECATED FULL-COLUMN PARSER (NOW A COMPATIBILITY WRAPPER)
# ------------------------------------------------------
# All logic is moved to per-block parsing inside:
#   phase2/block_parser.py
#
# This file now only provides a wrapper for backward compatibility.
# ------------------------------------------------------

from phase2.block_parser import parse_block


def parse_full_column(text: str, tag: str):
    """
    Backward-compatible wrapper.
    Delegates to per-block LLM parsing.
    However, dataset_builder now calls parse_block() directly
    for each segmented question block.
    """
    return parse_block(text, tag)
