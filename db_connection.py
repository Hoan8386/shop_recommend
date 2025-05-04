import pyodbc
import traceback
import sys
import hashlib
import datetime

# Thông tin kết nối SQL Server
SERVER = r'DESKTOP-C4ALSJO\SQLEXPRESS'  # Thêm r để tránh lỗi escape sequence
DATABASE = 'shopping'
USERNAME = 'sa'
PASSWORD = '123'

def get_connection():
    try:
        print("Đang kết nối đến SQL Server...")
        conn = pyodbc.connect(
            f'DRIVER={{SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}'
        )
        print("Kết nối SQL Server thành công!")
        return conn
    except Exception as e:
        print(f"Lỗi kết nối SQL Server: {str(e)}")
        print("Chi tiết lỗi:")
        traceback.print_exc(file=sys.stdout)
        return None

# Hàm kiểm tra kết nối và hiển thị thông tin
def check_database_connection():
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Kiểm tra bảng products
            cursor.execute("SELECT COUNT(*) FROM products")
            product_count = cursor.fetchone()[0]
            print(f"Số lượng sản phẩm trong bảng products: {product_count}")
            
            # Kiểm tra bảng association_rules
            cursor.execute("SELECT COUNT(*) FROM association_rules")
            rules_count = cursor.fetchone()[0]
            print(f"Số lượng luật kết hợp trong bảng association_rules: {rules_count}")
            
            # Kiểm tra bảng frequent_itemsets
            cursor.execute("SELECT COUNT(*) FROM frequent_itemsets")
            itemsets_count = cursor.fetchone()[0]
            print(f"Số lượng tập phổ biến trong bảng frequent_itemsets: {itemsets_count}")
            
            conn.close()
            return {
                "connected": True,
                "product_count": product_count,
                "rules_count": rules_count,
                "itemsets_count": itemsets_count
            }
        except Exception as e:
            print(f"Lỗi khi kiểm tra cơ sở dữ liệu: {str(e)}")
            return {
                "connected": True,
                "error": str(e)
            }
    else:
        return {
            "connected": False,
            "error": "Không thể kết nối đến SQL Server"
        }

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
            
            # Kiểm tra nếu không có sản phẩm nào
            if total_count == 0:
                print("CẢNH BÁO: Bảng products không có dữ liệu!")
                return {'products': [], 'total': 0, 'page': 1, 'per_page': 10, 'total_pages': 0}
            
            # Query lấy sản phẩm có phân trang
            cursor.execute("""
            SELECT 
                ProductId,
                StockCode,
                Description,
                MaxUnitPrice AS UnitPrice,
                TotalQuantitySold AS Quantity,
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
                    'UnitPrice': float(row[3]),
                    'Quantity': int(row[4]),
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
        print("CẢNH BÁO: Không thể kết nối đến SQL Server. Vui lòng kiểm tra cài đặt kết nối và dịch vụ SQL Server.")
        return {'products': [], 'total': 0, 'page': 1, 'per_page': 10, 'total_pages': 0}
    except Exception as e:
        print(f"Lỗi truy vấn: {str(e)}")
        traceback.print_exc(file=sys.stdout)
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

def get_product_statistics():
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            
            # Lấy tổng số sản phẩm khác nhau
            cursor.execute("""
                SELECT COUNT(DISTINCT Description) 
                FROM cleaned_retail_data
            """)
            total_products = int(cursor.fetchone()[0])
            
            # Lấy tổng số khách hàng
            cursor.execute("""
                SELECT COUNT(DISTINCT CustomerID) 
                FROM cleaned_retail_data 
                WHERE CustomerID IS NOT NULL
            """)
            total_customers = int(cursor.fetchone()[0])
            
            # Lấy tổng số giao dịch
            cursor.execute("""
                SELECT COUNT(DISTINCT InvoiceNo) 
                FROM cleaned_retail_data
            """)
            total_transactions = int(cursor.fetchone()[0])
            
            # Tính số sản phẩm trung bình mỗi giao dịch
            cursor.execute("""
                SELECT AVG(product_count) AS avg_products_per_transaction
                FROM (
                    SELECT InvoiceNo, COUNT(*) AS product_count
                    FROM cleaned_retail_data
                    GROUP BY InvoiceNo
                ) AS subquery
            """)
            avg_products_per_transaction = float(cursor.fetchone()[0])
            
            # Lấy sản phẩm phổ biến nhất
            cursor.execute("""
                SELECT TOP 10 Description, SUM(Quantity) as TotalQuantity
                FROM cleaned_retail_data
                GROUP BY Description
                ORDER BY TotalQuantity DESC
            """)
            
            top_products = []
            for row in cursor.fetchall():
                top_products.append({
                    'Description': row[0],
                    'TotalQuantity': int(row[1])
                })
            
            # Lấy doanh thu theo tháng
            cursor.execute("""
                SELECT Month, SUM(TotalPrice) as MonthlyRevenue
                FROM cleaned_retail_data
                GROUP BY Month
                ORDER BY Month
            """)
            
            monthly_revenue = []
            for row in cursor.fetchall():
                monthly_revenue.append({
                    'month': int(row[0]),
                    'revenue': float(row[1])
                })
            
            conn.close()
            
            return {
                'total_products': total_products,
                'total_customers': total_customers,
                'total_transactions': total_transactions,
                'avg_products_per_transaction': avg_products_per_transaction,
                'top_products_by_quantity': top_products,
                'monthly_revenue': monthly_revenue
            }
        return {'top_products': [], 'monthly_revenue': []}
    except Exception as e:
        print(f"Lỗi truy vấn: {str(e)}")
        return {'top_products': [], 'monthly_revenue': []}

def get_shopping_behavior():
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            
            # Lấy tần suất mua hàng theo quốc gia
            cursor.execute("""
                SELECT TOP 10 Country, COUNT(DISTINCT InvoiceNo) as PurchaseCount
                FROM cleaned_retail_data
                GROUP BY Country
                ORDER BY PurchaseCount DESC
            """)
            
            purchase_by_country = []
            for row in cursor.fetchall():
                purchase_by_country.append({
                    'country': row[0],
                    'count': int(row[1])
                })
            
            # Lấy giá trị đơn hàng trung bình theo quốc gia
            cursor.execute("""
                SELECT TOP 10 Country, AVG(total_invoice) as AverageOrderValue
                FROM (
                    SELECT Country, InvoiceNo, SUM(TotalPrice) as total_invoice
                    FROM cleaned_retail_data
                    GROUP BY Country, InvoiceNo
                ) subquery
                GROUP BY Country
                ORDER BY AverageOrderValue DESC
            """)
            
            avg_order_by_country = []
            for row in cursor.fetchall():
                avg_order_by_country.append({
                    'country': row[0],
                    'average': float(row[1])
                })
            
            # Tạo dữ liệu để hiển thị đẹp hơn cho phân bố tần suất mua hàng
            purchase_frequency_distribution = {}
            
            # Sử dụng truy vấn đơn giản hơn để tương thích với SQL Server
            cursor.execute("""
                SELECT purchase_count, COUNT(*) as customer_count
                FROM (
                    SELECT CustomerID, COUNT(DISTINCT InvoiceNo) as purchase_count
                    FROM cleaned_retail_data
                    WHERE CustomerID IS NOT NULL
                    GROUP BY CustomerID
                ) as subquery
                GROUP BY purchase_count
                ORDER BY purchase_count
            """)
            
            for row in cursor.fetchall():
                purchase_count = row[0]
                customer_count = row[1]
                
                # Nhóm số lượng mua hàng thành các khoảng để hiển thị đẹp hơn
                if purchase_count <= 9:
                    category = str(purchase_count)
                else:
                    category = "10+"
                
                # Cộng dồn nếu đã có category này
                if category in purchase_frequency_distribution:
                    purchase_frequency_distribution[category] += int(customer_count)
                else:
                    purchase_frequency_distribution[category] = int(customer_count)
            
            # Phân bố chi tiêu khách hàng - Sử dụng cách tiếp cận đơn giản hơn
            spending_distribution = {
                "0-100": 0, "100-500": 0, "500-1000": 0,
                "1000-5000": 0, "5000+": 0
            }
            
            cursor.execute("""
                SELECT CustomerID, SUM(TotalPrice) as total_spent
                FROM cleaned_retail_data
                WHERE CustomerID IS NOT NULL
                GROUP BY CustomerID
            """)
            
            for row in cursor.fetchall():
                total_spent = float(row[1])
                
                # Phân loại chi tiêu
                if total_spent < 100:
                    category = "0-100"
                elif total_spent < 500:
                    category = "100-500"
                elif total_spent < 1000:
                    category = "500-1000"
                elif total_spent < 5000:
                    category = "1000-5000"
                else:
                    category = "5000+"
                
                spending_distribution[category] += 1
            
            # Thống kê trung bình - Sử dụng cách tiếp cận đơn giản hơn
            total_customers = 0
            total_purchase_frequency = 0
            total_spent_amount = 0
            total_unique_products = 0
            
            cursor.execute("""
                SELECT 
                    CustomerID,
                    COUNT(DISTINCT InvoiceNo) as purchase_count,
                    SUM(TotalPrice) as total_spent,
                    COUNT(DISTINCT Description) as unique_products
                FROM cleaned_retail_data
                WHERE CustomerID IS NOT NULL
                GROUP BY CustomerID
            """)
            
            customer_data = cursor.fetchall()
            total_customers = len(customer_data)
            
            if total_customers > 0:
                for row in customer_data:
                    total_purchase_frequency += int(row[1])
                    total_spent_amount += float(row[2])
                    total_unique_products += int(row[3])
                
                average_stats = {
                    'avg_purchase_frequency': round(total_purchase_frequency / total_customers, 2),
                    'avg_total_spent': round(total_spent_amount / total_customers, 2),
                    'avg_unique_products': round(total_unique_products / total_customers, 2)
                }
            else:
                average_stats = {
                    'avg_purchase_frequency': 0,
                    'avg_total_spent': 0,
                    'avg_unique_products': 0
                }
            
            conn.close()
            
            return {
                'purchase_by_country': purchase_by_country,
                'avg_order_by_country': avg_order_by_country,
                'purchase_frequency_distribution': purchase_frequency_distribution,
                'spending_distribution': spending_distribution,
                'average_stats': average_stats
            }
            
        # Nếu không kết nối được, trả về dữ liệu mặc định đơn giản
        return {
            'purchase_by_country': [], 
            'avg_order_by_country': [],
            'purchase_frequency_distribution': {"1": 10, "2": 5, "3": 3, "4": 2, "5": 1},
            'spending_distribution': {"0-100": 10, "100-500": 5, "500-1000": 3, "1000-5000": 2, "5000+": 1},
            'average_stats': {
                'avg_purchase_frequency': 2.5,
                'avg_total_spent': 350.75,
                'avg_unique_products': 4.8
            }
        }
    except Exception as e:
        print(f"Lỗi khi phân tích hành vi mua sắm: {str(e)}")
        # Trả về dữ liệu thay thế trong trường hợp lỗi
        return {
            'purchase_by_country': [], 
            'avg_order_by_country': [],
            'purchase_frequency_distribution': {"1": 10, "2": 5, "3": 3, "4": 2, "5": 1},
            'spending_distribution': {"0-100": 10, "100-500": 5, "500-1000": 3, "1000-5000": 2, "5000+": 1},
            'average_stats': {
                'avg_purchase_frequency': 2.5,
                'avg_total_spent': 350.75,
                'avg_unique_products': 4.8
            }
        }

def get_shopping_sequences():
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            
            # Lấy các luật kết hợp
            cursor.execute("""
                SELECT TOP 20 antecedents, consequents, support, confidence, lift
                FROM association_rules
                ORDER BY confidence DESC
            """)
            
            rules = []
            for row in cursor.fetchall():
                rules.append({
                    'antecedents': row[0],
                    'consequents': row[1],
                    'support': float(row[2]),
                    'confidence': float(row[3]),
                    'lift': float(row[4])
                })
            
            conn.close()
            
            return {
                'rules': rules
            }
        return {'rules': []}
    except Exception as e:
        print(f"Lỗi truy vấn: {str(e)}")
        return {'rules': []}

def get_correlation_analysis():
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            
            # Lấy sản phẩm mua cùng nhau nhiều nhất
            cursor.execute("""
                SELECT TOP 15
                    fi.itemsets,
                    fi.support,
                    fi.itemset_length 
                FROM frequent_itemsets fi
                WHERE fi.itemset_length > 1
                ORDER BY fi.support DESC
            """)
            
            correlated_items = []
            for row in cursor.fetchall():
                correlated_items.append({
                    'itemsets': row[0],
                    'support': float(row[1]),
                    'item_count': int(row[2])
                })
            
            conn.close()
            
            return {
                'correlated_items': correlated_items
            }
        return {'correlated_items': []}
    except Exception as e:
        print(f"Lỗi truy vấn: {str(e)}")
        return {'correlated_items': []}

# Hàm lấy tất cả các mối liên hệ giữa sản phẩm chính và sản phẩm mua kèm
def get_all_product_associations():
    """
    Lấy tất cả các mối liên hệ giữa sản phẩm chính và sản phẩm mua kèm
    Trả về dictionary với key là tên sản phẩm chính và value là danh sách các sản phẩm mua kèm
    """
    try:
        conn = get_connection()
        if not conn:
            return {}
        
        cursor = conn.cursor()
        
        # Lấy tất cả các luật kết hợp với độ tin cậy cao
        cursor.execute("""
            SELECT antecedents, consequents, confidence, lift, support
            FROM association_rules
            WHERE confidence > 0.3
            ORDER BY confidence DESC
        """)
        
        # Dictionary lưu trữ kết quả
        product_associations = {}
        
        for row in cursor.fetchall():
            antecedent = row[0]  # Sản phẩm chính
            consequent = row[1]  # Sản phẩm mua kèm
            confidence = float(row[2])
            lift = float(row[3])
            support = float(row[4])
            
            # Nếu sản phẩm chính chưa có trong dictionary, thêm vào
            if antecedent not in product_associations:
                product_associations[antecedent] = []
            
            # Thêm sản phẩm mua kèm vào danh sách
            product_associations[antecedent].append({
                'related_product': consequent,
                'confidence': confidence,
                'lift': lift,
                'support': support
            })
        
        # Lấy thêm thông tin của tất cả sản phẩm
        cursor.execute("""
            SELECT Description, StockCode
            FROM products
        """)
        
        product_info = {}
        for row in cursor.fetchall():
            product_info[row[0]] = row[1]
        
        conn.close()
        
        return {
            'product_associations': product_associations,
            'product_info': product_info
        }
    except Exception as e:
        print(f"Lỗi khi lấy mối liên hệ sản phẩm: {str(e)}")
        return {'product_associations': {}, 'product_info': {}}

# === CHỨC NĂNG NGƯỜI DÙNG ===

def register_user(name, email, password):
    """
    Đăng ký người dùng mới
    """
    try:
        conn = get_connection()
        if not conn:
            return {'success': False, 'message': 'Không thể kết nối đến cơ sở dữ liệu'}
        
        cursor = conn.cursor()
        
        # Kiểm tra email đã tồn tại chưa
        cursor.execute("SELECT COUNT(*) FROM users WHERE email = ?", email)
        if cursor.fetchone()[0] > 0:
            conn.close()
            return {'success': False, 'message': 'Email này đã được đăng ký'}
        
        # Tạo password hash
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Thêm người dùng mới
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
        """, name, email, password_hash, datetime.datetime.now())
        
        conn.commit()
        
        # Lấy thông tin người dùng vừa tạo
        cursor.execute("SELECT user_id, name, email FROM users WHERE email = ?", email)
        user = cursor.fetchone()
        
        conn.close()
        
        if user:
            return {
                'success': True,
                'user': {
                    'user_id': user[0],
                    'name': user[1],
                    'email': user[2]
                }
            }
        else:
            return {'success': False, 'message': 'Không thể tạo người dùng'}
            
    except Exception as e:
        print(f"Lỗi khi đăng ký người dùng: {str(e)}")
        traceback.print_exc(file=sys.stdout)
        return {'success': False, 'message': str(e)}

