import re
import os

def fix_indentation(file_path):
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份原文件
    backup_path = file_path + '.bak'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"已备份原文件到 {backup_path}")
    
    # 修复特定格式问题
    # 1. 修复分行的字符串拼接
    content = re.sub(r'f"https://www\.okx\.com/zh-hans/p2p/order\?orderId={\s+order\[\'订单号\'\]}"', 
                     r'f"https://www.okx.com/zh-hans/p2p/order?orderId={order[\'订单号\']}"', content)
    
    # 2. 修复分行的列表定义
    content = re.sub(r'\[\s+handle for handle', r'[handle for handle', content)
    
    # 3. 修复错误的缩进
    lines = content.split('\n')
    fixed_lines = []
    
    # 标准缩进为4个空格
    standard_indent = 4
    
    for i, line in enumerate(lines):
        # 跳过空行
        if not line.strip():
            fixed_lines.append('')
            continue
        
        # 计算当前行的缩进级别
        leading_spaces = len(line) - len(line.lstrip())
        
        # 特殊处理第316行附近的问题
        if "detail_amount =" in line or "order[" in line or "logger.info" in line:
            # 确保这些行有一致的缩进
            if i > 0 and "# 保存详情页面获取的信息到order字典中" in lines[i-5:i]:
                # 使用与前面代码块相同的缩进级别
                indent_level = 32
                fixed_line = ' ' * indent_level + line.lstrip()
                fixed_lines.append(fixed_line)
                continue
        
        # 处理其他行
        if leading_spaces > 100:  # 过度缩进的行
            # 尝试根据上下文确定合适的缩进
            if i > 0 and i < len(lines) - 1:
                prev_indent = len(lines[i-1]) - len(lines[i-1].lstrip())
                next_indent = len(lines[i+1]) - len(lines[i+1].lstrip())
                
                # 使用上下文中较小的缩进
                if prev_indent < 100:
                    indent_level = prev_indent
                elif next_indent < 100:
                    indent_level = next_indent
                else:
                    # 如果上下文都有问题，使用合理的缩进
                    indent_level = 32  # 假设这是一个合理的缩进级别
            else:
                indent_level = 32  # 默认缩进
        else:
            # 保持原有缩进
            indent_level = leading_spaces
        
        fixed_line = ' ' * indent_level + line.lstrip()
        fixed_lines.append(fixed_line)
    
    # 写入修复后的内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines))
    
    print(f"已修复文件缩进: {file_path}")

if __name__ == "__main__":
    file_path = r"d:\study\IT\AI\otcAgent\OtcAgentPC\main.py"
    fix_indentation(file_path)