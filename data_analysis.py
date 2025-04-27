import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from mlxtend.frequent_patterns import apriori, association_rules
import numpy as np

print("Bắt đầu chạy script phân tích dữ liệu...")

# Định nghĩa thư mục làm việc
base_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_dir, 'OnlineRetail.xlsx')

if not os.path.exists(file_path):
    print(f"Lỗi: File {file_path} không tồn tại.")
    exit()

# Load dataset
print("Đang tải file OnlineRetail.xlsx...")
try:
    df = pd.read_excel(file_path)
    print(f"Tải dữ liệu thành công. Kích thước: {df.shape}")
except Exception as e:
    print(f"Lỗi khi đọc file: {e}")
    exit()

# Làm sạch dữ liệu
print("Đang làm sạch dữ liệu...")
df = df.dropna(subset=['CustomerID', 'Description'])
df = df[~df['InvoiceNo'].astype(str).str.startswith('C')]
df = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0)]
df['CustomerID'] = df['CustomerID'].astype(int)
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
df['TotalPrice'] = df['Quantity'] * df['UnitPrice']

# Thống kê mô tả chi tiết
print("\n=== THỐNG KÊ MÔ TẢ ===")
print(f"Tổng số giao dịch: {df['InvoiceNo'].nunique()}")
print(f"Tổng số sản phẩm: {df['StockCode'].nunique()}")
print(f"Tổng số khách hàng: {df['CustomerID'].nunique()}")
print(f"Tổng doanh thu: {df['TotalPrice'].sum():,.2f}")

# Phân tích theo thời gian
df['Month'] = df['InvoiceDate'].dt.month
df['Year'] = df['InvoiceDate'].dt.year
monthly_stats = df.groupby(['Year', 'Month']).agg({
    'InvoiceNo': 'nunique',
    'TotalPrice': 'sum',
    'Quantity': 'sum'
}).reset_index()

# Vẽ biểu đồ doanh thu theo tháng
plt.figure(figsize=(12, 6))
sns.lineplot(data=monthly_stats, x='Month', y='TotalPrice', hue='Year')
plt.title('Doanh thu theo tháng')
plt.xlabel('Tháng')
plt.ylabel('Doanh thu')
plt.savefig(os.path.join(base_dir, 'monthly_revenue.png'))

# Phân tích hành vi mua sắm
customer_stats = df.groupby('CustomerID').agg({
    'InvoiceNo': 'nunique',
    'TotalPrice': 'sum',
    'Quantity': 'sum'
}).reset_index()

# Vẽ biểu đồ phân bố số lần mua hàng
plt.figure(figsize=(10, 6))
sns.histplot(customer_stats['InvoiceNo'], bins=50, kde=True)
plt.title('Phân bố số lần mua hàng của khách')
plt.xlabel('Số lần mua')
plt.ylabel('Số lượng khách hàng')
plt.savefig(os.path.join(base_dir, 'purchase_frequency.png'))

# Phân tích sản phẩm
product_stats = df.groupby('Description').agg({
    'Quantity': 'sum',
    'TotalPrice': 'sum',
    'InvoiceNo': 'nunique'
}).reset_index()

# Vẽ biểu đồ top 10 sản phẩm bán chạy
plt.figure(figsize=(12, 6))
top_products = product_stats.nlargest(10, 'Quantity')
sns.barplot(data=top_products, x='Description', y='Quantity')
plt.title('Top 10 sản phẩm bán chạy nhất')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(os.path.join(base_dir, 'top_products.png'))

# Phân tích tương quan
correlation = df[['Quantity', 'UnitPrice', 'TotalPrice']].corr()
plt.figure(figsize=(8, 6))
sns.heatmap(correlation, annot=True, cmap='coolwarm')
plt.title('Tương quan giữa các biến')
plt.savefig(os.path.join(base_dir, 'correlation_heatmap.png'))