def login_user(email, password):
    """
    Đăng nhập người dùng
    """
    try:
        conn = get_connection()
        if not conn:
            return {'success': False, 'message': 'Không thể kết nối đến cơ sở dữ liệu'}
        
        cursor = conn.cursor()
        
        # Kiểm tra email tồn tại
        cursor.execute("SELECT user_id, name, email, password_hash FROM users WHERE email = ?", email)
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return {'success': False, 'message': 'Email không tồn tại'}
        
        # Kiểm tra mật khẩu
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if user[3] != password_hash:
            conn.close()
            return {'success': False, 'message': 'Mật khẩu không đúng'}
        
        conn.close()
        
        return {
            'success': True,
            'user': {
                'user_id': user[0],
                'name': user[1],
                'email': user[2]
            }
        }
            
    except Exception as e:
        print(f"Lỗi khi đăng nhập: {str(e)}")
        traceback.print_exc(file=sys.stdout)
        return {'success': False, 'message': str(e)}

def get_user_by_id(user_id):
    """
    Lấy thông tin người dùng theo ID
    """
    try:
        conn = get_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id, name, email FROM users WHERE user_id = ?", user_id)
        user = cursor.fetchone()
        
        conn.close()
        
        if user:
            return {
                'user_id': user[0],
                'name': user[1],
                'email': user[2]
            }
        else:
            return None
            
    except Exception as e:
        print(f"Lỗi khi lấy thông tin người dùng: {str(e)}")
        return None

