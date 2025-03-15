from web_agent import WebAgent
from config import Config
from utils import setup_logger
import time
import os
from order_monitor import OrderMonitor

# 修复语法错误
def main():
    logger = setup_logger()
    logger.info("程序启动")
    agent = WebAgent()
    
    try:
        # 访问 OKX 登录页面并完成登录
        logger.info("正在访问 OKX 登录页面...")
        agent.load_page("https://www.okx.com/zh-hans/account/login")
        
        # 查找并点击二维码登录选项
        logger.info("正在查找'二维码'按钮...")
        try:
            xpaths = [
                "//span[contains(text(), '二维码')]",
                "//div[contains(text(), '二维码')]",
                "//*[contains(text(), '二维码')]"
            ]
            
            for xpath in xpaths:
                element = agent.find_element_by_xpath(xpath)
                if element and element.is_displayed():
                    agent.click_element(element)
                    break
                    
        except Exception as e:
            logger.error(f"查找二维码按钮时出错: {str(e)}")
        
        # 等待用户扫码登录
        logger.info("请使用手机扫码完成登录...")
        for _ in range(60):
            try:
                if agent.find_element_by_xpath("//span[contains(text(), '资产')]"):
                    logger.info("检测到已完成登录")
                    break
            except:
                time.sleep(1)
        
        # 访问 P2P 页面
        logger.info("正在访问 P2P 页面...")
        agent.load_page("https://www.okx.com/zh-hans/p2p/dashboard")
        time.sleep(3)  # 等待页面加载
        
        # 查找订单菜单并点击
        logger.info("正在查找'订单'菜单...")
        element = agent.find_element_by_xpath("//span[text()='订单']")
        if element and element.is_displayed():
            agent.click_element(element)
            time.sleep(3)  # 等待页面加载
            
            # 测试查找"订单号"关键字和其他表头
            logger.info("正在查找表头...")
            headers = {
                '订单号': "//*[contains(text(), '订单号')]",
                '方向': "//*[contains(text(), '方向')]",
                '数量': "//*[contains(text(), '数量')]",
                '总金额': "//*[contains(text(), '总金额')]",
                '单价': "//*[contains(text(), '单价')]",
                '对手方': "//*[contains(text(), '对手方')]",
                '订单状态': "//*[contains(text(), '订单状态')]",
                '按时间排序': "//*[contains(text(), '按时间排序')]"
            }
            
            found_headers = {}
            for header_name, xpath in headers.items():
                element = agent.find_element_by_xpath(xpath)
                if element and element.is_displayed():
                    found_headers[header_name] = True
                    logger.info(f"找到表头: {header_name}")
                else:
                    found_headers[header_name] = False
                    logger.error(f"未找到表头: {header_name}")
            
            # 如果所有表头都找到了，保存到Excel
            if all(found_headers.values()):
                logger.info("所有表头都已找到！")
                import pandas as pd
                
                # 创建只包含表头的DataFrame
                df = pd.DataFrame(columns=list(headers.keys()))
                excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'headers.xlsx')
                df.to_excel(excel_path, index=False)
                logger.info(f"表头已保存到: {excel_path}")
                logger.info("OK")
                
                # 开始监控订单号
                logger.info("开始监控订单号...")
                while True:
                    try:
                        # 使用更精确的XPath定位订单号链接
                        order_numbers = agent.driver.find_elements("xpath", "//a[contains(@class, 'link') and contains(@href, '/p2p/order?orderId=')]")
                        
                        if order_numbers:
                            found_orders = []
                            for order_num in order_numbers:
                                if order_num.is_displayed():
                                    # 获取同一行的数据（通过父级td和tr定位）
                                    parent_row = order_num.find_element("xpath", "./ancestor::tr[contains(@class, 'okui-table-row')]")
                                    order_data = {
                                        '订单号': order_num.text,
                                        '方向': parent_row.find_element("xpath", ".//td[2]").text,
                                        '数量': parent_row.find_element("xpath", ".//td[3]").text,
                                        '总金额': parent_row.find_element("xpath", ".//td[4]").text,
                                        '单价': parent_row.find_element("xpath", ".//td[5]").text,
                                        '对手方': parent_row.find_element("xpath", ".//td[6]").text,
                                        '订单状态': parent_row.find_element("xpath", ".//td[7]").text,
                                        '时间': parent_row.find_element("xpath", ".//td[8]").text
                                    }
                                    found_orders.append(order_data)
                                    logger.info(f"找到订单: {order_data['订单号']}")
                            
                            if found_orders:
                                # 保存到orders.xlsx
                                orders_df = pd.DataFrame(found_orders)
                                orders_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'orders.xlsx')
                                
                                if os.path.exists(orders_path):
                                    existing_df = pd.read_excel(orders_path)
                                    orders_df = pd.concat([existing_df, orders_df], ignore_index=True)
                                    orders_df.drop_duplicates(subset=['订单号'], keep='first', inplace=True)
                                
                                orders_df.to_excel(orders_path, index=False)
                                logger.info(f"已保存 {len(found_orders)} 个订单号")
                        
                        time.sleep(10)
                        
                    except KeyboardInterrupt:
                        logger.info("监控被用户中断")
                        break
                    except Exception as e:
                        logger.error(f"监控过程出错: {str(e)}")
                        time.sleep(5)
                
                while True:
                    try:
                        # 查找所有订单行
                        rows = agent.find_elements_by_xpath("//div[contains(@class, 'order-item')]")
                        if rows:
                            orders_data = []
                            for row in rows:
                                try:
                                    order_data = {
                                        '订单号': row.find_element_by_xpath(".//div[string-length(text())=15 and translate(text(), '0123456789', '') = '']").text,
                                        '方向': row.find_element_by_xpath(".//div[contains(text(), '出售') or contains(text(), '购买')]").text,
                                        '数量': row.find_element_by_xpath(".//div[contains(@class, 'amount')]").text.replace('USDT', '').strip(),
                                        '总金额': row.find_element_by_xpath(".//div[contains(text(), 'CNY')]").text,
                                        '单价': row.find_element_by_xpath(".//div[contains(text(), '¥')]").text,
                                        '对手方': row.find_element_by_xpath(".//div[contains(@class, 'user')]").text,
                                        '订单状态': row.find_element_by_xpath(".//div[contains(text(), '您尚未放币') or contains(text(), '待支付')]").text,
                                        '按时间排序': row.find_element_by_xpath(".//div[contains(text(), '/')]").text
                                    }
                                    orders_data.append(order_data)
                                    logger.info(f"成功解析订单: {order_data['订单号']}")
                                except Exception as e:
                                    logger.error(f"解析订单行数据时出错: {str(e)}")
                                    continue
                            
                            if orders_data:
                                # 保存到Excel
                                df = pd.DataFrame(orders_data)
                                excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'orders.xlsx')
                                
                                # 如果文件已存在，读取并追加新数据
                                if os.path.exists(excel_path):
                                    existing_df = pd.read_excel(excel_path)
                                    df = pd.concat([existing_df, df], ignore_index=True)
                                    # 去重
                                    df.drop_duplicates(subset=['订单号'], keep='first', inplace=True)
                                
                                df.to_excel(excel_path, index=False)
                                logger.info(f"发现 {len(orders_data)} 个订单，已保存到: {excel_path}")
                        
                        # 等待一段时间再次检查
                        time.sleep(10)
                        
                    except KeyboardInterrupt:
                        logger.info("监控被用户中断")
                        break
                    except Exception as e:
                        logger.error(f"监控过程出错: {str(e)}")
                        time.sleep(5)
            else:
                logger.error("部分表头未找到")
                agent.save_screenshot("debug_headers.png")
        
        # 保持程序运行
        input("按回车键退出...")
        
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")
    finally:
        agent.close()

if __name__ == "__main__":
    main()