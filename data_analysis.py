import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from mlxtend.frequent_patterns import apriori, association_rules
import numpy as np
import pyodbc

print("Bắt đầu chạy script phân tích dữ liệu...")

# Định nghĩa thông tin kết nối SQL Server
SERVER = r'DESKTOP-C4ALSJO\SQLEXPRESS'
DATABASE = 'shopping'
USERNAME = 'sa'
PASSWORD = '123'

# Hàm kết nối đến SQL Server
def get_connection():
    try:
        conn = pyodbc.connect(
            f'DRIVER={{SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}'
        )
        return conn
    except Exception as e:
        print(f"Lỗi kết nối đến SQL Server: {str(e)}")
        return None

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

# Thêm trường thời gian
df['Month'] = df['InvoiceDate'].dt.month
df['Year'] = df['InvoiceDate'].dt.year
df['Day'] = df['InvoiceDate'].dt.day
df['DayOfWeek'] = df['InvoiceDate'].dt.dayofweek
df['Quarter'] = df['InvoiceDate'].dt.quarter

# Thêm ID cho phân trang
df.reset_index(inplace=True)
df.rename(columns={'index': 'ID'}, inplace=True)

# Thống kê mô tả chi tiết
print("\n=== THỐNG KÊ MÔ TẢ ===")
print(f"Tổng số giao dịch: {df['InvoiceNo'].nunique()}")
print(f"Tổng số sản phẩm: {df['StockCode'].nunique()}")
print(f"Tổng số khách hàng: {df['CustomerID'].nunique()}")
print(f"Tổng doanh thu: {df['TotalPrice'].sum():,.2f}")

# Phân tích theo thời gian
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
product_stats = df.groupby(['StockCode', 'Description']).agg({
    'Quantity': 'sum',
    'TotalPrice': 'sum',
    'InvoiceNo': pd.Series.nunique,
    'CustomerID': pd.Series.nunique,
    'UnitPrice': 'max'
}).reset_index()

product_stats.rename(columns={
    'Quantity': 'TotalQuantitySold',
    'TotalPrice': 'TotalRevenue',
    'InvoiceNo': 'NumberOfTransactions',
    'CustomerID': 'NumberOfCustomers',
    'UnitPrice': 'MaxUnitPrice'
}, inplace=True)

# Thêm cột ImagePath với đường dẫn đến hình ảnh tương ứng
product_stats['ImagePath'] = product_stats['Description'].apply(
    lambda x: f'imagesProduct/{x}.jpg'
)

# Kiểm tra số lượng sản phẩm
print(f"Số lượng sản phẩm trong product_stats: {len(product_stats)}")

# Vẽ biểu đồ top 10 sản phẩm bán chạy
plt.figure(figsize=(12, 6))
top_products = product_stats.nlargest(10, 'TotalQuantitySold')
sns.barplot(data=top_products, x='Description', y='TotalQuantitySold')
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

# Thiết lập chiến lược phân tích với 2500 sản phẩm phổ biến nhất
print(f"Tổng số sản phẩm trong dữ liệu: {df['Description'].nunique()}")

# Giữ ngưỡng min_support thấp để phát hiện các mối liên hệ hiếm
min_support_threshold = 0.01  # 0.1% 

# Chỉ phân tích 2500 sản phẩm phổ biến nhất
product_count = 2500  # Số lượng sản phẩm phổ biến nhất để phân tích
top_products_index = df['Description'].value_counts().head(product_count).index
df_filtered = df[df['Description'].isin(top_products_index)]

print(f"Phân tích {product_count} sản phẩm phổ biến nhất (chiếm {product_count/df['Description'].nunique():.1%})")

# Tạo dữ liệu basket với kiểu boolean để tiết kiệm bộ nhớ
print("Đang tạo dữ liệu basket...")
basket = df_filtered.groupby(['InvoiceNo', 'Description'])['Quantity'].sum().unstack().fillna(0)
basket = (basket > 0).astype(bool)

print(f"Kích thước dữ liệu phân tích: {basket.shape}")