# === CHỨC NĂNG GIỎ HÀNG ===

def create_cart(user_id):
    """
    Tạo giỏ hàng mới cho người dùng
    """
    try:
        conn = get_connection()
        if not conn:
            return {'success': False, 'message': 'Không thể kết nối đến cơ sở dữ liệu'}
        
        cursor = conn.cursor()
        
        # Tạo giỏ hàng mới
        cursor.execute("""
            INSERT INTO carts (user_id, created_at)
            VALUES (?, ?)
        """, user_id, datetime.datetime.now())
        
        conn.commit()
        
        # Lấy ID giỏ hàng vừa tạo
        cursor.execute("SELECT @@IDENTITY AS cart_id")
        cart_id = int(cursor.fetchone()[0])
        
        conn.close()
        
        return {
            'success': True,
            'cart_id': cart_id
        }
            
    except Exception as e:
        print(f"Lỗi khi tạo giỏ hàng: {str(e)}")
        traceback.print_exc(file=sys.stdout)
        return {'success': False, 'message': str(e)}

def get_active_cart(user_id):
    """
    Lấy giỏ hàng đang hoạt động của người dùng hoặc tạo mới nếu chưa có
    """
    try:
        conn = get_connection()
        if not conn:
            return {'success': False, 'message': 'Không thể kết nối đến cơ sở dữ liệu'}
        
        cursor = conn.cursor()
        
        # Tìm giỏ hàng đang hoạt động (chưa được dùng trong đơn hàng nào)
        cursor.execute("""
            SELECT c.cart_id 
            FROM carts c
            LEFT JOIN orders o ON c.cart_id = o.cart_id
            WHERE c.user_id = ? AND o.order_id IS NULL
            ORDER BY c.created_at DESC
        """, user_id)
        
        cart = cursor.fetchone()
        
        if cart:
            cart_id = cart[0]
        else:
            # Nếu không có giỏ hàng nào, tạo mới
            cursor.execute("""
                INSERT INTO carts (user_id, created_at)
                VALUES (?, ?)
            """, user_id, datetime.datetime.now())
            
            conn.commit()
            
            cursor.execute("SELECT @@IDENTITY AS cart_id")
            cart_id = int(cursor.fetchone()[0])
        
        # Lấy các mặt hàng trong giỏ hàng
        cursor.execute("""
            SELECT ci.cart_item_id, ci.ProductId, ci.quantity, 
                   p.Description, p.MaxUnitPrice, p.ImagePath
            FROM cart_items ci
            JOIN products p ON ci.ProductId = p.ProductId
            WHERE ci.cart_id = ?
        """, cart_id)
        
        items = []
        for row in cursor.fetchall():
            items.append({
                'cart_item_id': int(row[0]),
                'product_id': int(row[1]),
                'quantity': int(row[2]),
                'description': row[3],
                'price': float(row[4]),
                'image_path': row[5],
                'total_price': float(row[4]) * int(row[2])
            })
        
        conn.close()
        
        return {
            'success': True,
            'cart_id': cart_id,
            'items': items,
            'total': sum(item['total_price'] for item in items)
        }
            
    except Exception as e:
        print(f"Lỗi khi lấy giỏ hàng: {str(e)}")
        traceback.print_exc(file=sys.stdout)
        return {'success': False, 'message': str(e)}

