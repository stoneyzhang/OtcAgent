import pyautogui
import random
import time
from config import Config

class MouseController:
    def __init__(self):
        pyautogui.FAILSAFE = True
        
    def move_to(self, x, y, duration=None):
        """移动鼠标到指定位置"""
        if duration is None:
            duration = random.uniform(0.1, 0.3)
        pyautogui.moveTo(x, y, duration=duration)
        
    def click(self, x=None, y=None, button='left'):
        """点击指定位置"""
        if x is not None and y is not None:
            self.move_to(x, y)
        pyautogui.click(button=button)
        time.sleep(Config.CLICK_DELAY)
        
    def double_click(self, x=None, y=None):
        """双击指定位置"""
        if x is not None and y is not None:
            self.move_to(x, y)
        pyautogui.doubleClick()
        time.sleep(Config.CLICK_DELAY)
        
    def drag_to(self, x, y, duration=0.5):
        """拖拽到指定位置"""
        pyautogui.dragTo(x, y, duration=duration)