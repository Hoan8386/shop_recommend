import os
import shutil
import sys
from datetime import datetime

print("Bắt đầu quá trình dọn dẹp dự án...")

# Định nghĩa thư mục gốc dự án
base_dir = os.path.dirname(os.path.abspath(__file__))

# Danh sách các file cần giữ lại
essential_files = [
    'OnlineRetail.xlsx',  # File dữ liệu gốc
    'data_analysis.py',   # Script phân tích dữ liệu
    'api.py',             # API Flask
    'db_connection.py',   # Kết nối CSDL
    'db_connection_sqlite.py', # Phiên bản SQLite (backup)
    'index.html',         # Giao diện dashboard
    'shop.html',          # Giao diện cửa hàng
    'shop.js',            # JavaScript cho cửa hàng
    'api_documentation.md',  # Tài liệu API
    'clean_files.py',     # Script hiện tại
]

# Danh sách các file hình ảnh và kết quả phân tích cần giữ lại
essential_images = [
    'monthly_revenue.png',
    'top_products.png',
    'correlation_heatmap.png',
    'purchase_frequency.png',
]

# Danh sách các file sẽ bị xóa
files_to_remove = [
    # File dữ liệu trung gian
    'cleaned_retail_data.csv',
    'frequent_itemsets.csv',
    'association_rules.csv',
    'retail_analysis_results.xlsx',
    'import_to_sqlserver.py',  # Script cũ yêu cầu pandas
]

# Tạo thư mục backup nếu cần
def create_backup():
    """Tạo thư mục backup cho các file trước khi xóa"""
    backup_dir = os.path.join(base_dir, f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Backup các file sẽ bị xóa
    for file in files_to_remove:
        file_path = os.path.join(base_dir, file)
        if os.path.exists(file_path):
            try:
                shutil.copy2(file_path, os.path.join(backup_dir, file))
                print(f"Đã sao lưu {file} vào thư mục backup")
            except Exception as e:
                print(f"Không thể sao lưu {file}: {str(e)}")
    
    return backup_dir

# Xóa các file không cần thiết
def clean_project(backup_first=True):
    """Xóa các file không cần thiết"""
    if backup_first:
        backup_dir = create_backup()
        print(f"Đã tạo bản sao lưu tại: {backup_dir}")
    
    total_removed = 0
    total_size = 0
    
    for file in files_to_remove:
        file_path = os.path.join(base_dir, file)
        if os.path.exists(file_path):
            try:
                file_size = os.path.getsize(file_path)
                total_size += file_size
                os.remove(file_path)
                total_removed += 1
                print(f"Đã xóa {file} ({file_size/1024/1024:.2f} MB)")
            except Exception as e:
                print(f"Không thể xóa {file}: {str(e)}")
    
    print(f"\nĐã xóa tổng cộng {total_removed} file ({total_size/1024/1024:.2f} MB)")
    print("Dự án đã được dọn dẹp và tối ưu hóa.")

# Chạy chức năng dọn dẹp
if __name__ == "__main__":
    user_choice = input("Bạn có muốn tạo bản sao lưu trước khi xóa? (y/n): ").strip().lower()
    backup_first = user_choice.startswith('y')
    
    if not backup_first:
        confirm = input("Bạn chắc chắn muốn xóa các file mà không sao lưu? (y/n): ").strip().lower()
        if not confirm.startswith('y'):
            print("Hủy bỏ quá trình xóa.")
            sys.exit(0)
    
    print("Bắt đầu quá trình dọn dẹp...")
    clean_project(backup_first)
    
    # Thông báo các tệp đã được giữ lại
    print("\nCác tệp quan trọng được giữ lại:")
    for file in essential_files + essential_images:
        file_path = os.path.join(base_dir, file)
        if os.path.exists(file_path):
            print(f"  - {file}")
    
    print("\nDự án đã sẵn sàng để sử dụng.")