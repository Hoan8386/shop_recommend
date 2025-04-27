# Tài liệu API Phân tích Dữ liệu Bán lẻ

Tài liệu này mô tả chi tiết các API và các biến được sử dụng trong ứng dụng phân tích dữ liệu bán lẻ.

## Giới thiệu

Hệ thống API phân tích dữ liệu bán lẻ được phát triển để xử lý và trực quan hóa dữ liệu từ tập dữ liệu Online Retail. API cung cấp các phương thức để phân tích:
- Thống kê mô tả về sản phẩm và khách hàng
- Hành vi mua sắm của khách hàng
- Chuỗi mua sắm phổ biến
- Tương quan giữa các sản phẩm
- Tập phổ biến và gợi ý sản phẩm

## Cấu trúc dữ liệu

Dữ liệu Online Retail bao gồm các cột sau:
- **InvoiceNo**: Mã hóa đơn (chuỗi)
- **StockCode**: Mã sản phẩm (chuỗi)
- **Description**: Mô tả sản phẩm (chuỗi)
- **Quantity**: Số lượng sản phẩm (số nguyên)
- **InvoiceDate**: Ngày hóa đơn (datetime)
- **UnitPrice**: Giá đơn vị (số thực)
- **CustomerID**: Mã khách hàng (số nguyên)
- **Country**: Quốc gia (chuỗi)

Các biến được tính toán bổ sung:
- **TotalPrice**: Giá trị đơn hàng (Quantity * UnitPrice)
- **Month**, **Year**, **Day**, **DayOfWeek**, **Quarter**: Các thành phần thời gian trích xuất từ InvoiceDate

## Chi tiết API

### 1. Thống kê Sản phẩm

**Endpoint:** `/product-statistics`  
**Method:** GET  
**Mô tả:** Cung cấp thống kê tổng quan về sản phẩm và giao dịch.

**Các biến trả về:**
- `total_products`: Tổng số sản phẩm duy nhất
- `total_customers`: Tổng số khách hàng
- `total_transactions`: Tổng số giao dịch
- `avg_products_per_transaction`: Số sản phẩm trung bình mỗi giao dịch
- `avg_quantity_per_transaction`: Số lượng sản phẩm trung bình mỗi giao dịch
- `top_products_by_quantity`: Danh sách 10 sản phẩm bán chạy nhất theo số lượng
- `top_products_by_customers`: Danh sách 10 sản phẩm được nhiều khách hàng mua nhất

**Ví dụ phản hồi:**
```json
{
  "total_products": 4070,
  "total_customers": 4372,
  "total_transactions": 22190,
  "avg_products_per_transaction": 8.37,
  "avg_quantity_per_transaction": 24.56,
  "top_products_by_quantity": [
    {
      "Description": "WHITE HANGING HEART T-LIGHT HOLDER",
      "TotalQuantity": 2369
    },
    ...
  ],
  "top_products_by_customers": [
    {
      "Description": "JUMBO BAG RED RETROSPOT",
      "CustomerCount": 952
    },
    ...
  ]
}
```

### 2. Hành vi Mua sắm

**Endpoint:** `/shopping-behavior`  
**Method:** GET  
**Mô tả:** Phân tích hành vi mua sắm của khách hàng.

**Các biến trả về:**
- `purchase_frequency_distribution`: Phân phối tần suất mua hàng (số lần mua → số lượng khách hàng)
- `product_variety_distribution`: Phân phối số lượng sản phẩm khác nhau mỗi khách hàng mua
- `spending_distribution`: Phân phối chi tiêu của khách hàng (rất thấp, thấp, trung bình, cao, rất cao)
- `average_stats`: Thống kê trung bình
  - `avg_purchase_frequency`: Tần suất mua hàng trung bình
  - `avg_total_spent`: Tổng chi tiêu trung bình mỗi khách hàng
  - `avg_unique_products`: Số lượng sản phẩm khác nhau trung bình mỗi khách hàng mua
  - `median_purchase_frequency`: Trung vị tần suất mua hàng
  - `median_total_spent`: Trung vị chi tiêu mỗi khách hàng

**Ví dụ phản hồi:**
```json
{
  "purchase_frequency_distribution": {
    "1": 1549,
    "2": 726,
    ...
  },
  "product_variety_distribution": {
    "1": 354,
    "2": 283,
    ...
  },
  "spending_distribution": {
    "Very Low": 874,
    "Low": 874,
    "Medium": 875,
    "High": 874,
    "Very High": 875
  },
  "average_stats": {
    "avg_purchase_frequency": 4.23,
    "avg_total_spent": 1902.44,
    "avg_unique_products": 53.27,
    "median_purchase_frequency": 2.0,
    "median_total_spent": 659.25
  }
}
```

### 3. Chuỗi Mua sắm

