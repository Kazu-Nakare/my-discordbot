import math
import base64
import numpy as np


def utf2base(text):
    chars = text
    result = base64.b64encode(chars.encode()).decode()
    # print(result)
    return result


def base2binary(text):
    chars = utf2base(text)
    result = ""
    for i in range(len(chars)):
        result += f'{int(ord(chars[i])):08b}'
    # print(result)
    return result


def binary2bmp(text):
    binary = base2binary(text)
    size = math.ceil(math.sqrt(len(binary)))
    img = np.zeros((size, size), dtype=np.uint8)
    a = 0
    for i in range(size):
        for j in range(size):
            if a < len(binary):
                if binary[a] == "0":
                    img[i, j] = 0
                    a += 1
                elif binary[a] == "1":
                    img[i, j] = 255
                    a += 1
            else:
                img[i, j] = 255
    return img


def bmp2binary(img):
    binary = ""
    for i in range(len(img)):
        for j in range(len(img)):
            if img[i, j] == 0:
                binary += "0"
            elif img[i, j] == 255:
                binary += "1"
            else:
                raise SystemError
    return binary


def binary2base(img):
    chars = bmp2binary(img)
    result = ""
    for i in range(0, len(chars), 8):
        result += chr(int(chars[i:i + 8], 2))
    return result


def base2utf(img):
    chars = binary2base(img)
    result = str(base64.b64decode(chars.encode()).decode())
    return result
