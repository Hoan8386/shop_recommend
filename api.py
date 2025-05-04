from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import time
import jwt
import datetime
from functools import wraps
from db_connection import (get_cleaned_products, get_connection, get_product_statistics, 
                          get_shopping_behavior, get_correlation_analysis, get_shopping_sequences, get_products,
                          register_user, login_user, get_user_by_id, get_active_cart, add_to_cart, 
                          update_cart_item, remove_from_cart, create_order, get_order, get_user_orders,
                          search_products, get_product_recommendations)

app = Flask(__name__)

# Thêm SECRET_KEY cho JWT token
app.config['SECRET_KEY'] = 'your_super_secret_key_here'

# Cấu hình CORS đơn giản
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])

# Bộ nhớ đệm (cache) cho recommend_for_product_api
recommendation_cache = {}
# Thời gian hết hạn cache (1 giờ)
CACHE_EXPIRY = 3600

# === MIDDLEWARE XÁC THỰC TOKEN ===
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Kiểm tra token trong header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token không tồn tại!', 'success': False}), 401
        
        try:
            # Giải mã token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = get_user_by_id(data['user_id'])
            
            if not current_user:
                return jsonify({'message': 'Token không hợp lệ!', 'success': False}), 401
                
        except Exception as e:
            print(f"Lỗi xác thực token: {str(e)}")
            return jsonify({'message': 'Token không hợp lệ!', 'success': False}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated

@app.route('/api/cleaned-products', methods=['GET'])
def api_cleaned_products():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 12))
    
    result = get_cleaned_products(page, per_page)
    return jsonify(result)

@app.route('/')
def home():
    return 'Welcome to the Enhanced Online Retail API!'

@app.route('/product-statistics', methods=['GET'])
def product_statistics_api():
    try:
        result = get_product_statistics()
        # Kiểm tra cấu trúc dữ liệu mới
        if not result or (
            'total_products' not in result or 
            'total_customers' not in result or 
            'total_transactions' not in result or 
            'top_products_by_quantity' not in result or 
            len(result['top_products_by_quantity']) == 0
        ):
            return jsonify({'error': 'Không thể lấy dữ liệu thống kê sản phẩm.'}), 500
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Đã xảy ra lỗi: {str(e)}'}), 500

@app.route('/shopping-behavior', methods=['GET'])
def shopping_behavior_api():
    try:
        result = get_shopping_behavior()
        # Kiểm tra cấu trúc dữ liệu mới
        if not result or (
            'purchase_by_country' not in result or 
            'avg_order_by_country' not in result or 
            'purchase_frequency_distribution' not in result or 
            'spending_distribution' not in result or 
            'average_stats' not in result
        ):
            return jsonify({'error': 'Không thể lấy dữ liệu hành vi mua sắm.'}), 500
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Đã xảy ra lỗi: {str(e)}'}), 500

@app.route('/shopping-sequences', methods=['GET'])
def shopping_sequences_api():
    try:
        result = get_shopping_sequences()
        if not result or len(result['rules']) == 0:
            return jsonify({'error': 'Không thể lấy dữ liệu chuỗi mua sắm.'}), 500
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Đã xảy ra lỗi: {str(e)}'}), 500

@app.route('/correlation-analysis', methods=['GET'])
def correlation_analysis_api():
    try:
        result = get_correlation_analysis()
        if not result or len(result['correlated_items']) == 0:
            return jsonify({'error': 'Không thể lấy dữ liệu phân tích tương quan.'}), 500
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Đã xảy ra lỗi: {str(e)}'}), 500

@app.route('/common-shopping-patterns', methods=['GET'])
def common_shopping_patterns_api():
    try:
        # Sử dụng lại dữ liệu từ shopping_sequences
        result = get_shopping_sequences()
        if not result or len(result['rules']) == 0:
            return jsonify({'error': 'Không thể lấy dữ liệu mẫu mua sắm phổ biến.'}), 500
        
        # Chuyển đổi dữ liệu để phù hợp với mong đợi của frontend
        patterns = []
        for rule in result['rules']:
            patterns.append({
                'mua_truoc': rule['antecedents'],
                'mua_sau': rule['consequents'],
                'ho_tro': rule['support'],
                'do_tin_cay': rule['confidence'],
                'do_nang': rule['lift']
            })
        
        return jsonify(patterns)
    except Exception as e:
        return jsonify({'error': f'Đã xảy ra lỗi: {str(e)}'}), 500