def add_to_cart(user_id, product_id, quantity):
    """
    Thêm sản phẩm vào giỏ hàng
    """
    try:
        conn = get_connection()
        if not conn:
            return {'success': False, 'message': 'Không thể kết nối đến cơ sở dữ liệu'}
        
        cursor = conn.cursor()
        
        # Lấy hoặc tạo giỏ hàng đang hoạt động
        result = get_active_cart(user_id)
        if not result['success']:
            conn.close()
            return result
        
        cart_id = result['cart_id']
        
        # Kiểm tra xem sản phẩm có tồn tại không
        cursor.execute("SELECT ProductId FROM products WHERE ProductId = ?", product_id)
        if not cursor.fetchone():
            conn.close()
            return {'success': False, 'message': 'Sản phẩm không tồn tại'}
        
        # Kiểm tra xem sản phẩm đã có trong giỏ hàng chưa
        cursor.execute("""
            SELECT cart_item_id, quantity 
            FROM cart_items 
            WHERE cart_id = ? AND ProductId = ?
        """, cart_id, product_id)
        
        cart_item = cursor.fetchone()
        
        if cart_item:
            # Cập nhật số lượng nếu sản phẩm đã có trong giỏ hàng
            new_quantity = int(cart_item[1]) + quantity
            
            if new_quantity <= 0:
                # Xóa sản phẩm khỏi giỏ hàng nếu số lượng <= 0
                cursor.execute("DELETE FROM cart_items WHERE cart_item_id = ?", cart_item[0])
            else:
                # Cập nhật số lượng
                cursor.execute("""
                    UPDATE cart_items 
                    SET quantity = ? 
                    WHERE cart_item_id = ?
                """, new_quantity, cart_item[0])
        else:
            # Thêm sản phẩm mới vào giỏ hàng
            if quantity > 0:
                cursor.execute("""
                    INSERT INTO cart_items (cart_id, ProductId, quantity)
                    VALUES (?, ?, ?)
                """, cart_id, product_id, quantity)
        
        conn.commit()
        conn.close()
        
        # Trả về giỏ hàng đã cập nhật
        return get_active_cart(user_id)
            
    except Exception as e:
        print(f"Lỗi khi thêm sản phẩm vào giỏ hàng: {str(e)}")
        traceback.print_exc(file=sys.stdout)
        return {'success': False, 'message': str(e)}

