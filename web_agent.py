from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import cv2
import numpy as np
import pytesseract
import pyautogui
import time
import os
import logging

class WebAgent:
    def __init__(self, ignore_errors=None):
        # 设置日志记录器
        self.logger = logging.getLogger('WebAgent')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # 存储要忽略的错误
        self.ignore_errors = ignore_errors or []
        
        try:
            # 配置Chrome选项
            options = webdriver.ChromeOptions()
            
            # 忽略特定错误
            if self.ignore_errors:
                for error in self.ignore_errors:
                    options.add_argument(f"--disable-features={error}")
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.maximize_window()
        except Exception as e:
            self.logger.error(f"初始化WebDriver失败: {str(e)}")
            raise

    def find_element_by_xpath(self, xpath, max_retries=3, retry_delay=1):
        for attempt in range(max_retries):
            try:
                element = self.driver.find_element("xpath", xpath)
                return element
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise e
    
    def load_page(self, url, max_retries=3, retry_delay=2):
        for attempt in range(max_retries):
            try:
                self.driver.get(url)
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    raise e
        return False  # 如果所有重试都失败
            
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
    
    def save_screenshot(self, filename):
        """保存页面截图"""
        try:
            # 确保使用绝对路径
            if not os.path.isabs(filename):
                filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
            
            # 保存截图
            self.driver.save_screenshot(filename)
            return True
        except Exception as e:
            print(f"截图失败: {str(e)}")
            return False
            
# 使用示例
if __name__ == "__main__":
    agent = WebAgent()
    
    # 加载网页
    agent.load_page("https://www.sohu.com")
    time.sleep(5)
    
    # 关闭浏览器
    agent.close()