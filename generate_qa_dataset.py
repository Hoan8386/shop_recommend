import pandas as pd
import numpy as np
from db_connection import get_connection, get_product_statistics, get_shopping_behavior, get_correlation_analysis, get_shopping_sequences, get_all_product_associations
import datetime
import random

print("Bắt đầu tạo bộ dữ liệu câu hỏi và trả lời để huấn luyện chatbot...")

def generate_qa_dataset():
    """Generate a comprehensive Q&A dataset from retail analysis data"""
    
    qa_pairs = []
    
    # Add timestamp for reference
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Đang tạo bộ dữ liệu tại {current_time}")
    
    # Get data from various endpoints
    try:
        product_stats = get_product_statistics()
        shopping_behavior = get_shopping_behavior()
        correlations = get_correlation_analysis()
        shopping_patterns = get_shopping_sequences()
        product_associations = get_all_product_associations()
        
        print("Đã truy xuất dữ liệu từ cơ sở dữ liệu thành công")
    except Exception as e:
        print(f"Lỗi khi truy xuất dữ liệu: {str(e)}")
        return []
    
    # ========== GENERAL STATISTICS QUESTIONS ==========
    
    # Basic stats questions
    qa_pairs.extend([
        {
            "question": "Có bao nhiêu sản phẩm trong cơ sở dữ liệu?",
            "answer": f"Có {product_stats['total_products']} sản phẩm khác nhau trong cơ sở dữ liệu của chúng tôi."
        },
        {
            "question": "Tổng số khách hàng là bao nhiêu?",
            "answer": f"Chúng tôi có dữ liệu về {product_stats['total_customers']} khách hàng duy nhất."
        },
        {
            "question": "Có bao nhiêu giao dịch được ghi nhận trong hệ thống?",
            "answer": f"Cơ sở dữ liệu chứa {product_stats['total_transactions']} giao dịch duy nhất."
        },
        {
            "question": "Trung bình mỗi giao dịch có bao nhiêu sản phẩm?",
            "answer": f"Trung bình, mỗi giao dịch chứa {product_stats['avg_products_per_transaction']:.2f} sản phẩm."
        },
        {
            "question": "Cho tôi biết về thống kê chung của cửa hàng",
            "answer": f"Cửa hàng của chúng tôi có {product_stats['total_products']} sản phẩm duy nhất, " +
                     f"{product_stats['total_customers']} khách hàng, và " +
                     f"{product_stats['total_transactions']} giao dịch được ghi nhận. " +
                     f"Trung bình, khách hàng mua {product_stats['avg_products_per_transaction']:.2f} sản phẩm mỗi giao dịch."
        }
    ])
    
    # ========== TOP PRODUCTS QUESTIONS ==========
    
    # Get top products data
    top_products = product_stats.get('top_products_by_quantity', [])
    if top_products:
        top_product = top_products[0]
        
        # Top products questions
        qa_pairs.extend([
            {
                "question": "Sản phẩm bán chạy nhất là gì?",
                "answer": f"Sản phẩm bán chạy nhất là '{top_product['Description']}' với {top_product['TotalQuantity']} đơn vị đã bán."
            },
            {
                "question": "5 sản phẩm phổ biến nhất là gì?",
                "answer": "5 sản phẩm phổ biến nhất theo số lượng bán ra là: " + 
                         ", ".join([f"'{p['Description']}' ({p['TotalQuantity']} đơn vị)" for p in top_products[:5]])
            },
            {
                "question": "Sản phẩm nào bán được nhiều nhất?",
                "answer": "Các sản phẩm bán chạy nhất của chúng tôi là: " + 
                         ", ".join([f"'{p['Description']}' ({p['TotalQuantity']} đơn vị)" for p in top_products[:3]])
            }
        ])
    
    # ========== REVENUE QUESTIONS ==========
    
    # Revenue by month
    monthly_revenue = product_stats.get('monthly_revenue', [])
    if monthly_revenue:
        # Find month with highest revenue
        highest_month = max(monthly_revenue, key=lambda x: x['revenue'])
        lowest_month = min(monthly_revenue, key=lambda x: x['revenue'])
        month_name = {1: 'Tháng 1', 2: 'Tháng 2', 3: 'Tháng 3', 4: 'Tháng 4', 5: 'Tháng 5', 
                     6: 'Tháng 6', 7: 'Tháng 7', 8: 'Tháng 8', 9: 'Tháng 9', 
                     10: 'Tháng 10', 11: 'Tháng 11', 12: 'Tháng 12'}
        
        qa_pairs.extend([
            {
                "question": "Tháng nào có doanh số cao nhất?",
                "answer": f"Tháng có doanh số cao nhất là {month_name[highest_month['month']]} với doanh thu £{highest_month['revenue']:.2f}."
            },
            {
                "question": "Tháng nào có doanh số thấp nhất?",
                "answer": f"Tháng có doanh số thấp nhất là {month_name[lowest_month['month']]} với doanh thu £{lowest_month['revenue']:.2f}."
            },
            {
                "question": "Xu hướng doanh thu hàng tháng như thế nào?",
                "answer": "Doanh thu hàng tháng cho thấy " + 
                         ("xu hướng tăng" if monthly_revenue[-1]['revenue'] > monthly_revenue[0]['revenue'] else "xu hướng giảm") +
                         f" với doanh thu cao nhất là £{highest_month['revenue']:.2f} trong {month_name[highest_month['month']]} và thấp nhất là £{lowest_month['revenue']:.2f} trong {month_name[lowest_month['month']]}."
            }
        ])
    
    # ========== SHOPPING BEHAVIOR QUESTIONS ==========
    
    if shopping_behavior:
        # Purchase frequency distribution
        purchase_freq = shopping_behavior.get('purchase_frequency_distribution', {})
        
        # Spending distribution
        spending_dist = shopping_behavior.get('spending_distribution', {})
        
        # Average statistics
        avg_stats = shopping_behavior.get('average_stats', {})
        
        # Purchase by country
        country_data = shopping_behavior.get('purchase_by_country', [])
        top_country = country_data[0] if country_data else {'country': 'Không rõ', 'count': 0}
        
        # Xác định quốc gia có ít đơn hàng nhất
        if len(country_data) > 0:
            bottom_country = country_data[-1]
        else:
            bottom_country = {'country': 'Không rõ', 'count': 0}
            
        # Lấy giá trị đơn hàng trung bình theo quốc gia
        avg_order_by_country = shopping_behavior.get('avg_order_by_country', [])
        top_avg_order_country = avg_order_by_country[0] if avg_order_by_country else {'country': 'Không rõ', 'average': 0}
        
        qa_pairs.extend([
            {
                "question": "Tần suất mua hàng trung bình của mỗi khách hàng là bao nhiêu?",
                "answer": f"Trung bình, khách hàng thực hiện {avg_stats.get('avg_purchase_frequency', 0):.2f} lần mua hàng."
            },
            {
                "question": "Một khách hàng trung bình chi tiêu bao nhiêu?",
                "answer": f"Khách hàng trung bình chi tiêu £{avg_stats.get('avg_total_spent', 0):.2f} tổng cộng cho tất cả các lần mua hàng."
            },
            {
                "question": "Một khách hàng thường mua bao nhiêu sản phẩm khác nhau?",
                "answer": f"Một khách hàng điển hình mua {avg_stats.get('avg_unique_products', 0):.2f} sản phẩm khác nhau."
            },
            {
                "question": "Quốc gia nào có nhiều khách hàng nhất?",
                "answer": f"Quốc gia có nhiều khách hàng nhất là {top_country['country']} với {top_country['count']} lượt mua hàng."
            },
            {
                "question": "Quốc gia nào đặt hàng nhiều nhất?",
                "answer": f"Quốc gia đặt hàng nhiều nhất là {top_country['country']} với tổng cộng {top_country['count']} đơn hàng."
            },
            {
                "question": "Quốc gia nào đặt hàng ít nhất?",
                "answer": f"Quốc gia đặt hàng ít nhất là {bottom_country['country']} với chỉ {bottom_country['count']} đơn hàng."
            },
            {
                "question": "Quốc gia nào có giá trị đơn hàng trung bình cao nhất?",
                "answer": f"Quốc gia có giá trị đơn hàng trung bình cao nhất là {top_avg_order_country['country']} với giá trị trung bình là £{top_avg_order_country['average']:.2f} cho mỗi đơn hàng."
            },
            {
                "question": "Thị trường lớn nhất của chúng tôi là gì?",
                "answer": f"Thị trường lớn nhất của chúng tôi là {top_country['country']}, chiếm một phần đáng kể trong tổng số đơn hàng với {top_country['count']} lượt mua."
            },
            {
                "question": "Chi tiêu của khách hàng phân bố như thế nào?",
                "answer": "Chi tiêu của khách hàng được phân bố như sau: " + 
                         ", ".join([f"{key}: {value} khách hàng" for key, value in spending_dist.items()])
            },
            {
                "question": "Tần suất mua hàng phổ biến nhất là gì?",
                "answer": f"Tần suất mua hàng phổ biến nhất là {max(purchase_freq.items(), key=lambda x: x[1])[0]} lần mua hàng mỗi khách hàng."
            },
            {
                "question": "Cho tôi biết về hành vi mua sắm của khách hàng",
                "answer": f"Hầu hết khách hàng của chúng tôi đến từ {top_country['country']}. Trung bình, khách hàng thực hiện {avg_stats.get('avg_purchase_frequency', 0):.2f} " +
                         f"lần mua hàng và chi tiêu tổng cộng £{avg_stats.get('avg_total_spent', 0):.2f}. " +
                         f"Họ thường mua {avg_stats.get('avg_unique_products', 0):.2f} sản phẩm khác nhau."
            },
            {
                "question": "Quốc gia nào mua sắm nhiều nhất?",
                "answer": f"{top_country['country']} là quốc gia mua sắm nhiều nhất với {top_country['count']} đơn hàng. {top_avg_order_country['country']} là quốc gia có giá trị đơn hàng trung bình cao nhất (£{top_avg_order_country['average']:.2f})."
            }
        ])
    
    # ========== PRODUCT ASSOCIATIONS QUESTIONS ==========
    
    if correlations:
        correlated_items = correlations.get('correlated_items', [])
        
        if correlated_items:
            # Get the first correlated item for examples
            first_item = correlated_items[0]
            
            qa_pairs.extend([
                {
                    "question": "Những sản phẩm nào thường được mua cùng nhau?",
                    "answer": f"Các sản phẩm thường được mua cùng nhau bao gồm: {first_item['itemsets']} (hỗ trợ: {first_item['support']:.4f})."
                },
                {
                    "question": "Kết hợp sản phẩm phổ biến nhất là gì?",
                    "answer": f"Kết hợp sản phẩm phổ biến nhất là: {first_item['itemsets']}."
                },
                {
                    "question": "Cho tôi biết về mối liên hệ giữa các sản phẩm",
                    "answer": "Phân tích của chúng tôi cho thấy một số kết hợp sản phẩm thường xuyên được mua cùng nhau. " +
                             f"Mối liên hệ mạnh nhất là cho: {first_item['itemsets']} với giá trị hỗ trợ là {first_item['support']:.4f}."
                }
            ])

            # Thêm câu hỏi về mua kèm cho các sản phẩm cụ thể
            product_names = [
                "WHITE HANGING HEART T-LIGHT HOLDER",
                "REGENCY CAKESTAND 3 TIER",
                "JUMBO BAG RED RETROSPOT",
                "PARTY BUNTING",
                "SET OF 3 CAKE TINS PANTRY DESIGN"
            ]
            
            for product in product_names:
                qa_pairs.extend([
                    {
                        "question": f"Những sản phẩm nào thường được mua cùng với {product}?",
                        "answer": f"Khi khách hàng mua '{product}', họ thường mua kèm theo các sản phẩm như: "
                                 f"RED HANGING HEART T-LIGHT HOLDER, SET OF 6 T-LIGHTS và GLASS STAR FROSTED T-LIGHT HOLDER. "
                                 f"Đây là các sản phẩm bổ sung nhau về chức năng hoặc phong cách thiết kế."
                    },
                    {
                        "question": f"Nếu tôi muốn mua {product}, bạn sẽ đề xuất thêm gì?",
                        "answer": f"Nếu bạn quan tâm đến '{product}', tôi đề xuất bạn xem thêm các sản phẩm bổ sung như: "
                                 f"GLASS STAR FROSTED T-LIGHT HOLDER, GLASS STAR FROSTED T-LIGHT HOLDER và SET OF 6 T-LIGHTS. "
                                 f"Những sản phẩm này thường được mua cùng nhau và tạo thành một bộ sưu tập hoàn chỉnh."
                    }
                ])
    
    # ========== DYNAMIC PRODUCT RECOMMENDATIONS ==========
    # Tạo câu hỏi và trả lời cho các sản phẩm từ cơ sở dữ liệu
    
    if product_associations and 'product_associations' in product_associations:
        associations_data = product_associations['product_associations']
        product_info = product_associations.get('product_info', {})
        
        # Lấy ra các sản phẩm có dữ liệu về mối liên hệ
        products_with_associations = list(associations_data.keys())
        
        # Lấy mẫu ngẫu nhiên các sản phẩm để tạo câu hỏi (giới hạn số lượng để tránh quá tải)
        sample_size = min(50, len(products_with_associations))
        if sample_size > 0:
            sampled_products = random.sample(products_with_associations, sample_size)
            
            for product_name in sampled_products:
                # Lấy các sản phẩm mua kèm với sản phẩm này
                related_products = associations_data[product_name]
                
                if related_products:
                    # Sắp xếp theo độ tin cậy giảm dần
                    related_products.sort(key=lambda x: x['confidence'], reverse=True)
                    
                    # Lấy top 3 sản phẩm liên quan
                    top_related = related_products[:3]
                    
                    # Tạo câu trả lời với thông tin chi tiết
                    related_desc = ", ".join([f"'{p['related_product']}' (độ tin cậy: {p['confidence']*100:.1f}%, hệ số nâng cao: {p['lift']:.2f})" 
                                            for p in top_related])
                    
                    qa_pairs.extend([
                        {
                            "question": f"Những sản phẩm nào thường được mua cùng với {product_name}?",
                            "answer": f"Khi khách hàng mua '{product_name}', họ thường mua kèm theo các sản phẩm: {related_desc}. " +
                                     f"Những sản phẩm này có mối liên hệ mạnh với '{product_name}' dựa trên dữ liệu mua sắm của chúng tôi."
                        },
                        {
                            "question": f"Nếu tôi quan tâm đến {product_name}, bạn đề xuất mua thêm gì?",
                            "answer": f"Dựa trên hành vi mua sắm của khách hàng khác, tôi đề xuất bạn xem xét các sản phẩm sau cùng với '{product_name}': " +
                                     f"{', '.join([p['related_product'] for p in top_related])}. " +
                                     f"Những sản phẩm này thường được mua cùng nhau và bổ sung cho nhau rất tốt."
                        },
                        {
                            "question": f"Khi mua {product_name}, khách hàng khác thường mua gì thêm?",
                            "answer": f"Khách hàng mua '{product_name}' thường mua thêm: {', '.join([p['related_product'] for p in top_related])}. " +
                                     f"Sản phẩm được mua cùng phổ biến nhất là '{top_related[0]['related_product']}' với độ tin cậy {top_related[0]['confidence']*100:.1f}%."
                        }
                    ])
    
    # ========== GENERAL FAQs ==========
    
    # Add some general FAQs about the shopping system
    qa_pairs.extend([
        {
            "question": "Làm thế nào để tìm kiếm sản phẩm?",
            "answer": "Bạn có thể tìm kiếm sản phẩm bằng thanh tìm kiếm ở đầu trang cửa hàng. Nhập từ khóa liên quan đến sản phẩm bạn đang tìm kiếm."
        },
        {
            "question": "Hệ thống đề xuất sản phẩm hoạt động như thế nào?",
            "answer": "Đề xuất sản phẩm của chúng tôi dựa trên khai thác luật kết hợp, phân tích các mẫu trong lịch sử mua hàng của khách hàng. Chúng tôi xác định các sản phẩm thường được mua cùng nhau."
        },
        {
            "question": "Dữ liệu nào đang được phân tích?",
            "answer": "Chúng tôi phân tích dữ liệu giao dịch bao gồm thông tin sản phẩm, số lượng, giá cả, thông tin khách hàng và ngày mua hàng để xác định các mô hình và xu hướng."
        },
        {
            "question": "Dữ liệu có độ mới như thế nào?",
            "answer": "Phân tích dựa trên bộ dữ liệu Bán lẻ Trực tuyến, bao gồm các giao dịch từ tháng 12 năm 2010."
        },
        {
            "question": "Làm thế nào để biết về các xu hướng mua sắm theo quốc gia?",
            "answer": f"Chúng tôi có phân tích theo quốc gia cho thấy {top_country['country']} là thị trường lớn nhất với {top_country['count']} đơn hàng. Khách hàng từ {top_avg_order_country['country']} có giá trị đơn hàng trung bình cao nhất (£{top_avg_order_country['average']:.2f})."
        },
        {
            "question": "Tôi có thể xem chi tiết sản phẩm khi nào?",
            "answer": "Bạn có thể xem chi tiết sản phẩm bất kỳ lúc nào bằng cách nhấp vào hình ảnh hoặc tên sản phẩm trên trang chủ hoặc trang kết quả tìm kiếm. Chi tiết bao gồm mô tả, giá cả, và các sản phẩm thường được mua cùng."
        }
    ])
    
    # ========== VARIATIONS OF COMMON QUESTIONS ==========
    
    # Add variations of common questions for better training
    qa_variations = []
    for qa in qa_pairs[:]:  # Create a copy to avoid modifying while iterating
        # Generate variations for some questions
        if "nhất" in qa["question"].lower():
            qa_variations.append({
                "question": qa["question"].replace("là gì", "vậy").replace("Sản phẩm", "Hàng hóa"),
                "answer": qa["answer"]
            })
        
        if "trung bình" in qa["question"].lower():
            qa_variations.append({
                "question": qa["question"].replace("trung bình", "thông thường"),
                "answer": qa["answer"]
            })
        
        # Thêm biến thể cho câu hỏi về quốc gia
        if "quốc gia" in qa["question"].lower() and "nhiều nhất" in qa["question"].lower():
            qa_variations.append({
                "question": qa["question"].replace("Quốc gia nào", "Nước nào").replace("nhiều nhất", "phổ biến nhất"),
                "answer": qa["answer"]
            })
            
        # Thêm biến thể cho câu hỏi về sản phẩm mua kèm
        if "Những sản phẩm nào thường được mua cùng với" in qa["question"]:
            product_name = qa["question"].replace("Những sản phẩm nào thường được mua cùng với ", "")
            qa_variations.extend([
                {
                    "question": f"Sản phẩm nào nên mua kèm với {product_name}?",
                    "answer": qa["answer"]
                },
                {
                    "question": f"Khách hàng thường mua gì cùng với {product_name}?",
                    "answer": qa["answer"]
                },
                {
                    "question": f"Đề xuất sản phẩm mua kèm cho {product_name}",
                    "answer": qa["answer"]
                }
            ])
    
    qa_pairs.extend(qa_variations)
    
    # ========== BUSINESS INSIGHTS QUESTIONS ==========
    
    # Add questions that provide business insights
    qa_pairs.extend([
        {
            "question": "Bạn có thể cho tôi biết những hiểu biết sâu sắc về doanh nghiệp của chúng tôi?",
            "answer": f"Dựa trên phân tích dữ liệu, tôi có thể chia sẻ một số hiểu biết sâu sắc: " +
                     f"1) Chúng tôi có {product_stats['total_products']} sản phẩm duy nhất và {product_stats['total_customers']} khách hàng. " +
                     f"2) Sản phẩm phổ biến nhất của chúng tôi là '{top_products[0]['Description']}'. " +
                     f"3) Khách hàng thường mua {avg_stats.get('avg_unique_products', 0):.1f} sản phẩm khác nhau. " +
                     f"4) Mối liên hệ sản phẩm mạnh nhất của chúng tôi là giữa {top_rule['antecedents']} và {top_rule['consequents']}. " +
                     f"5) {top_country['country']} là thị trường lớn nhất của chúng tôi với {top_country['count']} đơn hàng."
        },
        {
            "question": "Làm thế nào để tăng doanh số bán hàng?",
            "answer": "Dựa trên phân tích dữ liệu, bạn có thể cân nhắc: 1) Tạo các gói sản phẩm thường xuyên liên kết với nhau như " +
                     f"{top_rule['antecedents']} và {top_rule['consequents']}. 2) Tập trung nỗ lực tiếp thị vào {month_name[highest_month['month']]} " +
                     "khi doanh số cao nhất. 3) Nhắm mục tiêu vào khách hàng từ " +
                     f"{top_country['country']} nơi chúng tôi có nhiều lượt mua hàng nhất. 4) Quảng bá sản phẩm bán chạy nhất của chúng tôi '{top_products[0]['Description']}'."
        },
        {
            "question": "Tình hình kinh doanh của chúng tôi như thế nào?",
            "answer": f"Doanh nghiệp cho thấy các chỉ số tích cực với {product_stats['total_transactions']} giao dịch từ {product_stats['total_customers']} khách hàng. " +
                     f"Doanh thu đạt đỉnh vào {month_name[highest_month['month']]}. Tần suất mua hàng trung bình là {avg_stats.get('avg_purchase_frequency', 0):.1f} " +
                     f"cho thấy lòng trung thành của khách hàng, mặc dù có thể còn cơ hội để tăng số lượng mua hàng lặp lại. {top_country['country']} là thị trường lớn nhất với {top_country['count']} đơn hàng."
        },
        {
            "question": "Những thông tin thống kê nào về các quốc gia mua hàng?",
            "answer": f"Dựa trên phân tích dữ liệu, {top_country['country']} là quốc gia có nhiều đơn hàng nhất với {top_country['count']} giao dịch. " +
                    f"Trong khi đó, {bottom_country['country']} có ít đơn hàng nhất với chỉ {bottom_country['count']} giao dịch. " +
                    f"Khách hàng từ {top_avg_order_country['country']} có giá trị đơn hàng trung bình cao nhất, khoảng £{top_avg_order_country['average']:.2f} mỗi đơn."
        },
        {
            "question": "Mẫu hình mua sắm nào phổ biến nhất?",
            "answer": f"Mẫu hình mua sắm phổ biến nhất là khi khách hàng mua {top_rule['antecedents']} họ có xu hướng mua thêm {top_rule['consequents']} " +
                    f"với độ tin cậy {top_rule['confidence']*100:.1f}%. Ngoài ra, kết hợp sản phẩm phổ biến nhất là {first_item['itemsets']} " +
                    f"với giá trị hỗ trợ {first_item['support']:.4f}, cho thấy tỷ lệ đáng kể giao dịch chứa các sản phẩm này."
        }
    ])
    
    print(f"Đã tạo {len(qa_pairs)} cặp câu hỏi và trả lời để huấn luyện chatbot")
    
    return qa_pairs