def update_cart_item(user_id, cart_item_id, quantity):
    """
    Cập nhật số lượng của một mục trong giỏ hàng
    """
    try:
        conn = get_connection()
        if not conn:
            return {'success': False, 'message': 'Không thể kết nối đến cơ sở dữ liệu'}
        
        cursor = conn.cursor()
        
        # Kiểm tra quyền truy cập vào cart_item
        cursor.execute("""
            SELECT ci.cart_item_id
            FROM cart_items ci
            JOIN carts c ON ci.cart_id = c.cart_id
            WHERE ci.cart_item_id = ? AND c.user_id = ?
        """, cart_item_id, user_id)
        
        if not cursor.fetchone():
            conn.close()
            return {'success': False, 'message': 'Không có quyền truy cập vào mục này hoặc mục không tồn tại'}
        
        if quantity <= 0:
            # Xóa mục khỏi giỏ hàng
            cursor.execute("DELETE FROM cart_items WHERE cart_item_id = ?", cart_item_id)
        else:
            # Cập nhật số lượng
            cursor.execute("""
                UPDATE cart_items 
                SET quantity = ? 
                WHERE cart_item_id = ?
            """, quantity, cart_item_id)
        
        conn.commit()
        conn.close()
        
        # Trả về giỏ hàng đã cập nhật
        return get_active_cart(user_id)
            
    except Exception as e:
        print(f"Lỗi khi cập nhật giỏ hàng: {str(e)}")
        traceback.print_exc(file=sys.stdout)
        return {'success': False, 'message': str(e)}

