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
                                    # 修改逻辑：不再跳过已处理订单，而是标记它们
                                    is_processed = order['订单号'] in processed_order_ids
                                    if is_processed:
                                        logger.info(f"订单 {order['订单号']} 已处理过，但仍将打开详情页面进行监控")
                                    
                                    # 在新窗口打开订单详情
                                    order_url = f"https://www.okx.com/zh-hans/p2p/order?orderId={order['订单号']}"
                                    main_window = agent.driver.current_window_handle
                                    
                                    # 使用更可靠的方式打开新页面
                                    try:
                                        # 记录当前窗口数量
                                        original_windows = agent.driver.window_handles
                                        
                                        # 直接使用JavaScript打开新窗口
                                        agent.driver.execute_script(f"window.open('{order_url}', '_blank');")
                                        time.sleep(5)  # 增加等待时间，确保新窗口有足够时间打开
                                        
                                        # 检查是否有新窗口打开
                                        current_windows = agent.driver.window_handles
                                        if len(current_windows) > len(original_windows):
                                            # 找到新窗口
                                            new_window = [handle for handle in current_windows if handle not in original_windows][0]
                                            agent.driver.switch_to.window(new_window)
                                            time.sleep(8)  # 增加等待时间，确保页面完全加载
                                            
                                            # 验证是否成功加载了订单详情页面
                                            if "p2p/order" in agent.driver.current_url and order['订单号'] in agent.driver.current_url:
                                                logger.info(f"成功打开订单 {order['订单号']} 详情页面")
                                            else:
                                                logger.warning(f"页面已打开但URL不匹配: {agent.driver.current_url}")
                                                # 尝试直接导航到正确的URL
                                                agent.load_page(order_url)
                                                time.sleep(5)  # 增加等待时间
                                                
                                                # 再次验证URL
                                                if "p2p/order" in agent.driver.current_url and order['订单号'] in agent.driver.current_url:
                                                    logger.info(f"成功重定向到订单 {order['订单号']} 详情页面")
                                                else:
                                                    logger.error(f"无法加载订单详情页面，当前URL: {agent.driver.current_url}")
                                                    # 尝试点击页面上的订单号链接
                                                    try:
                                                        order_link = agent.find_element_by_xpath(f"//a[contains(text(), '{order['订单号']}')]")
                                                        if order_link:
                                                            agent.click_element(order_link)
                                                            time.sleep(5)
                                                            logger.info("尝试通过点击订单号链接打开详情页")
                                                    except:
                                                        logger.error("找不到订单号链接")
                                        else:
                                            logger.error("未能打开新窗口")
                                            # 尝试在当前窗口打开订单详情
                                            logger.info("尝试在当前窗口打开订单详情...")
                                            agent.load_page(order_url)
                                            time.sleep(5)  # 增加等待时间
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
                                                
                                                # 先获取订单详情页面中的总金额和付款人实名
                                                # 获取总金额 - 使用多个可能的XPath
                                                amount_xpaths = [
                                                    "//div[contains(text(), '总金额')]/following-sibling::div[1]",
                                                    "//div[contains(text(), '总金额')]/../following-sibling::div[1]",
                                                    "//*[contains(text(), '总金额')]/following-sibling::*[1]",
                                                    "//span[contains(text(), '总金额')]/following-sibling::span[1]",
                                                    "//*[contains(@class, 'amount') and contains(text(), 'CNY')]"
                                                ]
                                                detail_amount_element = None
                                                for xpath in amount_xpaths:
                                                    try:
                                                        detail_amount_element = agent.find_element_by_xpath(xpath)
                                                        if detail_amount_element and detail_amount_element.is_displayed():
                                                            break
                                                    except:
                                                        continue
                                                
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
                                                
                                                # 保存详情页面获取的信息到order字典中
                                                detail_amount = detail_amount_element.text if detail_amount_element else None
                                                order['详情页总金额'] = detail_amount
                                                order['付款人实名'] = name_element.text if name_element else "未知"
                                                
                                                logger.info(f"从详情页获取的总金额: {detail_amount}")
                                                logger.info(f"从详情页获取的付款人实名: {order['付款人实名']}")
                                                
                                                # 如果订单状态是"买家已付款"，则打开支付宝页面
                                                if status_element and "买家已付款" in status_element.text:
                                                    logger.info("检测到买家已付款状态，准备打开支付宝交易记录页面...")
                                                    
                                                    # 保存当前窗口句柄
                                                    current_window = agent.driver.current_window_handle
                                                    
                                                    # 在新窗口中打开支付宝交易记录页面
                                                    try:
                                                        # 记录当前窗口数量
                                                        original_windows = agent.driver.window_handles
                                                        
                                                        # 使用JavaScript打开支付宝交易记录页面
                                                        agent.driver.execute_script("window.open('https://consumeprod.alipay.com/record/advanced.htm', '_blank');")
                                                        time.sleep(3)  # 等待新窗口打开
                                                        
                                                        # 检查是否有新窗口打开
                                                        current_windows = agent.driver.window_handles
                                                        if len(current_windows) > len(original_windows):
                                                            # 找到新窗口
                                                            alipay_window = [handle for handle in current_windows if handle not in original_windows][0]
                                                            agent.driver.switch_to.window(alipay_window)
                                                            time.sleep(5)  # 等待页面加载
                                                            
                                                            logger.info("已打开支付宝交易记录页面，开始监控付款记录...")
                                                            
                                                            # 使用详情页获取的总金额，处理格式
                                                            if detail_amount:
                                                                # 提取数字部分，去除"CNY"和其他非数字字符
                                                                import re
                                                                amount_matches = re.findall(r'([0-9,.]+)', detail_amount)
                                                                if amount_matches:
                                                                    order_amount = amount_matches[0].replace(',', '').strip()
                                                                else:
                                                                    # 如果无法从详情页提取，回退到列表页的总金额
                                                                    order_amount = order['总金额'].replace('¥', '').replace(',', '').strip()
                                                            else:
                                                                # 如果详情页没有获取到总金额，使用列表页的总金额
                                                                order_amount = order['总金额'].replace('¥', '').replace(',', '').strip()
                                                            
                                                            # 直接使用已保存的付款人实名
                                                            payer_name = order['付款人实名']
                                                            
                                                            logger.info(f"将使用以下信息匹配支付宝交易记录:")
                                                            logger.info(f"金额: {order_amount}")
                                                            logger.info(f"付款人: {payer_name}")
                                                            
                                                            # 检查是否需要登录支付宝
                                                            if "登录" in agent.driver.title or "login" in agent.driver.current_url.lower():
                                                                logger.info("检测到支付宝需要登录，请扫码登录...")
                                                                # 等待用户扫码登录，最多等待30秒
                                                                for _ in range(30):
                                                                    if "登录" not in agent.driver.title and "login" not in agent.driver.current_url.lower():
                                                                        logger.info("支付宝登录成功")
                                                                        break
                                                                    time.sleep(1)
                                                            
                                                            # 尝试在交易记录中查找匹配的付款
                                                            max_search_attempts = 18  # 增加尝试次数以适应更长的监控时间
                                                            found_payment = False
                                                            search_start_time = time.time()
                                                            search_timeout = 90  # 设置90秒超时
                                                            
                                                            logger.info(f"开始持续监控支付宝交易记录，将持续约90秒...")
                                                            logger.info(f"正在查找金额为 {order_amount} 的交易记录")
                                                            
                                                            # 转换订单金额为浮点数，便于比较
                                                            try:
                                                                order_amount_float = float(order_amount)
                                                                logger.info(f"订单金额转换为数字: {order_amount_float}")
                                                            except:
                                                                order_amount_float = None
                                                                logger.warning(f"订单金额 {order_amount} 无法转换为数字，将使用字符串匹配")
                                                            
                                                            while time.time() - search_start_time < search_timeout and not found_payment:
                                                                try:
                                                                    # 查找交易记录表格 - 使用更精确的选择器
                                                                    transaction_rows = []
                                                                    selectors = [
                                                                        "//tbody//tr[contains(@class, 'J-item')]",  # 最精确的选择器
                                                                        "//tr[contains(@class, 'J-item')]",
                                                                        "//tr[contains(@id, 'J-item')]",
                                                                        "//table//tbody//tr",  # 备用选择器
                                                                        "//div[contains(@class, 'record')]//tr"
                                                                    ]
                                                                    
                                                                    for selector in selectors:
                                                                        try:
                                                                            rows = agent.driver.find_elements("xpath", selector)
                                                                            if rows:
                                                                                transaction_rows = rows
                                                                                logger.info(f"使用选择器 '{selector}' 找到 {len(rows)} 条交易记录")
                                                                                break
                                                                        except:
                                                                            continue
                                                                    
                                                                    if transaction_rows:
                                                                        logger.info(f"找到 {len(transaction_rows)} 条交易记录，开始匹配...")
                                                                        
                                                                        # 记录每条交易记录的详细信息，方便调试
                                                                        record_count = 0
                                                                        for row in transaction_rows:
                                                                            record_count += 1
                                                                            try:
                                                                                # 获取整行文本用于日志记录
                                                                                row_text = row.text
                                                                                logger.info(f"交易记录 #{record_count}: {row_text[:100]}...")
                                                                                
                                                                                # 获取交易金额 - 尝试多种可能的选择器
                                                                                amount_selectors = [
                                                                                    ".//td[contains(@class, 'amount')]//span[contains(@class, 'amount-pay')]",
                                                                                    ".//span[contains(@class, 'amount-pay')]",
                                                                                    ".//td[contains(@class, 'amount')]",
                                                                                    ".//div[contains(@class, 'amount')]",
                                                                                    ".//*[contains(text(), '¥')]",
                                                                                    ".//td[contains(text(), '¥')]",
                                                                                    ".//span[contains(text(), '¥')]"
                                                                                ]
                                                                                
                                                                                transaction_amount = None
                                                                                used_selector = None
                                                                                for selector in amount_selectors:
                                                                                    try:
                                                                                        elements = row.find_elements("xpath", selector)
                                                                                        if elements:
                                                                                            for element in elements:
                                                                                                text = element.text
                                                                                                if text and ('¥' in text or text.strip().replace(',', '').replace('.', '').replace('+', '').replace('-', '').isdigit()):
                                                                                                    # 移除+号、¥符号和逗号
                                                                                                    transaction_amount = text.replace('¥', '').replace(',', '').replace('+', '').strip()
                                                                                                    used_selector = selector
                                                                                                    break
                                                                                        if transaction_amount:
                                                                                            break
                                                                                    except:
                                                                                        continue
                                                                                
                                                                                # 如果找不到金额，尝试获取整行文本并提取数字
                                                                                if not transaction_amount:
                                                                                    try:
                                                                                        # 直接尝试查找amount-pay类的元素
                                                                                        amount_pay_elements = row.find_elements("css selector", ".amount-pay")
                                                                                        if amount_pay_elements:
                                                                                            for element in amount_pay_elements:
                                                                                                text = element.text
                                                                                                if text:
                                                                                                    # 移除+号和其他非数字字符，保留数字和小数点
                                                                                                    import re
                                                                                                    amount_digits = re.findall(r'(\d+\.\d+|\d+)', text)
                                                                                                    if amount_digits:
                                                                                                        transaction_amount = amount_digits[0].strip()
                                                                                                        used_selector = "直接CSS选择器 .amount-pay"
                                                                                                        logger.info(f"使用CSS选择器直接找到金额: {text} -> {transaction_amount}")
                                                                                                        break
                                                                                    except Exception as e:
                                                                                        logger.error(f"使用CSS选择器查找金额时出错: {str(e)}")
                                                                                
                                                                                # 如果上述方法都失败，再尝试使用正则表达式，但更精确地匹配金额格式
                                                                                if not transaction_amount:
                                                                                    try:
                                                                                        # 使用更精确的正则表达式查找金额模式（匹配¥或+后跟数字和小数点的格式）
                                                                                        import re
                                                                                        # 匹配类似 "¥123.45" 或 "+123.45" 或 "123.45元" 的模式
                                                                                        amount_matches = re.findall(r'[¥\+]?\s*(\d+(?:\.\d+)?)\s*(?:元|CNY)?', row_text)
                                                                                        if amount_matches:
                                                                                            transaction_amount = amount_matches[0].strip()
                                                                                            used_selector = "改进的正则表达式"
                                                                                            logger.info(f"使用改进的正则表达式找到金额: {amount_matches[0]}")
                                                                                    except Exception as e:
                                                                                        logger.error(f"使用正则表达式查找金额时出错: {str(e)}")
                                                                                
                                                                                if not transaction_amount:
                                                                                    logger.warning(f"交易记录 #{record_count}: 无法提取金额")
                                                                                    continue
                                                                                
                                                                                logger.info(f"交易记录 #{record_count}: 找到金额 {transaction_amount} (使用选择器: {used_selector})")
                                                                                
                                                                                # 获取交易对方 - 尝试多种可能的选择器
                                                                                counterparty = None
                                                                                counterparty_selectors = [
                                                                                    ".//p[contains(@class, 'name')]",
                                                                                    ".//div[contains(@class, 'name')]",
                                                                                    ".//span[contains(@class, 'name')]",
                                                                                    ".//td[position()=1]",  # 第一列通常是交易对方
                                                                                    ".//*[contains(@class, 'merchant') or contains(@class, 'user')]"
                                                                                ]
                                                                                
                                                                                for selector in counterparty_selectors:
                                                                                    try:
                                                                                        elements = row.find_elements("xpath", selector)
                                                                                        if elements:
                                                                                            for element in elements:
                                                                                                if element.text and len(element.text.strip()) > 0:
                                                                                                    counterparty = element.text.strip()
                                                                                                    break
                                                                                        if counterparty:
                                                                                            break
                                                                                    except:
                                                                                        continue
                                                                                
                                                                                # 如果找不到交易对方，使用整行文本
                                                                                if not counterparty:
                                                                                    counterparty = row.text
                                                                                
                                                                                # 检查金额是否匹配 - 使用更灵活的匹配方式
                                                                                amount_match = False
                                                                                
                                                                                # 1. 精确字符串匹配
                                                                                if transaction_amount == order_amount:
                                                                                    amount_match = True
                                                                                    logger.info("金额精确匹配成功")
                                                                                # 2. 数值比较（允许小数点差异）
                                                                                elif order_amount_float is not None:
                                                                                    try:
                                                                                        transaction_amount_float = float(transaction_amount)
                                                                                        # 允许0.01的误差
                                                                                        if abs(transaction_amount_float - order_amount_float) < 0.01:
                                                                                            amount_match = True
                                                                                            logger.info(f"金额数值匹配成功: {transaction_amount_float} ≈ {order_amount_float}")
                                                                                    except:
                                                                                        pass
                                                                                # 3. 包含关系检查
                                                                                elif order_amount in transaction_amount or transaction_amount in order_amount:
                                                                                    amount_match = True
                                                                                    logger.info(f"金额部分匹配成功: '{transaction_amount}' 与 '{order_amount}'")
                                                                                
                                                                                # 检查付款人是否匹配
                                                                                name_match = True  # 默认为True，如果没有付款人信息
                                                                                if payer_name and counterparty:
                                                                                    # 更灵活的名称匹配
                                                                                    name_match = (
                                                                                        payer_name in counterparty or 
                                                                                        counterparty in payer_name or
                                                                                        any(part in counterparty for part in payer_name.split()) or
                                                                                        any(part in payer_name for part in counterparty.split())
                                                                                    )
                                                                                
                                                                                if amount_match and name_match:
                                                                                    logger.info(f"找到匹配的付款记录！金额: {transaction_amount}, 付款方: {counterparty}")
                                                                                    found_payment = True
                                                                                    break
                                                                                elif amount_match:
                                                                                    logger.warning(f"金额匹配但付款方不匹配。金额: {transaction_amount}, 付款方: {counterparty}, 期望付款方: {payer_name}")
                                                                                
                                                                            except Exception as e:
                                                                                logger.error(f"解析交易记录行时出错: {str(e)}")
                                                                                continue
                                                                    else:
                                                                        logger.warning("未找到交易记录，刷新页面重试...")
                                                                    
                                                                    if found_payment:
                                                                        break
                                                                    
                                                                    # 计算剩余监控时间
                                                                    remaining_time = search_timeout - (time.time() - search_start_time)
                                                                    logger.info(f"未找到匹配付款记录，将继续监控约 {int(remaining_time)} 秒...")
                                                                    
                                                                    # 刷新页面并等待
                                                                    agent.driver.refresh()
                                                                    time.sleep(5)  # 每5秒刷新一次
                                                                    
                                                                except Exception as e:
                                                                    logger.error(f"搜索交易记录时出错: {str(e)}")
                                                                    # 刷新页面并继续
                                                                    try:
                                                                        agent.driver.refresh()
                                                                        time.sleep(5)
                                                                    except:
                                                                        logger.error("刷新页面失败")
                                                            
                                                            # 记录搜索结果
                                                            search_duration = time.time() - search_start_time
                                                            if found_payment:
                                                                order['支付宝确认'] = "已确认"
                                                                logger.info(f"已在支付宝确认付款记录，用时 {search_duration:.1f} 秒")
                                                            else:
                                                                order['支付宝确认'] = "未确认"
                                                                logger.warning(f"监控结束，未在支付宝找到匹配的付款记录，监控时长 {search_duration:.1f} 秒")
                                                            
                                                            # 切回订单详情页面继续处理
                                                            agent.driver.switch_to.window(current_window)
                                                            logger.info("已切回订单详情页面")
                                                        else:
                                                            logger.error("未能打开支付宝交易记录窗口")
                                                    except Exception as e:
                                                        logger.error(f"打开支付宝交易记录页面失败: {str(e)}")
                                                        # 确保切回订单详情页面
                                                        try:
                                                            agent.driver.switch_to.window(current_window)
                                                        except:
                                                            logger.error("切回订单详情页面失败")
                                                
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