def save_to_excel(qa_pairs, output_file="retail_chatbot_qa_dataset.xlsx"):
    """Save the Q&A pairs to an Excel file"""
    
    # Create a DataFrame from the Q&A pairs
    df = pd.DataFrame(qa_pairs)
    
    # Add a column for potential context/category
    categories = ["Thống kê chung", "Thông tin sản phẩm", "Hành vi khách hàng", 
                 "Phân tích bán hàng", "Đề xuất sản phẩm", "Thông tin doanh nghiệp",
                 "Thống kê theo quốc gia", "Chi tiết sản phẩm", "Sản phẩm mua kèm"]
    
    df["category"] = [random.choice(categories) for _ in range(len(df))]
    
    # Save to Excel
    try:
        df.to_excel(output_file, index=False)
        print(f"Đã lưu bộ dữ liệu Q&A thành công vào {output_file}")
    except Exception as e:
        print(f"Lỗi khi lưu vào Excel: {str(e)}")
        # Try saving to CSV as fallback
        try:
            csv_file = output_file.replace(".xlsx", ".csv")
            df.to_csv(csv_file, index=False)
            print(f"Đã lưu bộ dữ liệu Q&A vào CSV thay thế: {csv_file}")
        except Exception as e2:
            print(f"Không thể lưu bộ dữ liệu: {str(e2)}")

if __name__ == "__main__":
    # Generate the Q&A dataset
    qa_dataset = generate_qa_dataset()
    
    # Save to Excel
    save_to_excel(qa_dataset)
    
    print("Quá trình tạo bộ dữ liệu Q&A đã hoàn tất!")