import unittest
import time
from web_agent import WebAgent
from exceptions import WebAgentException

class TestWebAgent(unittest.TestCase):
    def setUp(self):
        self.agent = WebAgent()
        
    def tearDown(self):
        self.agent.close()
        
    def test_load_page(self):
        result = self.agent.load_page("https://www.example.com")
        self.assertTrue(result)
        
    def test_find_text(self):
        self.agent.load_page("https://www.example.com")
        # 增加等待时间并修改查找的文本
        time.sleep(3)
        element = self.agent.find_text("Example")  # 只查找页面上一定存在的部分文本
        self.assertIsNotNone(element)
        
    def test_find_invalid_text(self):
        self.agent.load_page("https://www.example.com")
        element = self.agent.find_text("NonexistentText123456")
        self.assertIsNone(element)

    def test_page_content(self):
        self.agent.load_page("https://www.example.com")
        time.sleep(2)
        # 打印页面源代码，帮助调试
        print(self.agent.driver.page_source)
        element = self.agent.find_text("Example")
        self.assertIsNotNone(element)

if __name__ == '__main__':
    unittest.main()