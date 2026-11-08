import easyocr

# Initialize OCR reader only once
reader = easyocr.Reader(["en"], gpu=False)


def extract_text_from_image(image_path):
    """
    Extract text from an image using EasyOCR.
    """
    results = reader.readtext(
        str(image_path),
        detail=0
    )

    print("Detected Text:", results)

    return results