@app.route('/frequently-bought-together', methods=['GET'])
def frequently_bought_together_api():
    try:
        # Sử dụng lại dữ liệu từ correlation_analysis
        result = get_correlation_analysis()
        if not result or len(result['correlated_items']) == 0:
            return jsonify({'error': 'Không thể lấy dữ liệu sản phẩm thường được mua cùng nhau.'}), 500
        
        # Chuyển đổi dữ liệu để phù hợp với mong đợi của frontend
        items = []
        for item in result['correlated_items']:
            # Tách chuỗi itemsets thành các sản phẩm riêng lẻ
            products = item['itemsets'].split(',')
            if len(products) >= 2:
                items.append({
                    'san_pham_1': products[0].strip(),
                    'san_pham_2': products[1].strip(),
                    'so_lan_mua_chung': int(item['support'] * 1000)  # Nhân với 1000 để có số ước lượng
                })
        
        return jsonify(items)
    except Exception as e:
        return jsonify({'error': f'Đã xảy ra lỗi: {str(e)}'}), 500

@app.route('/recommendation', methods=['GET'])
def recommendation_api():
    try:
        # Lấy dữ liệu từ shopping_sequences và correlation_analysis
        sequences = get_shopping_sequences()
        correlations = get_correlation_analysis()
        
        if (not sequences or len(sequences['rules']) == 0) and (not correlations or len(correlations['correlated_items']) == 0):
            return jsonify({'error': 'Không thể lấy dữ liệu gợi ý.'}), 500
        
        # Dữ liệu luật kết hợp từ sequences
        association_rules = []
        for rule in sequences['rules']:
            association_rules.append({
                'antecedents': rule['antecedents'],
                'consequents': rule['consequents'],
                'support': rule['support'],
                'confidence': rule['confidence'],
                'lift': rule['lift']
            })
        
        # Dữ liệu tập phổ biến từ correlations
        frequent_itemsets = []
        for item in correlations['correlated_items']:
            frequent_itemsets.append({
                'itemsets': item['itemsets'],
                'support': item['support'],
                'itemset_length': item['item_count']
            })
        
        return jsonify({
            'association_rules': association_rules,
            'frequent_itemsets': frequent_itemsets
        })
    except Exception as e:
        return jsonify({'error': f'Đã xảy ra lỗi: {str(e)}'}), 500

