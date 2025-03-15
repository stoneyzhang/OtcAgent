from web_agent import WebAgent
from config import Config
from utils import setup_logger
import time
import os

# 修复语法错误
def main():
    logger = setup_logger()
    logger.info("程序启动")
    agent = WebAgent()
    
    try:
        # 访问 OKX 登录页面
        logger.info("正在访问 OKX 登录页面...")
        agent.load_page("https://www.okx.com/zh-hans/account/login")
        time.sleep(0)  # 移除等待
        
        # 查找并点击二维码登录选项
        logger.info("正在查找'二维码'按钮...")
        try:
            # 尝试多种定位方式
            xpaths = [
                "//span[contains(text(), '二维码')]",  # 包含文本匹配
                "//div[contains(text(), '二维码')]",   # 其他可能的元素
                "//*[contains(text(), '二维码')]"      # 任意元素
            ]
            
            found = False
            for xpath in xpaths:
                element = agent.find_element_by_xpath(xpath)
                if element and element.is_displayed():
                    logger.info(f"找到'二维码'按钮，使用xpath: {xpath}")
                    agent.click_element(element)
                    logger.info("成功点击'二维码'按钮")
                    found = True
                    break
            
            if not found:
                logger.error("未找到'二维码'按钮")
                agent.save_screenshot("qrcode_not_found.png")
                
        except Exception as e:
            logger.error(f"查找二维码按钮时出错: {str(e)}")
        
        # 等待用户扫码登录
        logger.info("请使用手机扫码完成登录...")
        # 检测登录状态，最多等待60秒
        for _ in range(60):
            try:
                # 检查是否存在登录后才会出现的元素
                if agent.find_element_by_xpath("//span[contains(text(), '资产')]"):
                    logger.info("检测到已完成登录")
                    break
            except:
                time.sleep(1)
        
        # 访问 P2P 页面
        logger.info("正在访问 P2P 页面...")
        agent.load_page("https://www.okx.com/zh-hans/p2p/dashboard")
        time.sleep(1)  # 稍微等待一下页面加载
        
        # 查找订单菜单
        logger.info("正在查找'订单'菜单...")
        try:
            xpaths = [
                "//span[text()='订单']",
                "//div[contains(@class, 'menu')]//span[text()='订单']",
                "//*[contains(@class, 'sidebar')]//span[text()='订单']"
            ]
            
            found = False
            for xpath in xpaths:
                element = agent.find_element_by_xpath(xpath)
                if element and element.is_displayed():
                    logger.info(f"找到'订单'菜单，使用xpath: {xpath}")
                    agent.click_element(element)
                    logger.info("成功点击'订单'菜单")
                    found = True
                    break
        except Exception as e:
            logger.error(f"查找订单菜单时出错: {str(e)}")
        
        if not found:
            logger.error("未能找到或点击订单菜单")
            agent.save_screenshot("debug_screenshot.png")
            logger.info("已保存页面截图用于调试")
        
        # 保持程序运行
        logger.info("程序将保持运行状态...")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")

if __name__ == "__main__":
    main()