# Khai thác tập phổ biến
print("\n=== PHÂN TÍCH TẬP PHỔ BIẾN ===")
top_products_index = df['Description'].value_counts().head(100).index
df_filtered = df[df['Description'].isin(top_products_index)]
basket = df_filtered.groupby(['InvoiceNo', 'Description'])['Quantity'].sum().unstack().fillna(0)
basket = (basket > 0).astype(int)

# Tìm tập phổ biến
frequent_itemsets = apriori(basket, min_support=0.02, use_colnames=True)
print("\nCác tập phổ biến:")
print(frequent_itemsets.head())

# Tìm luật kết hợp
rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1)
rules = rules.sort_values('lift', ascending=False)
print("\nTop 5 luật kết hợp:")
print(rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']].head())

# Lưu kết quả
df.to_csv(os.path.join(base_dir, 'cleaned_retail_data.csv'), index=False)
print("\nĐã lưu cleaned_retail_data.csv")

# Lưu tập phổ biến vào file CSV riêng
frequent_itemsets.to_csv(os.path.join(base_dir, 'frequent_itemsets.csv'), index=False)
print("Đã lưu frequent_itemsets.csv")

# Lưu luật kết hợp vào file CSV riêng
rules_csv = rules.copy()
rules_csv['antecedents'] = rules_csv['antecedents'].apply(lambda x: ', '.join(list(x)))
rules_csv['consequents'] = rules_csv['consequents'].apply(lambda x: ', '.join(list(x)))
rules_csv.to_csv(os.path.join(base_dir, 'association_rules.csv'), index=False)
print("Đã lưu association_rules.csv")

# Xuất dữ liệu ra file Excel
print("Đang xuất dữ liệu ra file Excel...")
excel_path = os.path.join(base_dir, 'retail_analysis_results.xlsx')

# Tạo ExcelWriter để viết nhiều bảng vào các sheet khác nhau
with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
    # Lưu dữ liệu đã làm sạch
    df.to_excel(writer, sheet_name='Cleaned_Data', index=False)
    
    # Lưu thống kê theo tháng
    monthly_stats.to_excel(writer, sheet_name='Monthly_Stats', index=False)
    
    # Lưu thống kê khách hàng
    customer_stats.to_excel(writer, sheet_name='Customer_Stats', index=False)
    
    # Lưu thống kê sản phẩm
    product_stats.to_excel(writer, sheet_name='Product_Stats', index=False)
    
    # Lưu top 10 sản phẩm bán chạy
    top_products.to_excel(writer, sheet_name='Top_Products', index=False)
    
    # Lưu ma trận tương quan
    correlation.to_excel(writer, sheet_name='Correlation', index=True)
    
    # Lưu tập phổ biến
    frequent_itemsets.to_excel(writer, sheet_name='Frequent_Itemsets', index=False)
    
    # Lưu luật kết hợp (top 100)
    if len(rules) > 100:
        top_rules = rules.head(100)
    else:
        top_rules = rules
        
    # Chuyển đổi các cột chứa frozenset thành chuỗi để lưu vào Excel
    top_rules_excel = top_rules.copy()
    top_rules_excel['antecedents'] = top_rules_excel['antecedents'].apply(lambda x: ', '.join(list(x)))
    top_rules_excel['consequents'] = top_rules_excel['consequents'].apply(lambda x: ', '.join(list(x)))
    top_rules_excel.to_excel(writer, sheet_name='Association_Rules', index=False)
    
    # Tạo sheet tổng quan
    summary_data = {
        'Metric': ['Tổng số giao dịch', 'Tổng số sản phẩm', 'Tổng số khách hàng', 'Tổng doanh thu',
                  'Giá trị trung bình', 'Số lượng trung bình'],
        'Value': [df['InvoiceNo'].nunique(), df['StockCode'].nunique(), df['CustomerID'].nunique(),
                 df['TotalPrice'].sum(), df['TotalPrice'].mean(), df['Quantity'].mean()]
    }
    pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)

print(f"Đã xuất dữ liệu thành công vào file {excel_path}")

print("\nHoàn thành phân tích dữ liệu!")