@app.route('/api/recommend-for-product/<product>', methods=['GET'])
@app.route('/recommend-for-product/<product>', methods=['GET'])
def recommend_for_product_api(product):
    try:
        # Kiểm tra cache
        cache_key = product
        current_time = time.time()
        
        # Nếu kết quả đã được cache và chưa hết hạn, trả về từ cache
        if cache_key in recommendation_cache and current_time - recommendation_cache[cache_key]['timestamp'] < CACHE_EXPIRY:
            print(f"Trả về gợi ý từ cache cho sản phẩm: {product}")
            return jsonify(recommendation_cache[cache_key]['data'])

        # Nếu không có trong cache hoặc đã hết hạn, tính toán mới
        print(f"Tính toán gợi ý mới cho sản phẩm: {product}")
        
        # Thử phương pháp nhanh nhất trước: Tìm luật kết hợp từ bảng association_rules
        conn = get_connection()
        if not conn:
            return jsonify({'recommendations': []}), 500
        
        cursor = conn.cursor()
        
        # Phương pháp 1: Tìm kiếm trực tiếp từ bảng luật kết hợp đã được tính sẵn
        cursor.execute("""
            SELECT 
                consequents, 
                confidence, 
                support, 
                lift
            FROM association_rules
            WHERE antecedents LIKE ? AND lift > 1
            ORDER BY lift DESC
        """, f'%{product}%')
        
        rule_results = cursor.fetchall()
        
        if rule_results and len(rule_results) > 0:
            # Nếu tìm thấy luật kết hợp, sử dụng để tạo gợi ý
            recommendations = []
            
            # Lấy các sản phẩm từ luật kết hợp
            for row in rule_results:
                consequent = row[0]
                confidence = float(row[1])
                support = float(row[2])
                lift = float(row[3])
                
                # Lấy thông tin chi tiết về sản phẩm gợi ý
                cursor.execute("""
                    SELECT 
                        ProductId, 
                        StockCode, 
                        Description, 
                        MaxUnitPrice AS UnitPrice, 
                        TotalQuantitySold, 
                        ImagePath
                    FROM products
                    WHERE Description = ?
                """, consequent)
                
                product_info = cursor.fetchone()
                
                if product_info:
                    recommendations.append({
                        'Description': product_info[2],
                        'confidence': confidence,
                        'support': support,
                        'lift': lift,
                        'InvoiceNo': 0,  # Không cần thiết cho hiển thị
                        'Quantity': int(product_info[4]),
                        'ImagePath': product_info[5],
                        'UnitPrice': float(product_info[3])
                    })
            
            conn.close()
            
            if recommendations:
                # Lưu vào cache
                result = {'recommendations': recommendations[:10]}
                recommendation_cache[cache_key] = {
                    'data': result,
                    'timestamp': current_time
                }
                return jsonify(result)
        
        # Nếu không tìm thấy từ bảng luật kết hợp, sử dụng phương pháp tính toán
        # Tìm các sản phẩm thường được mua cùng với sản phẩm hiện tại
        cursor.execute("""
            SELECT DISTINCT InvoiceNo 
            FROM cleaned_retail_data
            WHERE Description LIKE ?
        """, f'%{product}%')
        
        invoices = [row[0] for row in cursor.fetchall()]
        
        if not invoices:
            # Nếu không tìm thấy hóa đơn nào chứa sản phẩm này, chuyển sang phương pháp thay thế
            conn.close()
            return fallback_recommendations(product)
        
        # Tối ưu hóa: Sử dụng một truy vấn duy nhất để lấy tất cả thông tin cần thiết
        placeholders = ','.join(['?'] * len(invoices))
        query = f"""
            SELECT 
                d.Description,
                COUNT(*) as frequency,
                COUNT(DISTINCT d.InvoiceNo) as transaction_count,
                p.MaxUnitPrice,
                p.TotalQuantitySold,
                p.ImagePath
            FROM cleaned_retail_data d
            JOIN products p ON d.Description = p.Description
            WHERE d.InvoiceNo IN ({placeholders})
            AND d.Description <> ?
            GROUP BY d.Description, p.MaxUnitPrice, p.TotalQuantitySold, p.ImagePath
            ORDER BY frequency DESC, transaction_count DESC
        """
        
        # Thêm product vào cuối danh sách tham số
        cursor.execute(query, invoices + [product])
        
        # Lấy tổng số giao dịch để tính support
        cursor.execute("SELECT COUNT(DISTINCT InvoiceNo) FROM cleaned_retail_data")
        total_transactions = int(cursor.fetchone()[0])
        
        # Lấy số lượng giao dịch chứa sản phẩm hiện tại để tính support_x
        support_x = len(invoices) / total_transactions
        
        # Tối ưu: Tính toán một lần cho tất cả các sản phẩm
        recommendations = []
        added_products = set()  # Để đảm bảo không có sản phẩm trùng lặp
        
        for row in cursor.fetchall():
            description = row[0]
            frequency = row[1]
            transaction_count = row[2]
            price = float(row[3]) if row[3] else 0
            quantity = int(row[4]) if row[4] else 0
            image_path = row[5]
            
            # Tránh trùng lặp
            if description in added_products:
                continue
                
            added_products.add(description)
            
            # Tính toán các chỉ số theo cùng một cách như trước
            support_y = transaction_count / total_transactions  # Support của sản phẩm Y
            support_xy = transaction_count / total_transactions  # Support của X và Y cùng nhau
            
            # Confidence: P(Y|X) = P(X,Y)/P(X)
            confidence = support_xy / support_x if support_x > 0 else 0
            
            # Lift: P(Y|X)/P(Y) = P(X,Y)/(P(X)*P(Y))
            lift = support_xy / (support_x * support_y) if (support_x * support_y) > 0 else 1.0
            
            # Chỉ lấy các sản phẩm có lift > 1 (có mối liên kết tích cực)
            if lift > 1.0:
                recommendations.append({
                    'Description': description,
                    'confidence': confidence,
                    'support': support_xy,
                    'lift': lift,
                    'InvoiceNo': transaction_count,
                    'Quantity': quantity,
                    'ImagePath': image_path,
                    'UnitPrice': price
                })
        
        conn.close()
        
        # Sắp xếp theo lift giảm dần
        recommendations.sort(key=lambda x: x['lift'], reverse=True)
        
        if recommendations:
            # Lưu vào cache
            result = {'recommendations': recommendations[:10]}
            recommendation_cache[cache_key] = {
                'data': result,
                'timestamp': current_time
            }
            return jsonify(result)
        else:
            # Nếu không tìm thấy gợi ý có lift > 1, sử dụng phương pháp thay thế
            return fallback_recommendations(product)
    except Exception as e:
        print(f"Lỗi khi tạo gợi ý sản phẩm: {str(e)}")
        return jsonify({'error': f'Đã xảy ra lỗi: {str(e)}'}), 500

