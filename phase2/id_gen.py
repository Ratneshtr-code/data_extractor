# id_gen.py

def make_id(tag, index):
    # tag = UPSC_2025_p1_c1  → append q1
    return f"{tag}_q{index}"
