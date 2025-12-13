# utils/pdf_converter.py

import os
from pdf2image import convert_from_path

def pdf_to_images(pdf_path, output_folder, dpi=600):
    os.makedirs(output_folder, exist_ok=True)

    print(f"[PDF] Converting '{pdf_path}' to images at {dpi} DPI...")

    pages = convert_from_path(pdf_path, dpi=dpi)

    image_paths = []
    for i, page in enumerate(pages):
        out_path = os.path.join(output_folder, f"page_{i+1}.png")
        page.save(out_path, "PNG")
        image_paths.append(out_path)

    print(f"[PDF] Extracted {len(image_paths)} page images.")
    return image_paths