**Endpoint:** `/shopping-sequences`  
**Method:** GET  
**Mô tả:** Phân tích chuỗi mua sắm của khách hàng.

**Các biến trả về:**
- `customer_sequences`: Chuỗi mua sắm của top 5 khách hàng theo số lượng giao dịch
- `common_shopping_patterns`: Các mẫu mua sắm phổ biến dựa trên luật kết hợp

**Ví dụ phản hồi:**
```json
{
  "customer_sequences": {
    "14911": [
      {
        "invoice": "536365",
        "date": "2010-12-01",
        "products": ["WHITE HANGING HEART T-LIGHT HOLDER", "WHITE METAL LANTERN"]
      },
      ...
    ],
    ...
  },
  "common_shopping_patterns": [
    {
      "antecedents": "ROUND SNACK BOXES SET OF 4 FRUITS",
      "consequents": "LUNCH BAG RED RETROSPOT",
      "support": 0.0058,
      "confidence": 0.5534,
      "lift": 3.8937
    },
    ...
  ]
}
```

### 4. Phân tích Tương quan

**Endpoint:** `/correlation-analysis`  
**Method:** GET  
**Mô tả:** Phân tích tương quan giữa các biến và sản phẩm.

**Các biến trả về:**
- `variable_correlation`: Ma trận tương quan giữa các biến Quantity, UnitPrice, TotalPrice
- `product_correlations`: Các cặp sản phẩm thường được mua cùng nhau

**Ví dụ phản hồi:**
```json
{
  "variable_correlation": {
    "Quantity": {
      "Quantity": 1.0,
      "UnitPrice": -0.0438,
      "TotalPrice": 0.2827
    },
    "UnitPrice": {
      "Quantity": -0.0438,
      "UnitPrice": 1.0,
      "TotalPrice": 0.6945
    },
    "TotalPrice": {
      "Quantity": 0.2827,
      "UnitPrice": 0.6945,
      "TotalPrice": 1.0
    }
  },
  "product_correlations": [
    {
      "product1": "ASSORTED COLOUR BIRD ORNAMENT",
      "product2": "ROUND STORAGE JAR GREEN FLOWERS",
      "co_occurrence": 76
    },
    ...
  ]
}
```

### 5. Chuỗi Mua sắm Phổ biến

**Endpoint:** `/common-shopping-patterns`  
**Method:** GET  
**Mô tả:** Trả về top 10 chuỗi mua sắm phổ biến dựa trên luật kết hợp.

**Các biến trả về:**
- `mua_truoc`: Sản phẩm khách hàng mua trước (antecedents)
- `mua_sau`: Sản phẩm khách hàng mua sau (consequents)
- `ho_tro`: Mức độ hỗ trợ (support) - tỷ lệ giao dịch chứa cả hai sản phẩm
- `do_tin_cay`: Độ tin cậy (confidence) - xác suất có mua_sau khi đã mua mua_truoc
- `do_nang`: Độ nâng (lift) - mức độ tăng xác suất mua mua_sau khi đã mua mua_truoc

**Ví dụ phản hồi:**
```json
[
  {
    "mua_truoc": "GREEN REGENCY TEACUP AND SAUCER",
    "mua_sau": "PINK REGENCY TEACUP AND SAUCER",
    "ho_tro": 0.0042,
    "do_tin_cay": 0.6471,
    "do_nang": 69.834
  },
  ...
]
```

### 6. Sản phẩm Thường Được Mua Cùng Nhau

**Endpoint:** `/frequently-bought-together`  
**Method:** GET  
**Mô tả:** Trả về top 20 cặp sản phẩm thường được mua cùng nhau.

**Các biến trả về:**
- `san_pham_1`: Sản phẩm thứ nhất
- `san_pham_2`: Sản phẩm thứ hai
- `so_lan_mua_chung`: Số lần hai sản phẩm được mua cùng nhau

**Ví dụ phản hồi:**
```json
[
  {
    "san_pham_1": "JUMBO BAG RED RETROSPOT",
    "san_pham_2": "LUNCH BAG RED RETROSPOT",
    "so_lan_mua_chung": 112
  },
  ...
]
```

### 7. Gợi ý và Tập phổ biến

**Endpoint:** `/recommendation`  
**Method:** GET  
**Mô tả:** Trả về các tập phổ biến và luật kết hợp.

**Các biến trả về:**
- `frequent_itemsets`: Các tập sản phẩm thường được mua cùng nhau
  - `itemsets`: Danh sách sản phẩm trong tập
  - `support`: Mức độ hỗ trợ (tỷ lệ giao dịch chứa tập sản phẩm)
- `association_rules`: Các luật kết hợp giữa các sản phẩm
  - `antecedents`: Sản phẩm điều kiện
  - `consequents`: Sản phẩm kết quả
  - `support`: Mức độ hỗ trợ
  - `confidence`: Độ tin cậy
  - `lift`: Độ nâng

