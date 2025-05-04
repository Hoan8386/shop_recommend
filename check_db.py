from db_connection import check_database_connection

if __name__ == "__main__":
    print("Đang kiểm tra kết nối cơ sở dữ liệu...")
    result = check_database_connection()
    
    if result["connected"]:
        if "error" in result:
            print(f"Kết nối thành công nhưng có lỗi khi truy vấn: {result['error']}")
        else:
            print("Kết nối và truy vấn thành công:")
            print(f"- Số lượng sản phẩm trong bảng products: {result['product_count']}")
            print(f"- Số lượng luật kết hợp trong bảng association_rules: {result['rules_count']}")
            print(f"- Số lượng tập phổ biến trong bảng frequent_itemsets: {result['itemsets_count']}")
            
            if result['product_count'] == 0:
                print("\nCẢNH BÁO: Bảng products không có dữ liệu!")
                print("Bạn cần chạy lại file data_analysis.py để tạo dữ liệu cho các bảng.")
                
            if result['rules_count'] == 0:
                print("\nCẢNH BÁO: Bảng association_rules không có dữ liệu!")
                print("Điều này sẽ khiến tính năng gợi ý sản phẩm không hoạt động.")
    else:
        print(f"Không thể kết nối đến cơ sở dữ liệu: {result['error']}")
        print("\nLỗi này có thể do một trong các nguyên nhân sau:")
        print("1. SQL Server không được khởi động")
        print("2. Thông tin kết nối trong db_connection.py không chính xác")
        print("3. Cơ sở dữ liệu 'shopping' chưa được tạo")
        print("\nHãy kiểm tra và đảm bảo:")
        print("- Dịch vụ SQL Server đang chạy")
        print("- Thông tin kết nối trong db_connection.py là chính xác")
        print("- Có thể đăng nhập vào SQL Server bằng SQL Server Management Studio")