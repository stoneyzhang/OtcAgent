from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import cv2
import numpy as np
import pytesseract
import pyautogui
import time

class WebAgent:
    def __init__(self):
        # 初始化 Chrome 浏览器
        self.driver = webdriver.Chrome()
        # 设置 pytesseract 路径（需要先安装 Tesseract-OCR）
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
    def load_page(self, url):
        """加载指定URL的网页"""
        try:
            self.driver.get(url)
            return True
        except Exception as e:
            print(f"加载页面失败: {str(e)}")
            return False
            
    def find_text(self, text):
        """在页面中查找指定文本"""
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_containing_text(text)
            )
            return element
        except:
            return None
            
    def click_element(self, element):
        """点击指定元素"""
        try:
            element.click()
            return True
        except:
            # 如果直接点击失败，尝试使用 JavaScript 点击
            try:
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except:
                return False
                
    def find_image_on_screen(self, template_path, threshold=0.8):
        """在屏幕上查找指定图像"""
        # 获取屏幕截图
        screenshot = pyautogui.screenshot()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # 读取模板图像
        template = cv2.imread(template_path)
        
        # 模板匹配
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= threshold:
            return max_loc
        return None
        
    def click_image(self, template_path, threshold=0.8):
        """查找并点击指定图像"""
        location = self.find_image_on_screen(template_path, threshold)
        if location:
            # 获取模板图像尺寸
            template = cv2.imread(template_path)
            h, w = template.shape[:2]
            # 计算中心点
            center_x = location[0] + w//2
            center_y = location[1] + h//2
            # 移动鼠标并点击
            pyautogui.click(center_x, center_y)
            return True
        return False
        
    def close(self):
        """关闭浏览器"""
        self.driver.quit()

# 使用示例
if __name__ == "__main__":
    agent = WebAgent()
    
    # 加载网页
    agent.load_page("https://www.sohu.com")
    time.sleep(5)
    
    # 关闭浏览器
    agent.close()