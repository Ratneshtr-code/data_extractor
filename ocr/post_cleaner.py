# ocr/post_cleaner.py
# ------------------------------------------------------
# BACKWARD-COMPATIBLE WRAPPER
# ------------------------------------------------------
# The old post_cleaner.py had custom regex-based OCR fixes.
# We now use the new UPSCTextReconstructor for robust,
# UPSC-aware reconstruction.
# ------------------------------------------------------

from utils.upsc_text_reconstructor import reconstruct_text


def clean_ocr_block(text: str) -> str:
    """
    Wrapper kept ONLY for compatibility with run_extract.py.
    """
    return reconstruct_text(text)
