import pandas as pd
from datetime import datetime
import os

class OrderMonitor:
    def __init__(self, agent, logger):
        self.agent = agent
        self.logger = logger
        self.excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'orders.xlsx')
        self.last_order_id = None
        
    def get_order_details(self):
        """获取订单详情"""
        try:
            orders = []
            # 尝试多种方式定位订单
            xpaths = [
                "//div[contains(text(), '订单号')]/following::div[string-length(text())=15 and translate(text(), '0123456789', '') = '']",
                "//td[string-length(text())=15 and translate(text(), '0123456789', '') = '']",
                "//div[@class='order-list']//tr//td[string-length(text())=15]"
            ]
            
            for xpath in xpaths:
                order_elements = self.agent.find_elements_by_xpath(xpath)
                if order_elements:
                    for element in order_elements:
                        try:
                            # 获取订单号
                            order_id = element.text.strip()
                            if not order_id.isdigit() or len(order_id) != 15:
                                continue
                                
                            # 从订单号元素往上找到整行数据
                            row = element.find_element_by_xpath("./ancestor::tr")
                            
                            order = {
                                '订单号': order_id,
                                '方向': self._get_text(row, ".//td[2]"),
                                '数量': self._get_text(row, ".//td[3]"),
                                '总金额': self._get_text(row, ".//td[5]"),
                                '单价': self._get_text(row, ".//td[4]"),
                                '对手方': self._get_text(row, ".//td[6]"),
                                '订单状态': self._get_text(row, ".//td[7]"),
                                '按时间排序': self._get_text(row, ".//td[8]")
                            }
                            
                            # 只记录新订单
                            if self.last_order_id != order['订单号']:
                                orders.append(order)
                                self.last_order_id = order['订单号']
                                
                        except Exception as e:
                            self.logger.error(f"解析订单行时出错: {str(e)}")
                            continue
                    
                    # 如果找到了订单就不再尝试其他xpath
                    if orders:
                        break
            
            return orders
            
        except Exception as e:
            self.logger.error(f"获取订单详情失败: {str(e)}")
            return []
    
    def _get_text(self, element, xpath):
        """获取元素文本"""
        try:
            text_element = element.find_element_by_xpath(xpath)
            return text_element.text.strip()
        except:
            return ""
    
    def save_to_excel(self, orders):
        """保存订单到Excel"""
        try:
            # 读取现有数据或创建新的DataFrame
            if os.path.exists(self.excel_path):
                df = pd.read_excel(self.excel_path)
            else:
                df = pd.DataFrame()
            
            # 添加新订单
            new_df = pd.DataFrame(orders)
            df = pd.concat([df, new_df], ignore_index=True)
            
            # 保存到Excel，确保不重复
            df.drop_duplicates(subset=['订单号'], keep='first', inplace=True)
            df.to_excel(self.excel_path, index=False)
            self.logger.info(f"订单已保存到: {self.excel_path}")
            
        except Exception as e:
            self.logger.error(f"保存订单到Excel失败: {str(e)}")