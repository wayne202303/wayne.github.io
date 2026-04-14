import os
import xlrd

# 检查文件
file_path = 'wenzhang.xls'

if not os.path.exists(file_path):
    print(f"文件 {file_path} 不存在")
    exit(1)

print(f"文件大小: {os.path.getsize(file_path)} 字节")

# 尝试使用 xlrd 读取
try:
    print("尝试使用 xlrd 读取...")
    workbook = xlrd.open_workbook(file_path)
    print(f"成功打开工作簿")
    print(f"工作表数量: {workbook.nsheets}")
    
    for i in range(workbook.nsheets):
        sheet = workbook.sheet_by_index(i)
        print(f"工作表 {i+1}: {sheet.name}")
        print(f"行数: {sheet.nrows}, 列数: {sheet.ncols}")
        
        # 打印前几行
        if sheet.nrows > 0:
            print("前 5 行数据:")
            for row_idx in range(min(5, sheet.nrows)):
                row = sheet.row_values(row_idx)
                print(f"行 {row_idx+1}: {row}")
    
    print("读取成功！")
    
except Exception as e:
    print(f"读取失败: {str(e)}")
