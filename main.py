import json
import os
import sys

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path

# Возможно напрямую указать путь к tesseract.exe, в случае если он не указан в PATH
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def is_tesseract_lang_installed(lang_code):
    try:
        langs = pytesseract.get_languages(config="")
        return lang_code in langs
    except pytesseract.TesseractNotFoundError:
        print("[ERROR] Tesseract не установлен или не найден.")
        return False
    except Exception as e:
        print(f"[ERROR] Не удалось получить список языков: {e}")
        return False


def preprocess_image(pil_image):
    img = np.array(pil_image.convert("L"))
    img = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    return img


def ocr_pdf_to_json(pdf_path, output_json_path, lang="rus"):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Файл не найден: {pdf_path}")

    if not is_tesseract_lang_installed(lang):
        raise RuntimeError(f"Язык {lang} не установлен.")
    try:
        print("[INFO] Конвертация PDF в изображения...")
        images = convert_from_path(pdf_path)
    except Exception as e:
        raise RuntimeError(f"Ошибка при конвертации PDF в изображения: {e}")

    if not images:
        raise ValueError("PDF не содержит страниц или не удалось конвертировать.")

    result = {}
    for idx, image in enumerate(images, start=1):
        try:
            print(f"[INFO] Обработка страницы {idx}...")
            img = preprocess_image(image)
            text = pytesseract.image_to_string(image, lang=lang)
            result[f"page_{idx}"] = text.strip()
        except pytesseract.TesseractError as e:
            result[f"page_{idx}"] = f"[ERROR] Ошибка OCR: {str(e)}"

    try:
        print("[INFO] Сохранение результата в JSON...")
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        print(f"[DONE] Результат сохранён в {output_json_path}")
    except Exception as e:
        raise RuntimeError(f"Ошибка при сохранении JSON: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Использование: python main.py input.pdf output.json [lang]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    json_path = sys.argv[2]
    lang = sys.argv[3] if len(sys.argv) > 3 else "rus"

    try:
        ocr_pdf_to_json(pdf_path, json_path, lang)
    except Exception as e:
        print(f"[FATAL ERROR] {e}")