# Tìm tập phổ biến với ngưỡng min_support thấp
print(f"Bắt đầu phân tích Apriori với min_support={min_support_threshold}...")

try:
    # Giới hạn bộ nhớ cho NumPy để tránh lỗi
    import os
    import psutil
    # Lấy kích thước bộ nhớ hiện có và giới hạn sử dụng tối đa 70% bộ nhớ khả dụng
    available_memory = psutil.virtual_memory().available
    memory_limit = int(available_memory * 0.7)
    # Giới hạn bởi đơn vị byte
    os.environ['NUMPY_MAX_MEM'] = str(memory_limit)
    
    # Sử dụng low_memory=True để giảm thiểu sử dụng bộ nhớ
    frequent_itemsets = apriori(basket, min_support=min_support_threshold, use_colnames=True, low_memory=True, max_len=3)
    print(f"\nSố lượng tập phổ biến tìm được: {len(frequent_itemsets)}")
    
    if len(frequent_itemsets) > 0:
        print("\nCác tập phổ biến đầu tiên:")
        print(frequent_itemsets.head())

        # Tạo một bản sao của frequent_itemsets để sử dụng với association_rules
        frequent_itemsets_for_rules = frequent_itemsets.copy()
        
        # Chuyển đổi frozenset thành chuỗi để lưu vào cơ sở dữ liệu
        frequent_itemsets['itemsets'] = frequent_itemsets['itemsets'].apply(lambda x: ', '.join(list(x)))
        frequent_itemsets['itemset_length'] = frequent_itemsets['itemsets'].apply(lambda x: len(x.split(', ')))

        # Tìm luật kết hợp với ngưỡng lift = 1, sử dụng bản sao chưa chuyển đổi
        print(f"Đang tìm luật kết hợp với lift >= 1.0...")
        try:
            # Sử dụng frequent_itemsets_for_rules với cột itemsets vẫn ở dạng frozenset
            rules = association_rules(frequent_itemsets_for_rules, metric="lift", min_threshold=1.0)
            
            print(f"\nTổng số luật kết hợp tìm được: {len(rules)}")
            if len(rules) > 0:
                print("\nTop 5 luật kết hợp có lift cao nhất:")
                print(rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']].head())
        except KeyError as e:
            print(f"Lỗi khi tìm luật kết hợp: {str(e)}")
            print("Thử tìm luật kết hợp với tùy chọn support_only=True...")
            
            # Thử lại với tùy chọn support_only=True
            rules = association_rules(frequent_itemsets_for_rules, metric="lift", 
                                     min_threshold=1.0, support_only=True)
            
            print(f"\nTổng số luật kết hợp tìm được (với support_only=True): {len(rules)}")
            if len(rules) > 0:
                print("\nTop 5 luật kết hợp có lift cao nhất:")
                print(rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']].head())
        except Exception as e:
            print(f"Không thể tìm luật kết hợp: {str(e)}")
            # Tạo một DataFrame rỗng để tránh lỗi
            rules = pd.DataFrame(columns=['antecedents', 'consequents', 'antecedent support', 
                                         'consequent support', 'support', 'confidence', 'lift',
                                         'leverage', 'conviction'])
    else:
        print("Không tìm thấy tập phổ biến nào với ngưỡng min_support hiện tại.")
        print("Thử giảm ngưỡng min_support hoặc giảm số lượng sản phẩm phân tích.")
        # Tạo cấu trúc dữ liệu rỗng để tránh lỗi khi import
        frequent_itemsets = pd.DataFrame(columns=['itemsets', 'support', 'itemset_length'])
        rules = pd.DataFrame(columns=['antecedents', 'consequents', 'antecedent support', 
                                     'consequent support', 'support', 'confidence', 'lift',
                                     'leverage', 'conviction'])
except MemoryError:
    print("Lỗi bộ nhớ khi thực hiện thuật toán Apriori.")
    print("Thử lại với ngưỡng min_support cao hơn hoặc giảm số lượng sản phẩm phân tích.")
    # Tạo cấu trúc dữ liệu rỗng để tránh lỗi khi import
    frequent_itemsets = pd.DataFrame(columns=['itemsets', 'support', 'itemset_length'])
    rules = pd.DataFrame(columns=['antecedents', 'consequents', 'antecedent support', 
                                 'consequent support', 'support', 'confidence', 'lift',
                                 'leverage', 'conviction'])
except Exception as e:
    print(f"Lỗi không xác định khi phân tích Apriori: {str(e)}")
    # Tạo cấu trúc dữ liệu rỗng để tránh lỗi khi import
    frequent_itemsets = pd.DataFrame(columns=['itemsets', 'support', 'itemset_length'])
    rules = pd.DataFrame(columns=['antecedents', 'consequents', 'antecedent support', 
                                 'consequent support', 'support', 'confidence', 'lift',
                                 'leverage', 'conviction'])

# Import dữ liệu vào SQL Server
print("\n=== IMPORT DỮ LIỆU VÀO SQL SERVER ===")
conn = get_connection()
if conn:
    try:
        cursor = conn.cursor()
        
        # Tạo bảng cleaned_retail_data nếu chưa tồn tại
        print("Đang tạo/xóa bảng cleaned_retail_data...")
        cursor.execute("IF OBJECT_ID('cleaned_retail_data', 'U') IS NOT NULL DROP TABLE cleaned_retail_data")
        conn.commit()
        
        # Tạo bảng mới
        cursor.execute("""
        CREATE TABLE cleaned_retail_data (
            ID INT PRIMARY KEY,
            InvoiceNo NVARCHAR(50),
            StockCode NVARCHAR(50),
            Description NVARCHAR(255),
            Quantity INT,
            InvoiceDate DATETIME,
            UnitPrice FLOAT,
            CustomerID INT,
            Country NVARCHAR(50),
            TotalPrice FLOAT,
            Month INT,
            Year INT,
            Day INT,
            DayOfWeek INT,
            Quarter INT
        )
        """)
        conn.commit()
        
        # Chèn dữ liệu
        print("Đang chèn dữ liệu vào bảng cleaned_retail_data...")
        for index, row in df.iterrows():
            if index % 5000 == 0:
                print(f"Đã chèn {index} dòng...")
            
            cursor.execute("""
            INSERT INTO cleaned_retail_data 
            (ID, InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, 
             CustomerID, Country, TotalPrice, Month, Year, Day, DayOfWeek, Quarter)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, 
            row['ID'], row['InvoiceNo'], row['StockCode'], row['Description'], 
            row['Quantity'], row['InvoiceDate'], row['UnitPrice'], row['CustomerID'],
            row['Country'], row['TotalPrice'], row['Month'], row['Year'], 
            row['Day'], row['DayOfWeek'], row['Quarter'])
            
            if index % 1000 == 0:
                conn.commit()
        
        conn.commit()
        print("Hoàn thành chèn dữ liệu vào bảng cleaned_retail_data.")
        
        # Tạo bảng products
        print("Đang tạo/xóa bảng products...")
        cursor.execute("IF OBJECT_ID('products', 'U') IS NOT NULL DROP TABLE products")
        conn.commit()
        
        cursor.execute("""
        CREATE TABLE products (
            ProductId INT IDENTITY(1,1) PRIMARY KEY,
            StockCode NVARCHAR(50),
            Description NVARCHAR(255),
            MaxUnitPrice FLOAT,
            TotalQuantitySold INT,
            TotalRevenue FLOAT,
            NumberOfTransactions INT,
            NumberOfCustomers INT,
            ImagePath NVARCHAR(255)
        )
        """)
        conn.commit()
        
        # Chèn dữ liệu vào bảng products
        print("Đang chèn dữ liệu vào bảng products...")
        for index, row in product_stats.iterrows():
            cursor.execute("""
            INSERT INTO products 
            (StockCode, Description, MaxUnitPrice, TotalQuantitySold, TotalRevenue, 
             NumberOfTransactions, NumberOfCustomers, ImagePath)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, 
            row['StockCode'], row['Description'], row['MaxUnitPrice'], 
            row['TotalQuantitySold'], row['TotalRevenue'], row['NumberOfTransactions'],
            row['NumberOfCustomers'], row['ImagePath'])
        
        conn.commit()
        print("Hoàn thành chèn dữ liệu vào bảng products.")
        
        # Tạo bảng frequent_itemsets
        print("Đang tạo/xóa bảng frequent_itemsets...")
        cursor.execute("IF OBJECT_ID('frequent_itemsets', 'U') IS NOT NULL DROP TABLE frequent_itemsets")
        conn.commit()
        
        cursor.execute("""
        CREATE TABLE frequent_itemsets (
            id INT IDENTITY(1,1) PRIMARY KEY,
            itemsets NVARCHAR(MAX),
            support FLOAT,
            itemset_length INT
        )
        """)
        conn.commit()
        
        # Chèn dữ liệu vào bảng frequent_itemsets
        print("Đang chèn dữ liệu vào bảng frequent_itemsets...")
        for index, row in frequent_itemsets.iterrows():
            cursor.execute("""
            INSERT INTO frequent_itemsets (itemsets, support, itemset_length)
            VALUES (?, ?, ?)
            """, row['itemsets'], row['support'], row['itemset_length'])
        
        conn.commit()
        print("Hoàn thành chèn dữ liệu vào bảng frequent_itemsets.")
        
        # Tạo bảng association_rules
        print("Đang tạo/xóa bảng association_rules...")
        cursor.execute("IF OBJECT_ID('association_rules', 'U') IS NOT NULL DROP TABLE association_rules")
        conn.commit()
        
        cursor.execute("""
        CREATE TABLE association_rules (
            id INT IDENTITY(1,1) PRIMARY KEY,
            antecedents NVARCHAR(MAX),
            consequents NVARCHAR(MAX),
            antecedent_support FLOAT,
            consequent_support FLOAT,
            support FLOAT,
            confidence FLOAT,
            lift FLOAT,
            leverage FLOAT,
            conviction FLOAT
        )
        """)
        conn.commit()
        
        # Chèn dữ liệu vào bảng association_rules
        print("Đang chèn dữ liệu vào bảng association_rules...")
        for index, row in rules.iterrows():
            cursor.execute("""
            INSERT INTO association_rules 
            (antecedents, consequents, antecedent_support, consequent_support, 
             support, confidence, lift, leverage, conviction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, 
            ', '.join(list(row['antecedents'])), ', '.join(list(row['consequents'])), row['antecedent support'], 
            row['consequent support'], row['support'], row['confidence'], 
            row['lift'], row['leverage'], row['conviction'])
        
        conn.commit()
        print("Hoàn thành chèn dữ liệu vào bảng association_rules.")
        
        print("Đã import tất cả dữ liệu vào SQL Server thành công!")
        
    except Exception as e:
        print(f"Lỗi khi import dữ liệu: {str(e)}")
    finally:
        conn.close()
else:
    print("Không thể kết nối đến SQL Server, lưu kết quả vào CSV để sử dụng với SQLite...")
    # Lưu dữ liệu vào CSV để sử dụng với SQLite nếu không kết nối được SQL Server
    df.to_csv(os.path.join(base_dir, 'cleaned_retail_data.csv'), index=False)
    frequent_itemsets.to_csv(os.path.join(base_dir, 'frequent_itemsets.csv'), index=False)
    rules.to_csv(os.path.join(base_dir, 'association_rules.csv'), index=False)
    print("Đã lưu dữ liệu vào các file CSV thay thế.")

print("\nHoàn thành phân tích dữ liệu và import vào cơ sở dữ liệu!")

# Xóa các file Excel tạm thời không cần thiết (tùy chọn)
excel_to_remove = ['retail_analysis_results.xlsx']
for file in excel_to_remove:
    file_path = os.path.join(base_dir, file)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"Đã xóa file {file}")
        except Exception as e:
            print(f"Không thể xóa file {file}: {str(e)}")
