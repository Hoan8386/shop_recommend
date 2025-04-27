import pyodbc

# Thông tin kết nối SQL Server
SERVER = r'DESKTOP-C4ALSJO\SQLEXPRESS'  # Thêm r để tránh lỗi escape sequence
DATABASE = 'shopping'
USERNAME = 'sa'
PASSWORD = '123'

def get_connection():
    try:
        conn = pyodbc.connect(
            f'DRIVER={{SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}'
        )
        return conn
    except Exception as e:
        print(f"Lỗi kết nối: {str(e)}")
        return None

def get_products(page=1, per_page=10):
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            # Tính offset cho phân trang
            offset = (page - 1) * per_page
            
            # Query lấy tổng số sản phẩm
            cursor.execute("SELECT COUNT(*) FROM products")
            total_count = int(cursor.fetchone()[0])
            
            # Query lấy sản phẩm có phân trang
            cursor.execute("""
            SELECT 
                ProductId,
                StockCode,
                Description,
                MaxUnitPrice,
                TotalQuantitySold,
                TotalRevenue,
                NumberOfTransactions,
                ImagePath
            FROM products
            ORDER BY TotalQuantitySold DESC
            OFFSET ? ROWS
            FETCH NEXT ? ROWS ONLY
            """, offset, per_page)
            
            products = []
            for row in cursor.fetchall():
                products.append({
                    'ProductId': int(row[0]),
                    'StockCode': row[1],
                    'Description': row[2],
                    'MaxUnitPrice': float(row[3]),
                    'TotalQuantitySold': int(row[4]),
                    'TotalRevenue': float(row[5]),
                    'NumberOfTransactions': int(row[6]),
                    'ImagePath': row[7]
                })
            
            conn.close()
            
            return {
                'products': products,
                'total': total_count,
                'page': int(page),
                'per_page': int(per_page),
                'total_pages': int((total_count + per_page - 1) // per_page)
            }
        return {'products': [], 'total': 0, 'page': 1, 'per_page': 10, 'total_pages': 0}
    except Exception as e:
        print(f"Lỗi truy vấn: {str(e)}")
        return {'products': [], 'total': 0, 'page': 1, 'per_page': 10, 'total_pages': 0}

def search_products(query, page=1, per_page=10):
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            offset = (page - 1) * per_page
            
            # Query tìm kiếm có phân trang
            cursor.execute("""
            SELECT 
                ProductId,
                StockCode,
                Description,
                MaxUnitPrice,
                TotalQuantitySold,
                TotalRevenue,
                NumberOfTransactions,
                ImagePath
            FROM products
            WHERE Description LIKE ?
            ORDER BY TotalQuantitySold DESC
            OFFSET ? ROWS
            FETCH NEXT ? ROWS ONLY
            """, f'%{query}%', offset, per_page)
            
            # Lấy tổng số kết quả tìm kiếm
            cursor.execute("SELECT COUNT(*) FROM products WHERE Description LIKE ?", f'%{query}%')
            total_count = int(cursor.fetchone()[0])
            
            products = []
            for row in cursor.fetchall():
                products.append({
                    'ProductId': int(row[0]),
                    'StockCode': row[1],
                    'Description': row[2],
                    'MaxUnitPrice': float(row[3]),
                    'TotalQuantitySold': int(row[4]),
                    'TotalRevenue': float(row[5]),
                    'NumberOfTransactions': int(row[6]),
                    'ImagePath': row[7]
                })
            
            conn.close()
            
            return {
                'products': products,
                'total': total_count,
                'page': int(page),
                'per_page': int(per_page),
                'total_pages': int((total_count + per_page - 1) // per_page)
            }
        return {'products': [], 'total': 0, 'page': 1, 'per_page': 10, 'total_pages': 0}
    except Exception as e:
        print(f"Lỗi truy vấn: {str(e)}")
        return {'products': [], 'total': 0, 'page': 1, 'per_page': 10, 'total_pages': 0}

def get_product_recommendations(product_id):
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            
            # Lấy thông tin sản phẩm hiện tại
            cursor.execute("""
            SELECT Description FROM products WHERE ProductId = ?
            """, product_id)
            
            product_row = cursor.fetchone()
            if not product_row:
                return {'recommendations': []}
                
            product_desc = product_row[0]
            
            # Lấy sản phẩm gợi ý dựa trên luật kết hợp
            cursor.execute("""
            SELECT TOP 10
                p.ProductId,
                p.StockCode,
                p.Description,
                p.MaxUnitPrice,
                p.TotalQuantitySold,
                p.ImagePath,
                ar.confidence,
                ar.support
            FROM products p
            JOIN association_rules ar ON p.Description LIKE '%' + ar.consequents + '%'
            WHERE ar.antecedents LIKE ?
            ORDER BY ar.confidence DESC
            """, f'%{product_desc}%')
            
            recommendations = []
            for row in cursor.fetchall():
                recommendations.append({
                    'ProductId': int(row[0]),
                    'StockCode': row[1],
                    'Description': row[2],
                    'MaxUnitPrice': float(row[3]),
                    'TotalQuantitySold': int(row[4]),
                    'ImagePath': row[5],
                    'confidence': float(row[6]),
                    'support': float(row[7])
                })
            
            conn.close()
            
            return {
                'recommendations': recommendations
            }
        return {'recommendations': []}
    except Exception as e:
        print(f"Lỗi truy vấn: {str(e)}")
        return {'recommendations': []}

def get_cleaned_products(page=1, per_page=12):
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            offset = (page - 1) * per_page
            
            # Lấy tổng số dòng
            cursor.execute("SELECT COUNT(*) FROM cleaned_retail_data")
            total_count = int(cursor.fetchone()[0])

            # Lấy dữ liệu phân trang
            cursor.execute("""
                SELECT ID, InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country, TotalPrice, Month, Year, Day
                FROM cleaned_retail_data
                ORDER BY ID
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, offset, per_page)
            
            products = []
            for row in cursor.fetchall():
                products.append({
                    'ID': int(row[0]),
                    'InvoiceNo': row[1],
                    'StockCode': row[2],
                    'Description': row[3],
                    'Quantity': int(row[4]),
                    'InvoiceDate': row[5],
                    'UnitPrice': float(row[6]),
                    'CustomerID': row[7],
                    'Country': row[8],
                    'TotalPrice': float(row[9]),
                    'Month': int(row[10]),
                    'Year': int(row[11]),
                    'Day': row[12]
                })
            
            conn.close()
            
            return {
                'products': products,
                'total': total_count,
                'page': int(page),
                'per_page': int(per_page),
                'total_pages': int((total_count + per_page - 1) // per_page)
            }
        return {'products': [], 'total': 0, 'page': 1, 'per_page': per_page, 'total_pages': 0}
    except Exception as e:
        print(f"Lỗi truy vấn: {str(e)}")
        return {'products': [], 'total': 0, 'page': 1, 'per_page': per_page, 'total_pages': 0}