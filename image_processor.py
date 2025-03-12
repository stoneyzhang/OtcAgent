import cv2
import numpy as np
import pytesseract
from config import Config

class ImageProcessor:
    def __init__(self):
        pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_PATH
        
    def extract_text(self, image):
        """从图像中提取文字"""
        try:
            text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            return text.strip()
        except Exception as e:
            return None
            
    def match_template(self, image, template, threshold=None):
        """模板匹配"""
        if threshold is None:
            threshold = Config.IMAGE_MATCH_THRESHOLD
            
        result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= threshold:
            return max_loc, max_val
        return None, max_val
        
    def preprocess_image(self, image):
        """图像预处理"""
        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # 降噪
        denoised = cv2.fastNlMeansDenoising(gray)
        # 二值化
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary