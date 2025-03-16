import pandas as pd
import os

def fix_orders_excel():
    """修复orders.xlsx文件：重命名列并去除重复数据"""
    orders_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'orders.xlsx')
    
    if os.path.exists(orders_path):
        try:
            # 读取现有Excel
            df = pd.read_excel(orders_path)
            
            # 记录原始行数
            original_rows = len(df)
            
            # 重命名列
            if '时间' in df.columns and '按时间排序' not in df.columns:
                df = df.rename(columns={'时间': '按时间排序'})
            
            # 去重
            df = df.drop_duplicates(subset=['订单号'], keep='first')
            
            # 保存回Excel
            df.to_excel(orders_path, index=False)
            
            print(f"修复完成！原始记录数: {original_rows}, 去重后记录数: {len(df)}")
            return True
        except Exception as e:
            print(f"修复失败: {str(e)}")
            return False
    else:
        print(f"文件不存在: {orders_path}")
        return False

def optimize_order_processing():
    """为main.py提供的优化建议函数，在读取订单时就进行去重"""
    # 这个函数展示了如何在main.py中优化订单处理逻辑
    
    # 示例代码：
    # 1. 使用集合存储已处理的订单号
    processed_order_ids = set()
    
    # 2. 在处理新订单前检查是否已存在
    def process_new_orders(order_links):
        found_orders = []
        
        for order_link in order_links:
            order_number = order_link.text.strip()
            
            # 如果订单号已经处理过，跳过
            if order_number in processed_order_ids:
                print(f"订单 {order_number} 已处理过，跳过")
                continue
                
            # 处理新订单...
            order_data = {
                '订单号': order_number,
                # 其他数据...
            }
            
            # 添加到结果列表
            found_orders.append(order_data)
            
            # 添加到已处理集合
            processed_order_ids.add(order_number)
            
        return found_orders
    
    print("优化建议函数已加载，请在main.py中实现类似逻辑")

if __name__ == "__main__":
    fix_orders_excel()
    # optimize_order_processing()  # 这只是建议，不需要在这里运行