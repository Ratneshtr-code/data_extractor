# phase2/question_extractor.py
# ------------------------------------------------------
# BACKWARD COMPATIBILITY WRAPPER
# ------------------------------------------------------
# The old logic used regex on question numbers. That fails
# on UPSC PDFs due to OCR distortion.
#
# We now use:
#   utils/upsc_question_block_detector.py
#
# This module keeps the same function signature so that
# no other part of the pipeline breaks.
# ------------------------------------------------------

from utils.upsc_question_block_detector import detect_question_blocks


def split_into_questions(column_text: str):
    """
    Wrapper for backward compatibility.
    New implementation uses UPSCQuestionBlockDetector.
    """

    return detect_question_blocks(column_text)
