from web_agent import WebAgent
from config import Config
from utils import setup_logger
import time

def main():
    # 设置日志
    logger = setup_logger()
    
    try:
        # 创建 Web Agent 实例
        agent = WebAgent()
        logger.info("Web Agent 初始化成功")
        
        # 在这里添加您的自动化任务
        # 示例：
        agent.load_page("https://www.example.com")
        time.sleep(Config.PAGE_LOAD_DELAY)
        
        # 执行其他操作...
        
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")
    finally:
        agent.close()
        logger.info("Web Agent 已关闭")

if __name__ == "__main__":
    main()