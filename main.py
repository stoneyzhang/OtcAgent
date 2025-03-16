from web_agent import WebAgent
from config import Config
from utils import setup_logger
import time
import os
import pandas as pd  # 保留pandas导入，以备后用
from fix_orders import fix_orders_excel  # 添加这行导入

def main():
    logger = setup_logger()
    logger.info("程序启动")
    
    # 创建已处理订单号的集合
    processed_order_ids = set()
    
    # 先修复现有的orders.xlsx文件
    try:
        fix_orders_excel()
    except Exception as e:
        logger.error(f"修复orders.xlsx失败: {str(e)}")
    
    # 如果orders.xlsx存在，读取已有的订单号到集合中
    orders_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'orders.xlsx')
    if os.path.exists(orders_path):
        try:
            existing_df = pd.read_excel(orders_path)
            if '订单号' in existing_df.columns:
                processed_order_ids.update(existing_df['订单号'].astype(str).tolist())
                logger.info(f"已从Excel加载 {len(processed_order_ids)} 个处理过的订单号")
        except Exception as e:
            logger.error(f"读取已处理订单时出错: {str(e)}")
    
    # 配置 Selenium 选项来忽略特定错误
    agent = WebAgent(ignore_errors=[
        "Failed to resolve address",
        "ERR_NAME_NOT_RESOLVED",
        "online-metrix.net"
    ])
    
    try:
        # 访问 OKX 登录页面并完成登录
        logger.info("正在访问 OKX 登录页面...")
        max_retries = 3
        for retry in range(max_retries):
            try:
                agent.load_page("https://www.okx.com/zh-hans/account/login")
                time.sleep(3)  # 等待页面加载
                break
            except Exception as e:
                if retry < max_retries - 1:
                    logger.warning(f"加载登录页面失败，正在重试 ({retry + 1}/{max_retries})")
                    time.sleep(2)
                else:
                    raise Exception(f"无法加载登录页面: {str(e)}")
        
        # 查找并点击二维码登录选项
        logger.info("正在查找'二维码'按钮...")
        try:
            qr_xpaths = [
                "//span[contains(text(), '二维码')]",
                "//div[contains(text(), '二维码')]",
                "//*[contains(text(), '二维码')]",
                "//div[contains(@class, 'qrcode')]",
                "//div[contains(@class, 'QRCode')]",
                "//img[contains(@src, 'qr') or contains(@src, 'QR')]"
            ]
            
            for xpath in qr_xpaths:
                try:
                    element = agent.find_element_by_xpath(xpath)
                    if element and element.is_displayed():
                        agent.click_element(element)
                        logger.info(f"找到并点击了二维码按钮")
                        break
                except:
                    continue
                    
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
                try:
                    element = agent.find_element_by_xpath(xpath)
                    if element and element.is_displayed():
                        # 处理元素
                        pass
                except Exception as e:
                    logger.error(f"查找元素失败: {str(e)}")
                    # 可以在这里添加恢复机制，比如刷新页面
                    agent.load_page(agent.driver.current_url)
                    
                    if element and element.is_displayed():
                        found_headers[header_name] = True
                        logger.info(f"找到表头: {header_name}")
                    else:
                        found_headers[header_name] = False
                        logger.error(f"未找到表头: {header_name}")
            
            # 如果所有表头都找到了，开始监控
            if all(found_headers.values()):
                logger.info("所有表头都已找到！")
                
                # 开始监控订单号
                logger.info("开始监控订单号...")
                while True:
                    try:
                        # 使用更精确的XPath定位订单号链接
                        order_numbers = agent.driver.find_elements("xpath", "//a[contains(@class, 'link') and contains(@href, '/p2p/order?orderId=')]")
                        
                        if order_numbers:
                            temp_orders = []  # 创建临时数组存储订单基本信息
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
                                        '按时间排序': parent_row.find_element("xpath", ".//td[8]").text
                                    }
                                    temp_orders.append(order_data)
                                    logger.info(f"找到订单: {order_data['订单号']}")
                            
                            logger.info(f"已收集 {len(temp_orders)} 个订单的基本信息，准备获取详情...")
                            # 输出详细的订单信息到日志
                            logger.info("订单列表详细信息:")
                            for order in temp_orders:
                                logger.info("-" * 50)
                                for key, value in order.items():
                                    logger.info(f"{key}: {value}")
                            
                            # 处理订单详情
                            for order in temp_orders:
                                try:
                                    if order['订单号'] in processed_order_ids:
                                        logger.info(f"订单 {order['订单号']} 已处理过，跳过")
                                        continue
                                    
                                    # 在新窗口打开订单详情
                                    order_url = f"https://www.okx.com/zh-hans/p2p/order?orderId={order['订单号']}"
                                    main_window = agent.driver.current_window_handle
                                    
                                    # 使用更可靠的方式打开新页面
                                    try:
                                        # 记录当前窗口数量
                                        original_windows = agent.driver.window_handles
                                        
                                        # 直接使用JavaScript打开新窗口
                                        agent.driver.execute_script(f"window.open('{order_url}', '_blank');")
                                        time.sleep(3)  # 增加等待时间，确保新窗口有足够时间打开
                                        
                                        # 检查是否有新窗口打开
                                        current_windows = agent.driver.window_handles
                                        if len(current_windows) > len(original_windows):
                                            # 找到新窗口
                                            new_window = [handle for handle in current_windows if handle not in original_windows][0]
                                            agent.driver.switch_to.window(new_window)
                                            time.sleep(5)  # 增加等待时间，确保页面完全加载
                                            
                                            # 验证是否成功加载了订单详情页面
                                            if "p2p/order" in agent.driver.current_url and order['订单号'] in agent.driver.current_url:
                                                logger.info(f"成功打开订单 {order['订单号']} 详情页面")
                                            else:
                                                logger.warning(f"页面已打开但URL不匹配: {agent.driver.current_url}")
                                                # 尝试直接导航到正确的URL
                                                agent.load_page(order_url)
                                                time.sleep(3)
                                        else:
                                            logger.error("未能打开新窗口")
                                            # 尝试在当前窗口打开订单详情
                                            logger.info("尝试在当前窗口打开订单详情...")
                                            agent.load_page(order_url)
                                            time.sleep(3)
                                    except Exception as e:
                                        logger.error(f"打开订单详情页面失败: {str(e)}")
                                        # 尝试在当前窗口打开
                                        try:
                                            logger.info("尝试在当前窗口打开订单详情...")
                                            agent.load_page(order_url)
                                            time.sleep(3)
                                        except Exception as e2:
                                            logger.error(f"在当前窗口打开也失败: {str(e2)}")
                                            continue
                                    
                                    # 获取订单详情信息
                                    try:
                                        # 使用更健壮的方式查找元素，添加等待和重试机制
                                        max_attempts = 3
                                        for attempt in range(max_attempts):
                                            try:
                                                # 获取订单状态 - 使用更灵活的XPath
                                                status_xpath = "//*[contains(text(), '待对方付款') or contains(text(), '买家已付款') or contains(text(), '等待买家付款') or contains(text(), '等待卖家放币')]"
                                                status_element = agent.find_element_by_xpath(status_xpath)
                                                order['详情页订单状态'] = status_element.text if status_element else "未知"
                                                
                                                # 获取付款人实名 - 使用多个可能的XPath
                                                name_xpaths = [
                                                    "//div[contains(text(), '付款人实名')]/following-sibling::div[1]",
                                                    "//div[contains(text(), '付款人实名')]/../following-sibling::div[1]",
                                                    "//*[contains(text(), '付款人实名')]/following-sibling::*[1]",
                                                    "//span[contains(text(), '付款人实名')]/following-sibling::span[1]"
                                                ]
                                                name_element = None
                                                for xpath in name_xpaths:
                                                    try:
                                                        name_element = agent.find_element_by_xpath(xpath)
                                                        if name_element and name_element.is_displayed():
                                                            break
                                                    except:
                                                        continue
                                                order['付款人实名'] = name_element.text if name_element else "未知"
                                                
                                                # 获取收款方式 - 使用多个可能的XPath
                                                payment_xpaths = [
                                                    "//div[contains(text(), '支付方式')]/following-sibling::div[1]",
                                                    "//div[contains(text(), '支付方式')]/../following-sibling::div[1]",
                                                    "//*[contains(text(), '支付宝') or contains(text(), '微信') or contains(text(), '银行卡')]"
                                                ]
                                                payment_element = None
                                                for xpath in payment_xpaths:
                                                    try:
                                                        payment_element = agent.find_element_by_xpath(xpath)
                                                        if payment_element and payment_element.is_displayed():
                                                            break
                                                    except:
                                                        continue
                                                order['收款方式'] = payment_element.text if payment_element else "未知"
                                                
                                                break  # 如果成功找到元素，跳出重试循环
                                            except Exception as e:
                                                if attempt < max_attempts - 1:
                                                    logger.warning(f"尝试 {attempt+1}/{max_attempts} 获取订单详情失败，重试中...")
                                                    time.sleep(2)
                                                else:
                                                    raise  # 最后一次尝试失败，抛出异常
                                        
                                        logger.info(f"订单 {order['订单号']} 详情信息:")
                                        logger.info(f"详情页订单状态: {order['详情页订单状态']}")
                                        logger.info(f"付款人实名: {order['付款人实名']}")
                                        logger.info(f"收款方式: {order['收款方式']}")
                                        if '交易金额' in order:
                                            logger.info(f"交易金额: {order['交易金额']}")
                                        if '交易数量' in order:
                                            logger.info(f"交易数量: {order['交易数量']}")
                                        
                                    except Exception as e:
                                        logger.error(f"读取订单详情数据失败: {str(e)}")
                                    
                                    # 不关闭详情页面，只添加到已处理集合
                                    processed_order_ids.add(order['订单号'])
                                    
                                    # 切换回主窗口继续处理其他订单
                                    try:
                                        agent.driver.switch_to.window(main_window)
                                    except Exception as e:
                                        logger.error(f"切换回主窗口失败: {str(e)}")
                                        # 尝试恢复会话
                                        try:
                                            # 如果会话无效，尝试重新加载页面
                                            agent.load_page("https://www.okx.com/zh-hans/p2p/dashboard")
                                            time.sleep(3)
                                            agent.load_page("https://www.okx.com/zh-hans/p2p/orders")
                                            time.sleep(3)
                                            break  # 跳出订单处理循环，重新开始监控
                                        except:
                                            logger.error("无法恢复会话，退出监控")
                                            return  # 退出函数
                                    
                                    # 添加到已处理集合
                                    processed_order_ids.add(order['订单号'])
                                    
                                except Exception as e:
                                    logger.error(f"处理订单 {order['订单号']} 详情时出错: {str(e)}")
                                    try:
                                        agent.driver.switch_to.window(main_window)
                                    except:
                                        pass
                                    continue
                            
                            # 保存到orders.xlsx
                            if temp_orders:
                                try:
                                    orders_df = pd.DataFrame(temp_orders)
                                    orders_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'orders.xlsx')
                                    
                                    if os.path.exists(orders_path):
                                        existing_df = pd.read_excel(orders_path)
                                        orders_df = pd.concat([existing_df, orders_df], ignore_index=True)
                                        orders_df.drop_duplicates(subset=['订单号'], keep='first', inplace=True)
                                    
                                    orders_df.to_excel(orders_path, index=False)
                                    logger.info(f"已保存 {len(temp_orders)} 个订单到Excel")
                                except Exception as e:
                                    logger.error(f"保存数据失败: {str(e)}")
                            
                        time.sleep(10)
                        
                    except KeyboardInterrupt:
                        logger.info("监控被用户中断")
                        break
                    except Exception as e:
                        logger.error(f"监控过程出错: {str(e)}")
                        time.sleep(5)
                
                # 保持程序运行
                input("按回车键退出...")
                
            else:
                logger.warning("未找到所有必要的表头，无法开始监控")
        
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")
    finally:
        if 'agent' in locals() and agent:
            agent.close()

if __name__ == "__main__":
    main()