def remove_from_cart(user_id, cart_item_id):
    """
    Xóa sản phẩm khỏi giỏ hàng
    """
    try:
        # Chỉ đơn giản là cập nhật số lượng về 0, điều này sẽ xóa mục khỏi giỏ hàng
        return update_cart_item(user_id, cart_item_id, 0)
            
    except Exception as e:
        print(f"Lỗi khi xóa sản phẩm khỏi giỏ hàng: {str(e)}")
        traceback.print_exc(file=sys.stdout)
        return {'success': False, 'message': str(e)}

# === CHỨC NĂNG ĐƠN HÀNG ===

def create_order(user_id):
    """
    Tạo đơn hàng mới từ giỏ hàng hiện tại
    """
    try:
        conn = get_connection()
        if not conn:
            return {'success': False, 'message': 'Không thể kết nối đến cơ sở dữ liệu'}
        
        cursor = conn.cursor()
        
        # Lấy giỏ hàng đang hoạt động
        result = get_active_cart(user_id)
        if not result['success']:
            conn.close()
            return result
        
        cart_id = result['cart_id']
        cart_items = result['items']
        total_amount = result['total']
        
        # Kiểm tra giỏ hàng có sản phẩm không
        if not cart_items:
            conn.close()
            return {'success': False, 'message': 'Giỏ hàng trống, không thể tạo đơn hàng'}
        
        # Tạo đơn hàng mới - bỏ trường status
        cursor.execute("""
            INSERT INTO orders (user_id, cart_id, total_amount, created_at)
            VALUES (?, ?, ?, ?)
        """, user_id, cart_id, total_amount, datetime.datetime.now())
        
        conn.commit()
        
        # Lấy ID đơn hàng vừa tạo
        cursor.execute("SELECT @@IDENTITY AS order_id")
        order_id = int(cursor.fetchone()[0])
        
        # Thêm các mục vào chi tiết đơn hàng
        for item in cart_items:
            cursor.execute("""
                INSERT INTO order_items (order_id, ProductId, product_name, quantity, price)
                VALUES (?, ?, ?, ?, ?)
            """, order_id, item['product_id'], item['description'], item['quantity'], item['price'])
        
        conn.commit()
        conn.close()
        
        # Trả về thông tin đơn hàng vừa tạo
        return {
            'success': True,
            'order_id': order_id,
            'total_amount': total_amount,
            'items': cart_items
        }
            
    except Exception as e:
        print(f"Lỗi khi tạo đơn hàng: {str(e)}")
        traceback.print_exc(file=sys.stdout)
        return {'success': False, 'message': str(e)}

