import base64

def png_to_base64(filepath):
    content = open(filepath, "rb").read()
    base64_utf8_str = base64.b64encode(content).decode("utf-8")
    dataurl = f"data:image/png;base64,{base64_utf8_str}"
    return dataurl