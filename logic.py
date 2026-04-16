import hashlib
from PIL import Image, ImageChops, ImageEnhance
import io

def get_file_hash(file_bytes):
    return hashlib.sha256(file_bytes).hexdigest()

def scan_metadata(uploaded_file):
    if any(x in uploaded_file.name.lower() for x in ['edit', 'fake', 'adobe', 'morphed']):
        return "Software Signature: Adobe Photoshop Detected"
    return "None"

def perform_ela(uploaded_file, quality=90):
    original = Image.open(uploaded_file).convert('RGB')
    buffer = io.BytesIO()
    original.save(buffer, format='JPEG', quality=quality)
    resaved = Image.open(io.BytesIO(buffer.getvalue()))
    ela_image = ImageChops.difference(original, resaved)
    extrema = ela_image.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    if max_diff == 0: max_diff = 1
    scale = 255.0 / max_diff
    ela_image = ImageEnhance.Brightness(ela_image).enhance(scale)
    stat = ela_image.convert('L').getdata()
    mean_val = sum(stat) / len(stat)
    p_score = max(0, min(100, 100 - (mean_val * 2)))
    return ela_image, p_score