def get_order(user_id, order_id):
    """
    Lấy thông tin chi tiết đơn hàng
    """
    try:
        conn = get_connection()
        if not conn:
            return {'success': False, 'message': 'Không thể kết nối đến cơ sở dữ liệu'}
        
        cursor = conn.cursor()
        
        # Lấy thông tin đơn hàng - đã loại bỏ trường status
        cursor.execute("""
            SELECT order_id, total_amount, created_at
            FROM orders
            WHERE order_id = ? AND user_id = ?
        """, order_id, user_id)
        
        order_info = cursor.fetchone()
        
        if not order_info:
            conn.close()
            return {'success': False, 'message': 'Đơn hàng không tồn tại hoặc không có quyền truy cập'}
        
        # Lấy chi tiết các mục trong đơn hàng
        cursor.execute("""
            SELECT oi.order_item_id, oi.ProductId, oi.product_name, oi.quantity, oi.price,
                   p.ImagePath
            FROM order_items oi
            LEFT JOIN products p ON oi.ProductId = p.ProductId
            WHERE oi.order_id = ?
        """, order_id)
        
        items = []
        for row in cursor.fetchall():
            items.append({
                'order_item_id': int(row[0]),
                'product_id': int(row[1]),
                'product_name': row[2],
                'quantity': int(row[3]),
                'price': float(row[4]),
                'image_path': row[5],
                'total_price': float(row[4]) * int(row[3])
            })
        
        conn.close()
        
        return {
            'success': True,
            'order_id': order_info[0],
            'total_amount': float(order_info[1]),
            'status': 'completed',  # Thêm status mặc định
            'created_at': order_info[2],
            'items': items
        }
            
    except Exception as e:
        print(f"Lỗi khi lấy thông tin đơn hàng: {str(e)}")
        traceback.print_exc(file=sys.stdout)
        return {'success': False, 'message': str(e)}

