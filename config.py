class Config:
    # 浏览器配置
    CHROME_DRIVER_PATH = None  # 如果 ChromeDriver 在环境变量中，可以设为 None
    BROWSER_TIMEOUT = 10  # 浏览器等待超时时间（秒）
    
    # OCR配置
    TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    # 图像识别配置
    IMAGE_MATCH_THRESHOLD = 0.8  # 图像匹配阈值
    
    # 操作延迟配置
    CLICK_DELAY = 0.5  # 点击操作后的延迟时间（秒）
    PAGE_LOAD_DELAY = 2  # 页面加载后的延迟时间（秒）