def fallback_recommendations(product):
    """
    Phương pháp thay thế để tạo gợi ý khi không tìm thấy luật kết hợp
    """
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            
            # Lấy tổng số giao dịch để tính toán
            cursor.execute("SELECT COUNT(DISTINCT InvoiceNo) FROM cleaned_retail_data")
            total_transactions = int(cursor.fetchone()[0])
            
            # Lấy thông tin sản phẩm hiện tại để tìm sản phẩm tương tự
            # Tách các từ trong tên sản phẩm
            words = product.split()
            
            # Nếu sản phẩm có ít nhất 2 từ, tìm sản phẩm có chứa 1 trong các từ này
            if len(words) >= 2:
                # Tạo mệnh đề LIKE cho mỗi từ
                like_clauses = []
                for word in words:
                    if len(word) > 3:  # Chỉ sử dụng từ có độ dài > 3 để tránh từ không có ý nghĩa
                        like_clauses.append(f"Description LIKE '%{word}%'")
                
                if like_clauses:
                    # Tạo câu truy vấn với các mệnh đề LIKE được nối bằng OR
                    query = f"""
                        SELECT TOP 10
                            ProductId,
                            StockCode,
                            Description,
                            MaxUnitPrice,
                            TotalQuantitySold,
                            ImagePath
                        FROM products 
                        WHERE Description <> ? AND ({' OR '.join(like_clauses)})
                        ORDER BY TotalQuantitySold DESC
                    """
                    
                    cursor.execute(query, product)
                    
                    recommendations = []
                    for row in cursor.fetchall():
                        description = row[2]
                        
                        # Tính toán thực tế dựa trên dữ liệu thay vì hardcode
                        # Lấy số giao dịch chứa sản phẩm product
                        cursor.execute("""
                            SELECT COUNT(DISTINCT InvoiceNo) 
                            FROM cleaned_retail_data
                            WHERE Description = ?
                        """, product)
                        product_transactions = int(cursor.fetchone()[0])
                        
                        # Lấy số giao dịch chứa sản phẩm gợi ý
                        cursor.execute("""
                            SELECT COUNT(DISTINCT InvoiceNo) 
                            FROM cleaned_retail_data
                            WHERE Description = ?
                        """, description)
                        rec_transactions = int(cursor.fetchone()[0])
                        
                        # Lấy số giao dịch chứa cả hai sản phẩm
                        cursor.execute("""
                            SELECT COUNT(DISTINCT a.InvoiceNo)
                            FROM cleaned_retail_data a
                            JOIN cleaned_retail_data b ON a.InvoiceNo = b.InvoiceNo
                            WHERE a.Description = ? AND b.Description = ?
                        """, product, description)
                        common_transactions = int(cursor.fetchone()[0])
                        
                        # Tính toán các chỉ số Apriori
                        support_x = product_transactions / total_transactions
                        support_y = rec_transactions / total_transactions
                        support_xy = common_transactions / total_transactions
                        
                        # Confidence: P(Y|X) = P(X,Y)/P(X)
                        confidence = support_xy / support_x if support_x > 0 else 0.1
                        
                        # Lift: P(Y|X)/P(Y) = P(X,Y)/(P(X)*P(Y))
                        lift = support_xy / (support_x * support_y) if (support_x * support_y) > 0 else 1.0
                        
                        recommendations.append({
                            'Description': description,
                            'confidence': confidence,
                            'support': support_xy,
                            'lift': lift,
                            'InvoiceNo': rec_transactions,
                            'Quantity': int(row[4]),
                            'ImagePath': row[5] if row[5] else f'imagesProduct/{description}.jpg',
                            'UnitPrice': float(row[3]) if row[3] else 0
                        })
                    
                    if recommendations:
                        conn.close()
                        return jsonify({'recommendations': recommendations})
            
            # Nếu không tìm được theo từ hoặc sản phẩm chỉ có 1 từ, lấy các sản phẩm bán chạy
            cursor.execute("""
                SELECT TOP 10
                    ProductId,
                    StockCode,
                    Description,
                    MaxUnitPrice,
                    TotalQuantitySold,
                    ImagePath
                FROM products
                WHERE Description <> ?
                ORDER BY TotalQuantitySold DESC
            """, product)
            
            recommendations = []
            for row in cursor.fetchall():
                description = row[2]
                
                # Tính toán thực tế dựa trên dữ liệu thay vì hardcode
                # Lấy số giao dịch chứa sản phẩm product
                cursor.execute("""
                    SELECT COUNT(DISTINCT InvoiceNo) 
                    FROM cleaned_retail_data
                    WHERE Description = ?
                """, product)
                product_transactions = int(cursor.fetchone()[0])
                
                # Lấy số giao dịch chứa sản phẩm gợi ý
                cursor.execute("""
                    SELECT COUNT(DISTINCT InvoiceNo) 
                    FROM cleaned_retail_data
                    WHERE Description = ?
                """, description)
                rec_transactions = int(cursor.fetchone()[0])
                
                # Lấy số giao dịch chứa cả hai sản phẩm
                cursor.execute("""
                    SELECT COUNT(DISTINCT a.InvoiceNo)
                    FROM cleaned_retail_data a
                    JOIN cleaned_retail_data b ON a.InvoiceNo = b.InvoiceNo
                    WHERE a.Description = ? AND b.Description = ?
                """, product, description)
                common_transactions = int(cursor.fetchone()[0])
                
                # Tính toán các chỉ số Apriori
                support_x = product_transactions / total_transactions
                support_y = rec_transactions / total_transactions
                support_xy = common_transactions / total_transactions
                
                # Confidence: P(Y|X) = P(X,Y)/P(X)
                confidence = support_xy / support_x if support_x > 0 else 0.1
                
                # Lift: P(Y|X)/P(Y) = P(X,Y)/(P(X)*P(Y))
                lift = support_xy / (support_x * support_y) if (support_x * support_y) > 0 else 1.0
                
                recommendations.append({
                    'Description': description,
                    'confidence': confidence,
                    'support': support_xy,
                    'lift': lift,
                    'InvoiceNo': rec_transactions,
                    'Quantity': int(row[4]),
                    'ImagePath': row[5] if row[5] else f'imagesProduct/{description}.jpg',
                    'UnitPrice': float(row[3]) if row[3] else 0
                })
            
            conn.close()
            return jsonify({'recommendations': recommendations})
        
        return jsonify({'recommendations': []})
    except Exception as e:
        print(f"Lỗi trong phương pháp thay thế: {str(e)}")
        return jsonify({'recommendations': []})

