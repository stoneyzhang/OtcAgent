class WebAgentException(Exception):
    """Web Agent 基础异常类"""
    pass

class ElementNotFoundException(WebAgentException):
    """元素未找到异常"""
    pass

class PageLoadException(WebAgentException):
    """页面加载异常"""
    pass

class ImageNotFoundException(WebAgentException):
    """图像未找到异常"""
    pass

class ClickException(WebAgentException):
    """点击操作异常"""
    pass