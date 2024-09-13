import base64
from django.core.files.base import ContentFile

def base64_to_image(base64_string, file_name):
    if "data:" in base64_string and ";base64," in base64_string:
        base64_string = base64_string.split(";base64,")[1]
    
    try:
        image_data = base64.b64decode(base64_string)
    except (TypeError, ValueError) as e:
        raise ValueError("Invalid base64 string provided") from e
    
    return ContentFile(image_data, name=file_name)