@app.route('/api/best-sellers', methods=['GET'])
def best_sellers_api():
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            
            # Lấy danh sách sản phẩm bán chạy nhất (Top 8)
            cursor.execute("""
                SELECT TOP 8 
                    p.StockCode,
                    p.Description,
                    p.MaxUnitPrice as UnitPrice,
                    p.TotalQuantitySold as Quantity,
                    p.TotalRevenue,
                    p.NumberOfTransactions,
                    p.ImagePath
                FROM products p
                ORDER BY p.TotalQuantitySold DESC
            """)
            
            products = []
            for row in cursor.fetchall():
                products.append({
                    'StockCode': row[0],
                    'Description': row[1],
                    'UnitPrice': float(row[2]),
                    'Quantity': int(row[3]),
                    'TotalRevenue': float(row[4]),
                    'NumberOfTransactions': int(row[5]),
                    'ImagePath': row[6]
                })
            
            conn.close()
            
            return jsonify({
                'products': products,
                'success': True
            })
        return jsonify({'products': [], 'success': False, 'message': 'Không thể kết nối đến cơ sở dữ liệu'})
    except Exception as e:
        print(f"Lỗi khi lấy sản phẩm bán chạy: {str(e)}")
        return jsonify({'products': [], 'success': False, 'message': f'Đã xảy ra lỗi: {str(e)}'})

@app.route('/api/products', methods=['GET'])
def all_products_api():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 12))
        
        result = get_products(page, per_page)
        return jsonify(result)
    except Exception as e:
        print(f"Lỗi khi lấy danh sách sản phẩm: {str(e)}")
        return jsonify({
            'products': [], 
            'total': 0, 
            'page': 1, 
            'per_page': 12, 
            'total_pages': 0, 
            'success': False, 
            'message': f'Đã xảy ra lỗi: {str(e)}'
        })

@app.route('/api/product-info', methods=['GET'])
def product_info_api():
    try:
        description = request.args.get('description')
        if not description:
            return jsonify({'error': 'Missing description parameter'}), 400
            
        conn = get_connection()
        if not conn:
            return jsonify({'error': 'Không thể kết nối đến cơ sở dữ liệu'}), 500
            
        cursor = conn.cursor()
        
        # Tìm thông tin sản phẩm dựa trên Description
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
            WHERE Description = ?
        """, description)
        
        row = cursor.fetchone()
        
        if not row:
            # Thử tìm kiếm một phần của Description
            cursor.execute("""
                SELECT TOP 1
                    ProductId,
                    StockCode,
                    Description,
                    MaxUnitPrice AS UnitPrice,
                    TotalQuantitySold AS Quantity,
                    TotalRevenue,
                    NumberOfTransactions,
                    ImagePath
                FROM products
                WHERE Description LIKE ?
                ORDER BY TotalQuantitySold DESC
            """, f'%{description}%')
            
            row = cursor.fetchone()
            
        if row:
            product = {
                'ProductId': int(row[0]),
                'StockCode': row[1],
                'Description': row[2],
                'UnitPrice': float(row[3]),
                'Quantity': int(row[4]),
                'TotalRevenue': float(row[5]),
                'NumberOfTransactions': int(row[6]),
                'ImagePath': row[7]
            }
            
            conn.close()
            return jsonify({'product': product, 'success': True})
        
        conn.close()
        return jsonify({'product': None, 'success': False, 'message': 'Không tìm thấy sản phẩm'}), 404
    except Exception as e:
        print(f"Lỗi khi lấy thông tin sản phẩm: {str(e)}")
        return jsonify({'product': None, 'success': False, 'message': f'Đã xảy ra lỗi: {str(e)}'}), 500

# === API ĐĂNG KÝ VÀ ĐĂNG NHẬP ===
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'Không có dữ liệu!', 'success': False}), 400
    
    # Kiểm tra dữ liệu đầu vào
    required_fields = ['name', 'email', 'password']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'message': f'Thiếu thông tin {field}!', 'success': False}), 400
    
    # Gọi hàm đăng ký
    result = register_user(data['name'], data['email'], data['password'])
    
    if not result['success']:
        return jsonify(result), 400
    
    # Tạo token
    token = jwt.encode({
        'user_id': result['user']['user_id'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    return jsonify({
        'message': 'Đăng ký thành công!',
        'success': True,
        'token': token,
        'user': result['user']
    })

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'Không có dữ liệu!', 'success': False}), 400
    
    # Kiểm tra dữ liệu đầu vào
    required_fields = ['email', 'password']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'message': f'Thiếu thông tin {field}!', 'success': False}), 400
    
    # Gọi hàm đăng nhập
    result = login_user(data['email'], data['password'])
    
    if not result['success']:
        return jsonify(result), 401
    
    # Tạo token
    token = jwt.encode({
        'user_id': result['user']['user_id'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    return jsonify({
        'message': 'Đăng nhập thành công!',
        'success': True,
        'token': token,
        'user': result['user']
    })

@app.route('/api/profile', methods=['GET'])
@token_required
def api_profile(current_user):
    return jsonify({
        'success': True,
        'user': current_user
    })

# === API QUẢN LÝ GIỎ HÀNG ===
@app.route('/api/cart', methods=['GET'])
@token_required
def get_cart(current_user):
    """
    Lấy thông tin giỏ hàng hiện tại của người dùng
    """
    result = get_active_cart(current_user['user_id'])
    return jsonify(result)

@app.route('/api/cart/add', methods=['POST'])
@token_required
def add_cart_item(current_user):
    """
    Thêm sản phẩm vào giỏ hàng
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'Không có dữ liệu!', 'success': False}), 400
    
    # Kiểm tra dữ liệu đầu vào
    required_fields = ['product_id', 'quantity']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Thiếu thông tin {field}!', 'success': False}), 400
    
    # Đảm bảo quantity là số nguyên dương
    try:
        quantity = int(data['quantity'])
        if quantity <= 0:
            return jsonify({'message': 'Số lượng phải lớn hơn 0!', 'success': False}), 400
    except:
        return jsonify({'message': 'Số lượng không hợp lệ!', 'success': False}), 400
    
    # Gọi hàm thêm sản phẩm vào giỏ hàng
    result = add_to_cart(current_user['user_id'], data['product_id'], quantity)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400

