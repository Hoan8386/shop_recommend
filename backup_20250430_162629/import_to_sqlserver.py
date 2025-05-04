import pandas as pd
import pyodbc
import os
import shutil
import sys
import time
from datetime import datetime

# Path to your CSV files
base_dir = os.path.dirname(os.path.abspath(__file__))
cleaned_retail_path = os.path.join(base_dir, 'cleaned_retail_data.csv')
association_rules_path = os.path.join(base_dir, 'association_rules.csv')
frequent_itemsets_path = os.path.join(base_dir, 'frequent_itemsets.csv')

# SQL Server connection settings - update these with your SQL Server details
server = 'DESKTOP-C4ALSJO\SQLEXPRESS'  # e.g., 'localhost\SQLEXPRESS'
database = 'shopping'
username = 'sa'  # if using Windows Authentication, comment this and the password line
password = '123'
trusted_connection = 'yes'  # Use Windows Authentication, set to 'no' if using SQL username/password

# Create the connection string
if trusted_connection.lower() == 'yes':
    # Windows Authentication
    conn_str = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
else:
    # SQL Server Authentication
    conn_str = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

def import_products_with_max_price():
    """
    Import products from cleaned_retail_data.csv to SQL Server,
    using the maximum price for each product across all invoices.
    """
    try:
        # Connect to SQL Server
        print("Connecting to SQL Server...")
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        print(f"Connected to {server}, database: {database}")
        
        # Load data from CSV
        print("Reading cleaned_retail_data.csv file...")
        retail_df = pd.read_csv(cleaned_retail_path)
        
        # Handle potential issues with StockCode/Description combinations
        print("Handling duplicate StockCodes...")
        
        # First step: Identify cases where a StockCode has multiple Descriptions
        stock_desc_counts = retail_df.groupby('StockCode')['Description'].nunique().reset_index()
        duplicate_stocks = stock_desc_counts[stock_desc_counts['Description'] > 1]['StockCode'].tolist()
        
        if duplicate_stocks:
            print(f"Found {len(duplicate_stocks)} StockCodes with multiple descriptions")
            # For each duplicate StockCode, choose the most frequent Description
            for stock in duplicate_stocks:
                most_common_desc = retail_df[retail_df['StockCode'] == stock]['Description'].value_counts().index[0]
                retail_df.loc[retail_df['StockCode'] == stock, 'Description'] = most_common_desc
        
        # Calculate maximum price for each product
        print("Calculating maximum price for each product...")
        product_max_price = retail_df.groupby('StockCode')['UnitPrice'].max().reset_index()
        
        # Get the most common description for each StockCode
        product_desc = retail_df.groupby('StockCode')['Description'].first().reset_index()
        
        # Calculate additional statistics for each product
        product_stats = retail_df.groupby('StockCode').agg({
            'Quantity': 'sum',
            'TotalPrice': 'sum',
            'InvoiceNo': pd.Series.nunique
        }).reset_index()
        
        # Merge all product data together
        products_df = pd.merge(product_max_price, product_desc, on='StockCode')
        products_df = pd.merge(products_df, product_stats, on='StockCode')
        products_df.rename(columns={
            'UnitPrice': 'MaxUnitPrice', 
            'Quantity': 'TotalQuantitySold',
            'InvoiceNo': 'NumberOfTransactions'
        }, inplace=True)
        
        # Check if folder exists and assign image paths
        images_dir = os.path.join(base_dir, 'imagesProduct')
        products_df['ImagePath'] = None
        
        if os.path.exists(images_dir):
            # Get list of all image files
            image_files = os.listdir(images_dir)
            
            # Map products to images if there's a match in description
            for index, row in products_df.iterrows():
                product_name = row['Description']
                for image_file in image_files:
                    img_name = os.path.splitext(image_file)[0]
                    if img_name in product_name:
                        products_df.at[index, 'ImagePath'] = f'imagesProduct/{image_file}'
                        break
        
        # First clear existing data (if any)
        print("Clearing existing product data...")
        cursor.execute("DELETE FROM [dbo].[products]")
        conn.commit()
        
        # Insert data into products table
        print("Importing products data...")
        for index, row in products_df.iterrows():
            cursor.execute("""
            INSERT INTO [dbo].[products] 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, 
            row['StockCode'], 
            row['Description'], 
            row['MaxUnitPrice'],
            row['TotalQuantitySold'],
            row['TotalPrice'],
            row['NumberOfTransactions'],
            row['ImagePath'])
            
            # Commit every 100 rows to avoid memory issues
            if index % 100 == 0:
                conn.commit()
                print(f"Imported {index} product records...")
        
        conn.commit()
        print(f"Imported all {len(products_df)} product records successfully!")
        print("Product data import complete!")
        
    except pyodbc.Error as e:
        print(f"Database Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close the connection
        if 'conn' in locals():
            conn.close()
            print("Connection closed.")

try:
    # Connect to SQL Server
    print("Connecting to SQL Server...")
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    print(f"Connected to {server}, database: {database}")
    
    # Check if database exists, if not create it
    cursor.execute(f"IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{database}') CREATE DATABASE [{database}]")
    
    # Create tables if they don't exist
    print("Creating tables if they don't exist...")
    
    # 4. Create table for products
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[products]') AND type in (N'U'))
    CREATE TABLE [dbo].[products](
        [ProductId] INT IDENTITY(1,1),
        [StockCode] NVARCHAR(50) PRIMARY KEY,
        [Description] NVARCHAR(255),
        [MaxUnitPrice] DECIMAL(10, 2),
        [TotalQuantitySold] INT,
        [TotalRevenue] DECIMAL(15, 2),
        [NumberOfTransactions] INT,
        [ImagePath] NVARCHAR(255) NULL
    )
    """)
    
    # 1. Create table for cleaned_retail_data with auto-incrementing ID
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[cleaned_retail_data]') AND type in (N'U'))
    CREATE TABLE [dbo].[cleaned_retail_data](
        [ID] INT IDENTITY(1,1) PRIMARY KEY,
        [InvoiceNo] NVARCHAR(50),
        [StockCode] NVARCHAR(50),
        [Description] NVARCHAR(255),
        [Quantity] INT,
        [InvoiceDate] DATETIME,
        [UnitPrice] DECIMAL(10, 2),
        [CustomerID] INT,
        [Country] NVARCHAR(50),
        [TotalPrice] DECIMAL(10, 2),
        [Month] INT,
        [Year] INT,
        [Day] DATE,
        CONSTRAINT [FK_CleanedRetail_Products] FOREIGN KEY ([StockCode]) 
        REFERENCES [dbo].[products] ([StockCode])
    )
    """)
    
    # 2. Create table for association_rules with auto-incrementing ID
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[association_rules]') AND type in (N'U'))
    CREATE TABLE [dbo].[association_rules](
        [ID] INT IDENTITY(1,1) PRIMARY KEY,
        [antecedents] NVARCHAR(MAX),
        [consequents] NVARCHAR(MAX),
        [antecedent support] FLOAT,
        [consequent support] FLOAT,
        [support] FLOAT,
        [confidence] FLOAT,
        [lift] FLOAT,
        [representativity] FLOAT,
        [leverage] FLOAT,
        [conviction] FLOAT,
        [zhangs_metric] FLOAT,
        [jaccard] FLOAT,
        [certainty] FLOAT,
        [kulczynski] FLOAT
    )
    """)
    
    # 3. Create table for frequent_itemsets with auto-incrementing ID
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[frequent_itemsets]') AND type in (N'U'))
    CREATE TABLE [dbo].[frequent_itemsets](
        [ID] INT IDENTITY(1,1) PRIMARY KEY,
        [support] FLOAT,
        [itemsets] NVARCHAR(MAX)
    )
    """)
    
    conn.commit()
    print("Tables created successfully!")
    
    # Import products first
    import_products_with_max_price()
    
    # Load data from CSVs
    print("Reading CSV files...")
    cleaned_retail_df = pd.read_csv(cleaned_retail_path)
    association_rules_df = pd.read_csv(association_rules_path)
    frequent_itemsets_df = pd.read_csv(frequent_itemsets_path)
    
    # Convert datetime column to proper format
    cleaned_retail_df['InvoiceDate'] = pd.to_datetime(cleaned_retail_df['InvoiceDate'])
    
    # First clear existing data (if any)
    print("Clearing existing data...")
    cursor.execute("DELETE FROM [dbo].[cleaned_retail_data]")
    cursor.execute("DELETE FROM [dbo].[association_rules]")
    cursor.execute("DELETE FROM [dbo].[frequent_itemsets]")
    conn.commit()
    
    # Insert data into cleaned_retail_data table
    print("Importing cleaned retail data...")
    for index, row in cleaned_retail_df.iterrows():
        try:
            cursor.execute("""
            INSERT INTO [dbo].[cleaned_retail_data] 
            (InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country, TotalPrice, Month, Year, Day)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, 
            row['InvoiceNo'], 
            row['StockCode'], 
            row['Description'], 
            row['Quantity'], 
            row['InvoiceDate'],
            row['UnitPrice'],
            row['CustomerID'],
            row['Country'],
            row['TotalPrice'],
            row['Month'],
            row['Year'],
            str(row['InvoiceDate'].date()))  # Convert date to string format YYYY-MM-DD
        except pyodbc.Error as e:
            # Skip records that violate foreign key constraints
            print(f"Skipping record: {row['StockCode']} - {e}")
            continue
            
        # Commit every 1000 rows to avoid memory issues
        if index % 1000 == 0:
            conn.commit()
            print(f"Imported {index} retail records...")
    
    conn.commit()
    print(f"Imported retail records successfully!")
    
    # Insert data into association_rules table
    print("Importing association rules...")
    for index, row in association_rules_df.iterrows():
        cursor.execute("""
        INSERT INTO [dbo].[association_rules] 
        (antecedents, consequents, [antecedent support], [consequent support], support, confidence, lift, 
         representativity, leverage, conviction, zhangs_metric, jaccard, certainty, kulczynski)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, 
        row['antecedents'], 
        row['consequents'], 
        row['antecedent support'], 
        row['consequent support'],
        row['support'],
        row['confidence'],
        row['lift'],
        row['representativity'],
        row['leverage'],
        row['conviction'],
        row['zhangs_metric'],
        row['jaccard'],
        row['certainty'],
        row['kulczynski'])
        
        # Commit every 100 rows
        if index % 100 == 0:
            conn.commit()
            print(f"Imported {index} association rules...")
    
    conn.commit()
    print(f"Imported all {len(association_rules_df)} association rules successfully!")
    
    # Insert data into frequent_itemsets table
    print("Importing frequent itemsets...")
    for index, row in frequent_itemsets_df.iterrows():
        cursor.execute("""
        INSERT INTO [dbo].[frequent_itemsets] 
        (support, itemsets)
        VALUES (?, ?)
        """, 
        row['support'], 
        row['itemsets'])
        
        # Commit every 100 rows
        if index % 100 == 0:
            conn.commit()
            print(f"Imported {index} frequent itemsets...")
    
    conn.commit()
    print(f"Imported all {len(frequent_itemsets_df)} frequent itemsets successfully!")
    
    print("All data import complete!")
    
except pyodbc.Error as e:
    print(f"Database Error: {e}")
except Exception as e:
    print(f"Error: {e}")
finally:
    # Close the connection
    if 'conn' in locals():
        conn.close()
        print("Connection closed.")

# If you want to run only the product import
if __name__ == "__main__":
    # Uncomment the line below to only import products when running this script directly
    # import_products_with_max_price()
    pass

print("Bắt đầu quá trình dọn dẹp dự án...")

# Danh sách các file cần giữ lại
essential_files = [
    'OnlineRetail.xlsx',  # File dữ liệu gốc
    'data_analysis.py',   # Script phân tích dữ liệu
    'api.py',             # API Flask
    'db_connection.py',   # Kết nối CSDL
    'index.html',         # Giao diện dashboard
    'shop.html',          # Giao diện cửa hàng
    'shop.js',            # JavaScript cho cửa hàng
    'api_documentation.md',  # Tài liệu API
    'import_to_sqlserver.py',  # Script hiện tại
]

# Danh sách các thư mục cần giữ lại
essential_folders = [
    'imagesProduct',  # Thư mục chứa ảnh sản phẩm
    'static',         # Thư mục chứa tài nguyên tĩnh
    '__pycache__'     # Thư mục cache Python (có thể xóa nhưng sẽ tự tạo lại)
]

# Danh sách các file hình ảnh kết quả phân tích cần giữ lại
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
    """Xóa các file không cần thiết sau khi đã import vào cơ sở dữ liệu"""
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
    print("\nCác tệp được giữ lại:")
    for file in essential_files + essential_images:
        file_path = os.path.join(base_dir, file)
        if os.path.exists(file_path):
            print(f"  - {file}")
    
    print("\nCác thư mục được giữ lại:")
    for folder in essential_folders:
        folder_path = os.path.join(base_dir, folder)
        if os.path.exists(folder_path):
            print(f"  - {folder}")
    
    print("\nDự án đã sẵn sàng để sử dụng trực tiếp với SQL Server.")