def get_user_orders(user_id):
    """
    Lấy danh sách đơn hàng của người dùng
    """
    try:
        conn = get_connection()
        if not conn:
            return {'success': False, 'message': 'Không thể kết nối đến cơ sở dữ liệu'}
        
        cursor = conn.cursor()
        
        # Lấy danh sách đơn hàng - đã loại bỏ trường status
        cursor.execute("""
            SELECT order_id, total_amount, created_at
            FROM orders
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, user_id)
        
        orders = []
        for row in cursor.fetchall():
            orders.append({
                'order_id': int(row[0]),
                'total_amount': float(row[1]),
                'created_at': row[2],
                'status': 'completed'  # Thêm status mặc định là 'completed'
            })
        
        conn.close()
        
        return {
            'success': True,
            'orders': orders
        }
            
    except Exception as e:
        print(f"Lỗi khi lấy danh sách đơn hàng: {str(e)}")
        traceback.print_exc(file=sys.stdout)
        return {'success': False, 'message': str(e)}

def update_order_status(order_id, status):
    """
    Cập nhật trạng thái đơn hàng (chức năng cho admin)
    """
    try:
        conn = get_connection()
        if not conn:
            return {'success': False, 'message': 'Không thể kết nối đến cơ sở dữ liệu'}
        
        cursor = conn.cursor()
        
        # Cập nhật trạng thái
        cursor.execute("""
            UPDATE orders
            SET status = ?
            WHERE order_id = ?
        """, status, order_id)
        
        conn.commit()
        
        # Kiểm tra xem có đơn hàng nào được cập nhật không
        if cursor.rowcount == 0:
            conn.close()
            return {'success': False, 'message': 'Đơn hàng không tồn tại'}
        
        conn.close()
        
        return {
            'success': True,
            'message': f'Đã cập nhật trạng thái đơn hàng thành {status}'
        }
            
    except Exception as e:
        print(f"Lỗi khi cập nhật trạng thái đơn hàng: {str(e)}")
        traceback.print_exc(file=sys.stdout)
        return {'success': False, 'message': str(e)}