**Ví dụ phản hồi:**
```json
{
  "frequent_itemsets": [
    {
      "itemsets": ["JUMBO BAG RED RETROSPOT"],
      "support": 0.0548
    },
    ...
  ],
  "association_rules": [
    {
      "antecedents": ["LUNCH BAG RED RETROSPOT"],
      "consequents": ["JUMBO BAG RED RETROSPOT"],
      "support": 0.0083,
      "confidence": 0.3475,
      "lift": 6.3434
    },
    ...
  ]
}
```

### 8. Gợi ý cho Sản phẩm Cụ thể

**Endpoint:** `/recommend-for-product/{product}`  
**Method:** GET  
**Mô tả:** Trả về các gợi ý sản phẩm dựa trên một sản phẩm cụ thể.

**Tham số:**
- `product`: Tên sản phẩm cần tìm gợi ý (chuỗi, được mã hóa URL)

**Các biến trả về:**
- `product`: Tên sản phẩm đã tìm kiếm
- `total_matching_invoices`: Tổng số hóa đơn có chứa sản phẩm
- `recommendations`: Danh sách các sản phẩm được gợi ý
  - `Description`: Tên sản phẩm
  - `InvoiceNo`: Số lần mua chung
  - `Quantity`: Tổng số lượng bán ra
  - `confidence`: Độ tin cậy (tỷ lệ mua sản phẩm này khi đã mua sản phẩm tìm kiếm)
  - `ImagePath`: Đường dẫn hình ảnh sản phẩm (nếu có)

**Ví dụ phản hồi:**
```json
{
  "product": "RED HANGING HEART",
  "total_matching_invoices": 187,
  "recommendations": [
    {
      "Description": "WHITE HANGING HEART T-LIGHT HOLDER",
      "InvoiceNo": 53,
      "Quantity": 416,
      "confidence": 0.2834,
      "ImagePath": "imagesProduct/WHITE HANGING HEART T-LIGHT HOLDER.jpg"
    },
    ...
  ]
}
```

## Các thuật toán chính được sử dụng

### 1. Phân tích tập phổ biến (Apriori)
Thuật toán Apriori được sử dụng để tìm các tập phổ biến - các sản phẩm thường được mua cùng nhau:
- **Min support**: 0.02 (xuất hiện trong ít nhất 2% giao dịch)
- **Phương pháp tính toán**: Các sản phẩm được mã hóa thành ma trận giỏ hàng nhị phân (0/1)

### 2. Luật kết hợp (Association Rules)
Các luật kết hợp được tạo ra từ các tập phổ biến, mô tả mối quan hệ "nếu mua A thì sẽ mua B":
- **Min lift**: 1.0 (chỉ quan tâm đến các luật có tác động tích cực)
- **Metrics chính**: Support, Confidence, Lift

### 3. Ma trận mua chung (Co-purchase Matrix)
Phân tích mức độ các sản phẩm được mua cùng nhau trong cùng một hóa đơn.

## Cách triển khai và sử dụng

1. Đảm bảo Flask API đang chạy:
   ```
   python api.py
   ```

2. Truy cập các endpoint API qua URL:
   ```
   http://127.0.0.1:5000/product-statistics
   http://127.0.0.1:5000/shopping-behavior
   ...
   ```

3. Mở file `index.html` để xem dashboard trực quan phân tích dữ liệu.

## Các biến quan trọng và ý nghĩa

### Biến thống kê

| Biến | Ý nghĩa |
|------|---------|
| Support (Hỗ trợ) | Tỷ lệ giao dịch chứa tập sản phẩm nhất định |
| Confidence (Độ tin cậy) | Xác suất có sản phẩm B khi đã mua sản phẩm A |
| Lift (Độ nâng) | Mức độ gia tăng xác suất có B khi đã có A |

### Biến phân tích hành vi

| Biến | Ý nghĩa |
|------|---------|
| Purchase Frequency | Số lần mua hàng của mỗi khách hàng |
| Average Items | Số lượng sản phẩm trung bình mỗi khách hàng mua |
| Spending Groups | Phân loại khách hàng theo mức chi tiêu |

### Biến phân tích tương quan

| Biến | Ý nghĩa |
|------|---------|
| Correlation Matrix | Ma trận tương quan giữa các biến số học |
| Co-occurrence | Số lần hai sản phẩm xuất hiện cùng nhau |

## Lưu ý

- Dữ liệu đã được làm sạch để loại bỏ giao dịch bị hủy (InvoiceNo bắt đầu bằng "C")
- Các khách hàng không có CustomerID đã bị loại bỏ
- Chỉ giao dịch có Quantity > 0 và UnitPrice > 0 được giữ lại