@app.route('/api/cart/update', methods=['PUT'])
@token_required
def update_cart(current_user):
    """
    Cập nhật số lượng sản phẩm trong giỏ hàng
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'Không có dữ liệu!', 'success': False}), 400
    
    # Kiểm tra dữ liệu đầu vào
    required_fields = ['cart_item_id', 'quantity']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Thiếu thông tin {field}!', 'success': False}), 400
    
    # Gọi hàm cập nhật giỏ hàng
    result = update_cart_item(current_user['user_id'], data['cart_item_id'], data['quantity'])
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400

@app.route('/api/cart/remove', methods=['DELETE'])
@token_required
def remove_cart_item(current_user):
    """
    Xóa sản phẩm khỏi giỏ hàng
    """
    cart_item_id = request.args.get('cart_item_id')
    
    if not cart_item_id:
        return jsonify({'message': 'Thiếu thông tin cart_item_id!', 'success': False}), 400
    
    # Gọi hàm xóa sản phẩm khỏi giỏ hàng
    result = remove_from_cart(current_user['user_id'], cart_item_id)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400

# === API QUẢN LÝ ĐƠN HÀNG ===
@app.route('/api/orders', methods=['GET'])
@token_required
def get_orders_list(current_user):
    """
    Lấy danh sách đơn hàng của người dùng
    """
    result = get_user_orders(current_user['user_id'])
    return jsonify(result)

@app.route('/api/orders/<int:order_id>', methods=['GET'])
@token_required
def get_order_detail(current_user, order_id):
    """
    Lấy thông tin chi tiết một đơn hàng
    """
    try:
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Không thể kết nối đến cơ sở dữ liệu'}), 500
        
        cursor = conn.cursor()
        
        # Lấy thông tin đơn hàng - đã xóa trường status
        cursor.execute("""
            SELECT order_id, total_amount, created_at
            FROM orders
            WHERE order_id = ? AND user_id = ?
        """, order_id, current_user['user_id'])
        
        order_info = cursor.fetchone()
        
        if not order_info:
            conn.close()
            return jsonify({'success': False, 'message': 'Đơn hàng không tồn tại hoặc không có quyền truy cập'}), 404
        
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
        
        return jsonify({
            'success': True,
            'order_id': order_info[0],
            'total_amount': float(order_info[1]),
            'created_at': order_info[2],
            'items': items
        })
            
    except Exception as e:
        print(f"Lỗi khi lấy thông tin đơn hàng: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/orders/create', methods=['POST'])
@token_required
def create_new_order(current_user):
    """
    Tạo đơn hàng mới từ giỏ hàng hiện tại
    """
    result = create_order(current_user['user_id'])
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400

# === API TÌM KIẾM ===
@app.route('/api/search', methods=['GET'])
def search_products_api():
    """
    Tìm kiếm sản phẩm theo từ khóa
    """
    query = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 12))
    
    if not query:
        return jsonify({
            'products': [],
            'total': 0,
            'page': page,
            'per_page': per_page,
            'total_pages': 0
        })
    
    result = search_products(query, page, per_page)
    return jsonify(result)

# === API GỢI Ý SẢN PHẨM LIÊN QUAN ===
@app.route('/api/product-recommendations/<int:product_id>', methods=['GET'])
def product_recommendations_api(product_id):
    """
    Gợi ý sản phẩm liên quan dựa trên ID sản phẩm
    """
    result = get_product_recommendations(product_id)
    return jsonify(result)

# === API GỢI Ý CÁ NHÂN HÓA ===
@app.route('/api/recommendations/personalized', methods=['GET'])
@token_required
def personalized_recommendations_api(current_user):
    """
    Gợi ý cá nhân hóa - hiển thị 8 sản phẩm khách hàng đã mua nhiều nhất
    """
    try:
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Không thể kết nối đến cơ sở dữ liệu'}), 500
        
        cursor = conn.cursor()
        
        # Lấy các sản phẩm người dùng đã mua và số lượng đã mua
        cursor.execute("""
            SELECT p.ProductId, p.StockCode, p.Description, p.MaxUnitPrice as UnitPrice,
                  SUM(oi.quantity) as TotalBought, p.ImagePath,
                  p.TotalQuantitySold
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
            JOIN products p ON oi.ProductId = p.ProductId
            WHERE o.user_id = ?
            GROUP BY p.ProductId, p.StockCode, p.Description, p.MaxUnitPrice, p.ImagePath, p.TotalQuantitySold
            ORDER BY TotalBought DESC
        """, current_user['user_id'])
        
        purchased_products = cursor.fetchall()
        
        # Nếu người dùng chưa mua hàng, trả về thông báo chưa có sản phẩm phù hợp
        if not purchased_products:
            return jsonify({
                'success': False,
                'recommendations': [],
                'message': 'Chưa có sản phẩm phù hợp cho bạn'
            })
        
        # Lấy tối đa 8 sản phẩm mà khách hàng đã mua nhiều nhất
        top_purchased_products = []
        for row in purchased_products[:8]:  # Giới hạn 8 sản phẩm
            top_purchased_products.append({
                'ProductId': int(row[0]),
                'StockCode': row[1],
                'Description': row[2],
                'UnitPrice': float(row[3]),
                'Quantity': int(row[4]),  # Số lượng khách hàng đã mua
                'ImagePath': row[5],
                'recommendation_score': 0.8  # Điểm gợi ý cao vì đây là sản phẩm khách hàng đã mua
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'recommendations': top_purchased_products,
            'message': 'Sản phẩm bạn mua nhiều nhất'
        })
            
    except Exception as e:
        print(f"Lỗi khi lấy sản phẩm đã mua: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'Đã xảy ra lỗi: {str(e)}'
        }), 500

@app.route('/api/personal-product-recommendations/<product>', methods=['GET'])
@token_required
def personal_product_recommendations_api(current_user, product):
    """
    Gợi ý sản phẩm mua kèm dựa trên lịch sử mua hàng của chính khách hàng,
    sử dụng thuật toán Apriori và chỉ số Lift
    """
    try:
        conn = get_connection()
        if not conn:
            return jsonify({'recommendations': [], 'message': 'Không có gợi ý sản phẩm mua kèm'}), 200
        
        cursor = conn.cursor()
        
        # Lấy các hóa đơn (đơn hàng) của người dùng
        cursor.execute("""
            SELECT order_id 
            FROM orders
            WHERE user_id = ?
        """, current_user['user_id'])
        
        user_orders = [row[0] for row in cursor.fetchall()]
        
        if not user_orders:
            # Nếu người dùng chưa có đơn hàng, trả về thông báo không có gợi ý
            return jsonify({'recommendations': [], 'message': 'Bạn chưa có đơn hàng nào để đề xuất sản phẩm mua kèm'}), 200
        
        # Lấy các sản phẩm đã mua trong các đơn hàng của người dùng
        order_placeholders = ','.join(['?'] * len(user_orders))
        cursor.execute(f"""
            SELECT DISTINCT oi.product_name
            FROM order_items oi
            WHERE oi.order_id IN ({order_placeholders})
        """, user_orders)
        
        purchased_products = [row[0] for row in cursor.fetchall()]
        
        if not purchased_products or len(purchased_products) <= 1:
            # Nếu người dùng chỉ mua 1 sản phẩm hoặc không có sản phẩm, trả về thông báo không đủ dữ liệu
            return jsonify({'recommendations': [], 'message': 'Bạn cần mua thêm sản phẩm để nhận gợi ý chính xác hơn'}), 200
        
        # Kiểm tra xem sản phẩm được yêu cầu có trong danh sách sản phẩm đã mua không
        if product not in purchased_products:
            # Nếu người dùng không mua sản phẩm này trước đây, thử tìm sản phẩm tương tự
            cursor.execute("""
                SELECT Description
                FROM products
                WHERE Description LIKE ?
                ORDER BY TotalQuantitySold DESC
                LIMIT 1
            """, f'%{product}%')
            
            product_match = cursor.fetchone()
            if product_match:
                product = product_match[0]
            else:
                # Nếu không tìm thấy sản phẩm tương tự, trả về thông báo không có dữ liệu
                return jsonify({'recommendations': [], 'message': 'Không tìm thấy sản phẩm tương tự trong lịch sử mua hàng của bạn'}), 200
        
        # Từ các sản phẩm đã mua, tính toán mối quan hệ giữa các sản phẩm
        # và tìm các sản phẩm thường được mua cùng với sản phẩm đang xem
        
        # Tạo bảng tần suất mua cùng giữa các sản phẩm
        product_counts = {}
        co_occurrence_counts = {}
        
        # Duyệt qua từng đơn hàng để đếm tần suất
        for order_id in user_orders:
            cursor.execute("""
                SELECT product_name
                FROM order_items
                WHERE order_id = ?
            """, order_id)
            
            products_in_order = [row[0] for row in cursor.fetchall()]
            
            # Cập nhật số lượng mua của từng sản phẩm
            for p in products_in_order:
                product_counts[p] = product_counts.get(p, 0) + 1
            
            # Cập nhật số lượng mua cùng nhau
            for i in range(len(products_in_order)):
                for j in range(i+1, len(products_in_order)):
                    p1 = products_in_order[i]
                    p2 = products_in_order[j]
                    
                    pair = tuple(sorted([p1, p2]))
                    co_occurrence_counts[pair] = co_occurrence_counts.get(pair, 0) + 1
        
        # Tính toán Lift cho các cặp sản phẩm
        total_orders = len(user_orders)
        product_pairs_lift = []
        
        for pair, co_count in co_occurrence_counts.items():
            p1, p2 = pair
            
            # Tính support cho từng sản phẩm và cả cặp
            support_p1 = product_counts.get(p1, 0) / total_orders
            support_p2 = product_counts.get(p2, 0) / total_orders
            support_pair = co_count / total_orders
            
            # Tính confidence
            confidence_p1_p2 = 0
            if support_p1 > 0:
                confidence_p1_p2 = support_pair / support_p1
            
            confidence_p2_p1 = 0
            if support_p2 > 0:
                confidence_p2_p1 = support_pair / support_p2
            
            # Tính lift
            lift = 0
            if support_p1 * support_p2 > 0:
                lift = support_pair / (support_p1 * support_p2)
            
            # Lưu kết quả
            product_pairs_lift.append({
                'product1': p1,
                'product2': p2,
                'support': support_pair,
                'confidence_p1_p2': confidence_p1_p2,
                'confidence_p2_p1': confidence_p2_p1,
                'lift': lift
            })
        
        # Sắp xếp các cặp theo lift giảm dần
        product_pairs_lift.sort(key=lambda x: x['lift'], reverse=True)
        
        # Lọc các sản phẩm liên quan đến sản phẩm đang xem
        related_products = []
        
        for pair_data in product_pairs_lift:
            p1 = pair_data['product1']
            p2 = pair_data['product2']
            
            if p1 == product and p2 != product:
                related_product = p2
                confidence = pair_data['confidence_p1_p2']
            elif p2 == product and p1 != product:
                related_product = p1
                confidence = pair_data['confidence_p2_p1']
            else:
                continue
            
            # Chỉ lấy các sản phẩm có lift > 1 (mối liên kết tích cực)
            if pair_data['lift'] > 1.0:
                # Lấy thông tin chi tiết về sản phẩm gợi ý
                cursor.execute("""
                    SELECT 
                        ProductId, 
                        StockCode, 
                        Description, 
                        MaxUnitPrice AS UnitPrice, 
                        TotalQuantitySold, 
                        ImagePath
                    FROM products
                    WHERE Description = ?
                """, related_product)
                
                product_info = cursor.fetchone()
                
                if product_info:
                    related_products.append({
                        'Description': product_info[2],
                        'confidence': confidence,
                        'support': pair_data['support'],
                        'lift': pair_data['lift'],
                        'Quantity': int(product_info[4]),
                        'ImagePath': product_info[5],
                        'UnitPrice': float(product_info[3])
                    })
        
        conn.close()
        
        # Nếu không tìm thấy sản phẩm liên quan, trả về thông báo không có gợi ý
        if not related_products:
            return jsonify({
                'recommendations': [],
                'message': 'Không tìm thấy gợi ý sản phẩm mua kèm cho sản phẩm này'
            }), 200
        
        return jsonify({
            'recommendations': related_products,
            'message': 'Gợi ý dựa trên lịch sử mua hàng của bạn'
        })
    
    except Exception as e:
        print(f"Lỗi khi tạo gợi ý cá nhân hóa cho sản phẩm: {str(e)}")
        # Không sử dụng phương thức dự phòng, chỉ thông báo lỗi
        return jsonify({
            'recommendations': [],
            'message': 'Đã xảy ra lỗi khi tìm kiếm sản phẩm gợi ý'
        }), 200

if __name__ == '__main__':
    app.run(debug=True)
