from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from db_connection import get_cleaned_products, get_connection

app = Flask(__name__)

# Cấu hình CORS đơn giản
CORS(app, origins="*", allow_headers=["Content-Type"])

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
def product_statistics():
    try:
        conn = get_connection()
        if not conn:
            return jsonify({'error': 'Không thể kết nối đến cơ sở dữ liệu.'}), 500
        
        cursor = conn.cursor()
        
        # Get product statistics
        cursor.execute("""
            SELECT 
                Description,
                SUM(Quantity) AS TotalQuantity,
                SUM(TotalPrice) AS TotalRevenue,
                COUNT(DISTINCT InvoiceNo) AS TransactionCount,
                COUNT(DISTINCT CustomerID) AS CustomerCount
            FROM cleaned_retail_data
            GROUP BY Description
        """)
        
        product_stats = []
        for row in cursor.fetchall():
            product_stats.append({
                'Description': row[0],
                'TotalQuantity': int(row[1]),
                'TotalRevenue': float(row[2]),
                'TransactionCount': int(row[3]),
                'CustomerCount': int(row[4])
            })
        
        # Get general statistics
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT StockCode) AS total_products,
                COUNT(DISTINCT CustomerID) AS total_customers,
                COUNT(DISTINCT InvoiceNo) AS total_transactions
        """)
        
        general_stats = cursor.fetchone()
        
        # Get average products per transaction
        cursor.execute("""
            SELECT AVG(ProductCount) AS avg_products_per_transaction
            FROM (
                SELECT InvoiceNo, COUNT(DISTINCT StockCode) AS ProductCount
                FROM cleaned_retail_data
                GROUP BY InvoiceNo
            ) AS subquery
        """)
        
        avg_products_per_transaction = cursor.fetchone()[0]
        
        # Get average quantity per transaction
        cursor.execute("""
            SELECT AVG(QuantitySum) AS avg_quantity_per_transaction
            FROM (
                SELECT InvoiceNo, SUM(Quantity) AS QuantitySum
                FROM cleaned_retail_data
                GROUP BY InvoiceNo
            ) AS subquery
        """)
        
        avg_quantity_per_transaction = cursor.fetchone()[0]
        
        # Get top products by quantity
        cursor.execute("""
            SELECT TOP 10 Description, SUM(Quantity) AS TotalQuantity
            FROM cleaned_retail_data
            GROUP BY Description
            ORDER BY TotalQuantity DESC
        """)
        
        top_products_by_quantity = []
        for row in cursor.fetchall():
            top_products_by_quantity.append({
                'Description': row[0],
                'TotalQuantity': int(row[1])
            })
        
        # Get top products by customer count
        cursor.execute("""
            SELECT TOP 10 Description, COUNT(DISTINCT CustomerID) AS CustomerCount
            FROM cleaned_retail_data
            GROUP BY Description
            ORDER BY CustomerCount DESC
        """)
        
        top_products_by_customers = []
        for row in cursor.fetchall():
            top_products_by_customers.append({
                'Description': row[0],
                'CustomerCount': int(row[1])
            })
        
        conn.close()
        
        summary = {
            'total_products': int(general_stats[0]),
            'total_customers': int(general_stats[1]),
            'total_transactions': int(general_stats[2]),
            'avg_products_per_transaction': float(avg_products_per_transaction),
            'avg_quantity_per_transaction': float(avg_quantity_per_transaction),
            'top_products_by_quantity': top_products_by_quantity,
            'top_products_by_customers': top_products_by_customers
        }
        
        return jsonify(summary)
        
    except Exception as e:
        return jsonify({'error': f'Đã xảy ra lỗi: {str(e)}'}), 500

@app.route('/shopping-behavior', methods=['GET'])
def shopping_behavior():
    try:
        conn = get_connection()
        if not conn:
            return jsonify({'error': 'Không thể kết nối đến cơ sở dữ liệu.'}), 500
        
        cursor = conn.cursor()
        
        # Get customer purchase frequency
        cursor.execute("""
            SELECT CustomerID, COUNT(DISTINCT InvoiceNo) AS PurchaseFrequency,
                   SUM(TotalPrice) AS TotalSpent,
                   SUM(Quantity) AS TotalItems,
                   COUNT(DISTINCT StockCode) AS UniqueProducts
            FROM cleaned_retail_data
            GROUP BY CustomerID
        """)
        
        # Create purchase frequency distribution
        cursor.execute("""
            SELECT PurchaseFrequency, COUNT(*) AS CustomerCount
            FROM (
                SELECT CustomerID, COUNT(DISTINCT InvoiceNo) AS PurchaseFrequency
                FROM cleaned_retail_data
                GROUP BY CustomerID
            ) AS subquery
            GROUP BY PurchaseFrequency
            ORDER BY PurchaseFrequency
        """)
        
        purchase_frequency_dist = {}
        for row in cursor.fetchall():
            purchase_frequency_dist[str(row[0])] = int(row[1])
        
        # Create product variety distribution
        cursor.execute("""
            SELECT UniqueProducts, COUNT(*) AS CustomerCount
            FROM (
                SELECT CustomerID, COUNT(DISTINCT StockCode) AS UniqueProducts
                FROM cleaned_retail_data
                GROUP BY CustomerID
            ) AS subquery
            GROUP BY UniqueProducts
            ORDER BY UniqueProducts
        """)
        
        product_variety_dist = {}
        for row in cursor.fetchall():
            product_variety_dist[str(row[0])] = int(row[1])
        
        # Create spending distribution (using percentile values)
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN NTILE(5) OVER (ORDER BY TotalSpent) = 1 THEN 'Very Low'
                    WHEN NTILE(5) OVER (ORDER BY TotalSpent) = 2 THEN 'Low'
                    WHEN NTILE(5) OVER (ORDER BY TotalSpent) = 3 THEN 'Medium'
                    WHEN NTILE(5) OVER (ORDER BY TotalSpent) = 4 THEN 'High'
                    WHEN NTILE(5) OVER (ORDER BY TotalSpent) = 5 THEN 'Very High'
                END AS SpendingGroup,
                COUNT(*) AS CustomerCount
            FROM (
                SELECT CustomerID, SUM(TotalPrice) AS TotalSpent
                FROM cleaned_retail_data
                GROUP BY CustomerID
            ) AS subquery
            GROUP BY 
                CASE 
                    WHEN NTILE(5) OVER (ORDER BY TotalSpent) = 1 THEN 'Very Low'
                    WHEN NTILE(5) OVER (ORDER BY TotalSpent) = 2 THEN 'Low'
                    WHEN NTILE(5) OVER (ORDER BY TotalSpent) = 3 THEN 'Medium'
                    WHEN NTILE(5) OVER (ORDER BY TotalSpent) = 4 THEN 'High'
                    WHEN NTILE(5) OVER (ORDER BY TotalSpent) = 5 THEN 'Very High'
                END
        """)
        
        spending_dist = {}
        for row in cursor.fetchall():
            spending_dist[row[0]] = int(row[1])
        
        # Get average statistics
        cursor.execute("""
            SELECT 
                AVG(PurchaseFrequency) AS avg_purchase_frequency,
                AVG(TotalSpent) AS avg_total_spent,
                AVG(UniqueProducts) AS avg_unique_products,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY PurchaseFrequency) OVER() AS median_purchase_frequency,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY TotalSpent) OVER() AS median_total_spent
            FROM (
                SELECT 
                    CustomerID, 
                    COUNT(DISTINCT InvoiceNo) AS PurchaseFrequency,
                    SUM(TotalPrice) AS TotalSpent,
                    COUNT(DISTINCT StockCode) AS UniqueProducts
                FROM cleaned_retail_data
                GROUP BY CustomerID
            ) AS subquery
        """)
        
        avg_stats_row = cursor.fetchone()
        
        avg_stats = {
            'avg_purchase_frequency': float(avg_stats_row[0]),
            'avg_total_spent': float(avg_stats_row[1]),
            'avg_unique_products': float(avg_stats_row[2]),
            'median_purchase_frequency': float(avg_stats_row[3]),
            'median_total_spent': float(avg_stats_row[4])
        }
        
        conn.close()
        
        result = {
            'purchase_frequency_distribution': purchase_frequency_dist,
            'product_variety_distribution': product_variety_dist,
            'spending_distribution': spending_dist,
            'average_stats': avg_stats
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Đã xảy ra lỗi: {str(e)}'}), 500

@app.route('/shopping-sequences', methods=['GET'])
def shopping_sequences():
    try:
        # Get database connection
        conn = get_connection()
        if not conn:
            return jsonify({'error': 'Không thể kết nối đến cơ sở dữ liệu.'}), 500
        
        cursor = conn.cursor()
        
        # Get top 5 customers with most transactions
        cursor.execute("""
            SELECT TOP 5 CustomerID, COUNT(DISTINCT InvoiceNo) AS InvoiceCount
            FROM cleaned_retail_data
            GROUP BY CustomerID
            ORDER BY InvoiceCount DESC
        """)
        
        top_customers = [row[0] for row in cursor.fetchall()]
        
        # Analyze shopping sequences for top customers
        customer_sequences = {}
        
        for customer in top_customers:
            cursor.execute("""
                SELECT DISTINCT InvoiceNo, CONVERT(VARCHAR(10), Day, 120) AS InvoiceDate
                FROM cleaned_retail_data
                WHERE CustomerID = ?
                ORDER BY InvoiceDate
            """, customer)
            
            invoices = cursor.fetchall()
            
            sequence = []
            for invoice_row in invoices:
                invoice = invoice_row[0]
                date = invoice_row[1]
                
                # Get products for this invoice (limited to 5)
                cursor.execute("""
                    SELECT TOP 5 Description
                    FROM cleaned_retail_data
                    WHERE CustomerID = ? AND InvoiceNo = ?
                """, customer, invoice)
                
                products = [row[0] for row in cursor.fetchall()]
                
                sequence.append({
                    'invoice': invoice,
                    'date': date,
                    'products': products
                })
            
            customer_sequences[str(customer)] = sequence
        
        # Get common shopping patterns from association_rules table
        cursor.execute("""
            SELECT TOP 20 antecedents, consequents, support, confidence, lift
            FROM association_rules
            ORDER BY lift DESC
        """)
        
        common_sequences = []
        for row in cursor.fetchall():
            sequence = {
                'antecedents': row[0],
                'consequents': row[1],
                'support': float(row[2]),
                'confidence': float(row[3]),
                'lift': float(row[4])
            }
            common_sequences.append(sequence)
        
        conn.close()
        
        result = {
            'customer_sequences': customer_sequences,
            'common_shopping_patterns': common_sequences
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Đã xảy ra lỗi: {str(e)}'}), 500

@app.route('/correlation-analysis', methods=['GET'])
def correlation_analysis():
    try:
        conn = get_connection()
        if not conn:
            return jsonify({'error': 'Không thể kết nối đến cơ sở dữ liệu.'}), 500
        
        cursor = conn.cursor()
        
        # Calculate correlation between quantity and price variables
        cursor.execute("""
            SELECT 
                (
                    (COUNT(*) * SUM(Quantity * UnitPrice)) - (SUM(Quantity) * SUM(UnitPrice))
                ) / 
                (
                    SQRT((COUNT(*) * SUM(Quantity * Quantity)) - (SUM(Quantity) * SUM(Quantity))) * 
                    SQRT((COUNT(*) * SUM(UnitPrice * UnitPrice)) - (SUM(UnitPrice) * SUM(UnitPrice)))
                ) AS quantity_unitprice_corr,
                
                (
                    (COUNT(*) * SUM(Quantity * TotalPrice)) - (SUM(Quantity) * SUM(TotalPrice))
                ) / 
                (
                    SQRT((COUNT(*) * SUM(Quantity * Quantity)) - (SUM(Quantity) * SUM(Quantity))) * 
                    SQRT((COUNT(*) * SUM(TotalPrice * TotalPrice)) - (SUM(TotalPrice) * SUM(TotalPrice)))
                ) AS quantity_totalprice_corr,
                
                (
                    (COUNT(*) * SUM(UnitPrice * TotalPrice)) - (SUM(UnitPrice) * SUM(TotalPrice))
                ) / 
                (
                    SQRT((COUNT(*) * SUM(UnitPrice * UnitPrice)) - (SUM(UnitPrice) * SUM(UnitPrice))) * 
                    SQRT((COUNT(*) * SUM(TotalPrice * TotalPrice)) - (SUM(TotalPrice) * SUM(TotalPrice)))
                ) AS unitprice_totalprice_corr
            FROM cleaned_retail_data
        """)
        
        corr_row = cursor.fetchone()
        
        # Create correlation dictionary formatted like the DataFrame.corr() result
        correlation = {
            'Quantity': {
                'Quantity': 1.0,
                'UnitPrice': float(corr_row[0]),
                'TotalPrice': float(corr_row[1])
            },
            'UnitPrice': {
                'Quantity': float(corr_row[0]),
                'UnitPrice': 1.0,
                'TotalPrice': float(corr_row[2])
            },
            'TotalPrice': {
                'Quantity': float(corr_row[1]),
                'UnitPrice': float(corr_row[2]),
                'TotalPrice': 1.0
            }
        }
        
        # Get top 20 products for co-occurrence analysis
        cursor.execute("""
            SELECT TOP 20 Description
            FROM (
                SELECT Description, COUNT(*) AS cnt
                FROM cleaned_retail_data
                GROUP BY Description
            ) AS product_counts
            ORDER BY cnt DESC
        """)
        
        top_products = [row[0] for row in cursor.fetchall()]
        
        # Find product co-occurrences in the same invoices
        product_correlations = []
        
        # This is a complex query, so we'll use multiple queries to get the data
        for i in range(len(top_products)):
            for j in range(i+1, len(top_products)):
                # Count how many times products appear together
                cursor.execute("""
                    SELECT COUNT(DISTINCT a.InvoiceNo) AS co_occurrence
                    FROM cleaned_retail_data a
                    JOIN cleaned_retail_data b ON a.InvoiceNo = b.InvoiceNo
                    WHERE a.Description = ? AND b.Description = ?
                """, top_products[i], top_products[j])
                
                co_occurrence = cursor.fetchone()[0]
                
                if co_occurrence > 0:
                    product_correlations.append({
                        "product1": top_products[i],
                        "product2": top_products[j],
                        "co_occurrence": int(co_occurrence)
                    })
        
        # Sort product correlations by co-occurrence
        product_correlations.sort(key=lambda x: x["co_occurrence"], reverse=True)
        product_correlations = product_correlations[:20]  # Limit to top 20
        
        conn.close()
        
        result = {
            'variable_correlation': correlation,
            'product_correlations': product_correlations
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Đã xảy ra lỗi: {str(e)}'}), 500

@app.route('/recommendation', methods=['GET'])
def product_recommendation():
    try:
        conn = get_connection()
        if not conn:
            return jsonify({'error': 'Không thể kết nối đến cơ sở dữ liệu.'}), 500
        
        cursor = conn.cursor()
        
        # Get frequent itemsets from the database
        cursor.execute("""
            SELECT TOP 20 itemsets, support
            FROM frequent_itemsets
            ORDER BY support DESC
        """)
        
        frequent_itemsets = []
        for row in cursor.fetchall():
            frequent_itemsets.append({
                'itemsets': row[0],
                'support': float(row[1])
            })
        
        # Get association rules from the database
        cursor.execute("""
            SELECT TOP 20 antecedents, consequents, support, confidence, lift
            FROM association_rules
            ORDER BY lift DESC
        """)
        
        rules_list = []
        for row in cursor.fetchall():
            rules_list.append({
                'antecedents': row[0],
                'consequents': row[1],
                'support': float(row[2]),
                'confidence': float(row[3]),
                'lift': float(row[4])
            })
        
        conn.close()
        
        result = {
            'frequent_itemsets': frequent_itemsets,
            'association_rules': rules_list
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Đã xảy ra lỗi: {str(e)}'}), 500

@app.route('/recommend-for-product/<product>', methods=['GET'])
def recommend_for_product(product):
    try:
        conn = get_connection()
        if not conn:
            return jsonify({'error': 'Không thể kết nối đến cơ sở dữ liệu.'}), 500
        
        cursor = conn.cursor()
        
        # Tìm các sản phẩm thường được mua cùng với sản phẩm đầu vào
        cursor.execute("""
            SELECT COUNT(DISTINCT InvoiceNo) as invoices_count
            FROM cleaned_retail_data
            WHERE Description LIKE ?
        """, f'%{product}%')
        
        count_result = cursor.fetchone()
        if not count_result or count_result[0] == 0:
            return jsonify({'product': product, 'recommendations': [], 'message': 'Không tìm thấy sản phẩm.'})
        
        # Lấy tất cả hóa đơn có chứa sản phẩm này
        cursor.execute("""
            SELECT DISTINCT InvoiceNo
            FROM cleaned_retail_data
            WHERE Description LIKE ?
        """, f'%{product}%')
        
        invoices = [row[0] for row in cursor.fetchall()]
        
        # Lấy danh sách các sản phẩm được mua cùng với sản phẩm này
        placeholders = ','.join(['?'] * len(invoices))
        query = f"""
            SELECT 
                Description,
                COUNT(DISTINCT InvoiceNo) as co_purchases,
                SUM(Quantity) as total_quantity
            FROM cleaned_retail_data
            WHERE InvoiceNo IN ({placeholders})
            AND Description NOT LIKE ?
            GROUP BY Description
            ORDER BY co_purchases DESC, total_quantity DESC
            OFFSET 0 ROWS FETCH NEXT 10 ROWS ONLY
        """
        
        # Thêm tham số product vào cuối danh sách tham số
        params = invoices + [f'%{product}%']
        cursor.execute(query, params)
        
        recommendations = []
        for row in cursor.fetchall():
            # Tính toán độ tin cậy (confidence)
            confidence = row[1] / len(invoices)
            
            # Lấy thông tin hình ảnh cho sản phẩm nếu có
            cursor.execute("""
                SELECT ImagePath 
                FROM products 
                WHERE Description LIKE ?
            """, f'%{row[0]}%')
            
            image_row = cursor.fetchone()
            image_path = image_row[0] if image_row else None
            
            recommendations.append({
                'Description': row[0],
                'InvoiceNo': int(row[1]),  # Số lần mua chung
                'Quantity': int(row[2]),   # Tổng số lượng
                'confidence': float(confidence),
                'ImagePath': image_path
            })
        
        result = {
            'product': product,
            'total_matching_invoices': len(invoices),
            'recommendations': recommendations
        }
        
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Đã xảy ra lỗi: {str(e)}'}), 500

@app.route('/common-shopping-patterns', methods=['GET'])
def common_shopping_patterns():
    try:
        conn = get_connection()
        if not conn:
            return jsonify({'error': 'Không thể kết nối đến cơ sở dữ liệu.'}), 500
        
        cursor = conn.cursor()
        
        # Get top 10 association rules based on confidence
        cursor.execute("""
            SELECT TOP 10 
                antecedents, 
                consequents, 
                support, 
                confidence, 
                lift
            FROM association_rules
            ORDER BY confidence DESC
        """)
        
        top_patterns = []
        for row in cursor.fetchall():
            pattern = {
                'mua_truoc': row[0],
                'mua_sau': row[1],
                'ho_tro': float(row[2]),
                'do_tin_cay': float(row[3]),
                'do_nang': float(row[4])
            }
            top_patterns.append(pattern)
        
        conn.close()
        return jsonify(top_patterns)
        
    except Exception as e:
        return jsonify({'error': f'Đã xảy ra lỗi: {str(e)}'}), 500

@app.route('/frequently-bought-together', methods=['GET'])
def frequently_bought_together():
    try:
        conn = get_connection()
        if not conn:
            return jsonify({'error': 'Không thể kết nối đến cơ sở dữ liệu.'}), 500
        
        cursor = conn.cursor()
        
        # Get product pairs frequently bought together using SQL
        cursor.execute("""
            SELECT TOP 20
                a.Description AS product1,
                b.Description AS product2,
                COUNT(DISTINCT a.InvoiceNo) AS co_occurrence_count
            FROM 
                cleaned_retail_data a
            JOIN 
                cleaned_retail_data b ON a.InvoiceNo = b.InvoiceNo
            WHERE 
                a.Description < b.Description
            GROUP BY 
                a.Description, b.Description
            ORDER BY 
                co_occurrence_count DESC
        """)
        
        result = []
        for row in cursor.fetchall():
            item = {
                'san_pham_1': row[0],
                'san_pham_2': row[1],
                'so_lan_mua_chung': int(row[2])
            }
            result.append(item)
        
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Đã xảy ra lỗi: {str(e)}'}), 500

@app.route('/product-search', methods=['GET'])
def product_search():
    try:
        query = request.args.get('query', '').strip().lower()
        if not query:
            return jsonify([])
        
        conn = get_connection()
        if not conn:
            return jsonify({'error': 'Không thể kết nối đến cơ sở dữ liệu.'}), 500
        
        cursor = conn.cursor()
        
        # Search for products by name
        cursor.execute("""
            SELECT DISTINCT TOP 10 Description
            FROM cleaned_retail_data
            WHERE LOWER(Description) LIKE ?
            ORDER BY Description
        """, f'%{query}%')
        
        matching_products = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return jsonify(matching_products)
        
    except Exception as e:
        return jsonify({'error': f'Đã xảy ra lỗi: {str(e)}'}), 500

@app.route('/api/products', methods=['GET'])
def get_all_products():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 12))
        
        conn = get_connection()
        if not conn:
            return jsonify({'error': 'Không thể kết nối đến cơ sở dữ liệu.'}), 500
        
        cursor = conn.cursor()
        
        # Tính offset cho phân trang
        offset = (page - 1) * per_page
        
        # Query lấy tổng số bản ghi
        cursor.execute("SELECT COUNT(*) FROM cleaned_retail_data")
        total = int(cursor.fetchone()[0])
        
        # Query lấy dữ liệu có phân trang
        cursor.execute("""
            SELECT 
                ID, InvoiceNo, StockCode, Description, Quantity, 
                InvoiceDate, UnitPrice, CustomerID, Country, 
                TotalPrice, Month, Year, Day
            FROM cleaned_retail_data
            ORDER BY ID
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """, offset, per_page)
        
        products = []
        for row in cursor.fetchall():
            products.append({
                'ID': row[0],
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
        
        return jsonify({
            'products': products,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({'error': f'Đã xảy ra lỗi: {str(e)}'}), 500

@app.route('/api/products/search', methods=['GET'])
def search_products_api():
    try:
        query = request.args.get('query', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 12))
        
        if not query:
            return jsonify({'products': [], 'total': 0, 'page': 1, 'per_page': 12, 'total_pages': 0})
        
        conn = get_connection()
        if not conn:
            return jsonify({'error': 'Không thể kết nối đến cơ sở dữ liệu.'}), 500
        
        cursor = conn.cursor()
        
        # Tính offset cho phân trang
        offset = (page - 1) * per_page
        
        # Query lấy tổng số kết quả tìm kiếm
        cursor.execute("""
            SELECT COUNT(*)
            FROM cleaned_retail_data
            WHERE Description LIKE ?
        """, f'%{query}%')
        
        total = int(cursor.fetchone()[0])
        
        # Query lấy dữ liệu có phân trang
        cursor.execute("""
            SELECT 
                ID, InvoiceNo, StockCode, Description, Quantity, 
                InvoiceDate, UnitPrice, CustomerID, Country, 
                TotalPrice, Month, Year, Day
            FROM cleaned_retail_data
            WHERE Description LIKE ?
            ORDER BY ID
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """, f'%{query}%', offset, per_page)
        
        products = []
        for row in cursor.fetchall():
            products.append({
                'ID': row[0],
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
        
        return jsonify({
            'products': products,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({'error': f'Đã xảy ra lỗi: {str(e)}'}), 500

@app.route('/api/products/<int:product_id>/recommendations', methods=['GET'])
def get_recommendations(product_id):
    try:
        conn = get_connection()
        if not conn:
            return jsonify({'error': 'Không thể kết nối đến cơ sở dữ liệu.'}), 500
        
        cursor = conn.cursor()
        
        # First get the product description
        cursor.execute("""
            SELECT Description 
            FROM products 
            WHERE ProductId = ?
        """, product_id)
        
        product_row = cursor.fetchone()
        if not product_row:
            return jsonify({'error': 'Không tìm thấy sản phẩm.'}), 404
            
        product_desc = product_row[0]
        
        # Get recommendations based on association rules
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
        
        products = []
        for row in cursor.fetchall():
            products.append({
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
        
        return jsonify({'recommendations': products})
    except Exception as e:
        return jsonify({'error': f'Đã xảy ra lỗi: {str(e)}'}), 500

@app.route('/api/best-sellers', methods=['GET'])
def best_sellers():
    try:
        conn = get_connection()
        if not conn:
            return jsonify({'error': 'Không thể kết nối đến cơ sở dữ liệu.'}), 500
        
        cursor = conn.cursor()
        
        # Get top 12 best-selling products
        cursor.execute("""
            SELECT TOP 12 
                StockCode, 
                Description,
                SUM(Quantity) AS TotalQuantity,
                MAX(UnitPrice) AS UnitPrice,
                SUM(TotalPrice) AS TotalRevenue,
                COUNT(DISTINCT InvoiceNo) AS TransactionCount
            FROM cleaned_retail_data
            GROUP BY StockCode, Description
            ORDER BY TotalQuantity DESC
        """)
        
        products = []
        for row in cursor.fetchall():
            products.append({
                'StockCode': row[0],
                'Description': row[1],
                'Quantity': int(row[2]),
                'UnitPrice': float(row[3]),
                'TotalRevenue': float(row[4]),
                'TransactionCount': int(row[5])
            })
        
        conn.close()
        return jsonify({'products': products})
    except Exception as e:
        return jsonify({'error': f'Đã xảy ra lỗi: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
