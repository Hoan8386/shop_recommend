const API_URL = "http://127.0.0.1:5000";
let products = [];
let cart = JSON.parse(localStorage.getItem('cart') || '[]');
let searchTimeout = null;
let currentUser = JSON.parse(localStorage.getItem('user') || 'null');
let currentProduct = null;
let currentPage = 1;
let totalPages = 1;

// Hàm hỗ trợ cắt văn bản dài
function truncateText(text, maxLength) {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

// Hàm định dạng số có dấu phẩy ngăn cách
function numberWithCommas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Biến lưu trữ bộ lọc
let currentFilters = {
    country: ''
};

// Khởi tạo UI dựa trên trạng thái đăng nhập
function updateAuthUI() {
    const loginBtn = document.getElementById('login-btn');
    const registerBtn = document.getElementById('register-btn');
    const userInfo = document.createElement('div');
    userInfo.className = 'd-flex align-items-center';

    if (currentUser) {
        loginBtn.style.display = 'none';
        registerBtn.style.display = 'none';
        userInfo.innerHTML = `
            <span class="me-2">Xin chào, ${currentUser.name}</span>
            <button class="btn btn-outline-danger btn-sm" onclick="logout()">Đăng xuất</button>
        `;
        document.querySelector('.navbar .d-flex').appendChild(userInfo);
    } else {
        loginBtn.style.display = 'inline-block';
        registerBtn.style.display = 'inline-block';
        const existingUserInfo = document.querySelector('.navbar .d-flex div');
        if (existingUserInfo) existingUserInfo.remove();
    }
}

// Đăng nhập
document.getElementById('login-btn').addEventListener('click', () => {
    new bootstrap.Modal(document.getElementById('loginModal')).show();
});

document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    try {
        // Trong thực tế, bạn sẽ gọi API để xác thực
        // Đây là demo đơn giản
        currentUser = {
            id: 1,
            name: email.split('@')[0],
            email: email
        };
        localStorage.setItem('user', JSON.stringify(currentUser));
        updateAuthUI();
        bootstrap.Modal.getInstance(document.getElementById('loginModal')).hide();
        alert('Đăng nhập thành công!');
    } catch (error) {
        alert('Đăng nhập thất bại. Vui lòng thử lại.');
    }
});

// Đăng ký
document.getElementById('register-btn').addEventListener('click', () => {
    new bootstrap.Modal(document.getElementById('registerModal')).show();
});

document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('register-name').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm-password').value;

    if (password !== confirmPassword) {
        alert('Mật khẩu không khớp!');
        return;
    }

    try {
        // Trong thực tế, bạn sẽ gọi API để đăng ký
        // Đây là demo đơn giản
        currentUser = {
            id: 1,
            name: name,
            email: email
        };
        localStorage.setItem('user', JSON.stringify(currentUser));
        updateAuthUI();
        bootstrap.Modal.getInstance(document.getElementById('registerModal')).hide();
        alert('Đăng ký thành công!');
    } catch (error) {
        alert('Đăng ký thất bại. Vui lòng thử lại.');
    }
});

// Đăng xuất
window.logout = function () {
    currentUser = null;
    localStorage.removeItem('user');
    updateAuthUI();
    alert('Đã đăng xuất!');
};

// Thêm sản phẩm vào giỏ hàng
window.addToCart = function (id, quantity = 1, price = 0) {
    if (!currentUser) {
        alert('Vui lòng đăng nhập để thêm sản phẩm vào giỏ hàng!');
        new bootstrap.Modal(document.getElementById('loginModal')).show();
        return;
    }

    const idx = cart.findIndex(item => item.id === id);
    if (idx >= 0) {
        cart[idx].qty += parseInt(quantity);
    } else {
        cart.push({
            id: id,
            qty: parseInt(quantity),
            price: parseFloat(price)
        });
    }
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartCount();

    // Hiển thị thông báo thành công
    const toastContainer = document.createElement('div');
    toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
    toastContainer.style.zIndex = '5';
    toastContainer.innerHTML = `
        <div class="toast show" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <strong class="me-auto">Thông báo</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                Đã thêm sản phẩm vào giỏ hàng!
            </div>
        </div>
    `;
    document.body.appendChild(toastContainer);

    // Tự động ẩn thông báo sau 3 giây
    setTimeout(() => {
        const toast = document.querySelector('.toast');
        if (toast) {
            const bsToast = new bootstrap.Toast(toast);
            bsToast.hide();
            setTimeout(() => toastContainer.remove(), 500);
        }
    }, 3000);
};

// Cập nhật số lượng sản phẩm trong giỏ hàng
window.updateCartItemQuantity = function (id, newQuantity) {
    newQuantity = parseInt(newQuantity);
    if (newQuantity < 1) return;

    const idx = cart.findIndex(item => item.id === id);
    if (idx >= 0) {
        cart[idx].qty = newQuantity;
        localStorage.setItem('cart', JSON.stringify(cart));
        updateCartCount();
        updateCartDisplay(); // Thay thế openCart() bằng hàm này
    }
};

// Xóa sản phẩm khỏi giỏ hàng
window.removeFromCart = function (id) {
    cart = cart.filter(item => item.id !== id);
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartCount();
    updateCartDisplay(); // Thay thế openCart() bằng hàm này
};

// Hàm mới để cập nhật hiển thị giỏ hàng mà không mở modal mới
function updateCartDisplay() {
    const list = document.getElementById('cart-list');
    list.innerHTML = '';
    let total = 0;

    if (cart.length === 0) {
        list.innerHTML = '<tr><td colspan="5" class="text-center">Giỏ hàng trống</td></tr>';
    } else {
        cart.forEach(item => {
            const tr = document.createElement('tr');
            const subtotal = (item.price || 0) * (item.qty || 0);
            total += subtotal;

            tr.innerHTML = `
                <td>${item.id || ''}</td>
                <td>
                    <div class="input-group input-group-sm" style="width: 120px;">
                        <button class="btn btn-outline-secondary" type="button" onclick="updateCartItemQuantity('${item.id}', ${(item.qty || 0) - 1})">-</button>
                        <input type="number" class="form-control text-center" value="${item.qty || 0}" min="1" onchange="updateCartItemQuantity('${item.id}', this.value)">
                        <button class="btn btn-outline-secondary" type="button" onclick="updateCartItemQuantity('${item.id}', ${(item.qty || 0) + 1})">+</button>
                    </div>
                </td>
                <td>${(item.price || 0).toLocaleString()}đ</td>
                <td>${subtotal.toLocaleString()}đ</td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="removeFromCart('${item.id}')">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
            list.appendChild(tr);
        });
    }

    document.getElementById('cart-total').textContent = total.toLocaleString() + 'đ';
}

// Quản lý số lượng sản phẩm trong modal
window.increaseQuantity = function () {
    const input = document.getElementById('product-quantity');
    input.value = parseInt(input.value) + 1;
};

window.decreaseQuantity = function () {
    const input = document.getElementById('product-quantity');
    if (parseInt(input.value) > 1) {
        input.value = parseInt(input.value) - 1;
    }
};

// Thanh toán giỏ hàng
window.checkout = function () {
    if (!currentUser) {
        alert('Vui lòng đăng nhập để thanh toán!');
        new bootstrap.Modal(document.getElementById('loginModal')).show();
        return;
    }

    if (cart.length === 0) {
        alert('Giỏ hàng của bạn đang trống!');
        return;
    }

    const confirmed = confirm('Xác nhận thanh toán các sản phẩm trong giỏ hàng?');
    if (confirmed) {
        alert('Đặt hàng thành công! Cảm ơn bạn đã mua sắm tại Shop Online.');
        cart = [];
        localStorage.setItem('cart', JSON.stringify(cart));
        updateCartCount();

        // Đóng modal giỏ hàng
        const cartModal = bootstrap.Modal.getInstance(document.getElementById('cartModal'));
        if (cartModal) {
            cartModal.hide();
        }
    }
};

// Hiển thị danh sách sản phẩm bán chạy
async function loadBestSellers() {
    try {
        const response = await fetch(`${API_URL}/api/best-sellers`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        renderBestSellers(data.products);
    } catch (error) {
        console.error('Error loading best sellers:', error);
        document.getElementById('best-seller-list').innerHTML = '<div class="col-12 text-center">Không thể tải sản phẩm bán chạy. Vui lòng thử lại sau.</div>';
    }
}

// Hiển thị các sản phẩm bán chạy
function renderBestSellers(products) {
    const list = document.getElementById('best-seller-list');
    list.innerHTML = '';

    if (!products || products.length === 0) {
        list.innerHTML = '<div class="col-12 text-center">Không có sản phẩm bán chạy.</div>';
        return;
    }

    products.forEach(prod => {
        const card = document.createElement('div');
        card.className = 'col-md-3 mb-4';
        const defaultImage = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTUwIiBoZWlnaHQ9IjE1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTUwIiBoZWlnaHQ9IjE1MCIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9Ijc1IiB5PSI3NSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiBmaWxsPSIjOTk5IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+Tm8gSW1hZ2U8L3RleHQ+PC9zdmc+';

        const description = prod.Description || '';
        // Đảm bảo lấy giá từ đúng trường
        const price = parseFloat(prod.UnitPrice || 0);
        const quantity = parseInt(prod.Quantity || 0);
        const stockCode = prod.StockCode || '';
        const imagePath = `imagesProduct/${encodeURIComponent(description)}.jpg`;

        card.innerHTML = `
            <div class="product-card">
                <div class="text-center mb-3">
                    <img src="${imagePath}" 
                         class="product-image" 
                         alt="${description}" 
                         onerror="this.src='${defaultImage}'"
                         loading="lazy">
                </div>
                <div class="d-flex flex-column flex-grow-1">
                    <div class="product-title" title="${description}">${truncateText(description, 40)}</div>
                    <div class="text-danger fw-bold mb-2">${numberWithCommas(price)}đ</div>
                    <div class="text-muted small mb-2">Mã SP: ${stockCode}</div>
                    <div class="text-muted small mb-2">Đã bán: ${quantity}</div>
                    <div class="mt-auto">
                        <button class="btn btn-outline-primary w-100 mb-2" onclick="showProductDetail('${description}')">Xem chi tiết</button>
                        <button class="btn btn-success w-100" onclick="addToCart('${description}', 1, ${price})">
                            <i class="bi bi-cart-plus"></i> Thêm vào giỏ
                        </button>
                    </div>
                </div>
            </div>
        `;
        list.appendChild(card);
    });
}

// Hiển thị tất cả sản phẩm
async function loadAllProducts(page = 1) {
    try {
        const response = await fetch(`${API_URL}/api/products?page=${page}`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        renderAllProducts(data.products);

        // Cập nhật phân trang nếu cần
        currentPage = data.page || 1;
        totalPages = data.total_pages || 1;
        renderPagination(document.getElementById('all-products-list').parentNode);
    } catch (error) {
        console.error('Error loading all products:', error);
        document.getElementById('all-products-list').innerHTML = '<div class="col-12 text-center">Không thể tải danh sách sản phẩm. Vui lòng thử lại sau.</div>';
    }
}

// Hiển thị danh sách tất cả sản phẩm
function renderAllProducts(products) {
    const list = document.getElementById('all-products-list');
    list.innerHTML = '';

    if (!products || products.length === 0) {
        list.innerHTML = '<div class="col-12 text-center">Không tìm thấy sản phẩm nào.</div>';
        return;
    }

    products.forEach(prod => {
        const card = document.createElement('div');
        card.className = 'col-md-3 mb-4';
        const defaultImage = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTUwIiBoZWlnaHQ9IjE1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTUwIiBoZWlnaHQ9IjE1MCIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9Ijc1IiB5PSI3NSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiBmaWxsPSIjOTk5IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+Tm8gSW1hZ2U8L3RleHQ+PC9zdmc+';

        // Lấy dữ liệu sản phẩm từ API với xử lý chính xác các trường dữ liệu
        const description = prod.Description || '';
        // Đảm bảo lấy giá từ đúng trường và chuyển đổi thành số
        const price = parseFloat(prod.UnitPrice || 0);
        const quantity = parseInt(prod.Quantity || 0);
        const stockCode = prod.StockCode || '';
        const imagePath = `imagesProduct/${encodeURIComponent(description)}.jpg`;

        card.innerHTML = `
            <div class="product-card">
                <div class="text-center mb-3">
                    <img src="${imagePath}" 
                         class="product-image" 
                         alt="${description}" 
                         onerror="this.src='${defaultImage}'"
                         loading="lazy">
                </div>
                <div class="d-flex flex-column flex-grow-1">
                    <div class="product-title" title="${description}">${truncateText(description, 40)}</div>
                    <div class="text-danger fw-bold mb-2">${numberWithCommas(price)}đ</div>
                    <div class="text-muted small mb-2">Mã SP: ${stockCode}</div>
                    <div class="text-muted small mb-2">Đã bán: ${quantity}</div>
                    <div class="mt-auto">
                        <button class="btn btn-outline-primary w-100 mb-2" onclick="showProductDetail('${description}')">Xem chi tiết</button>
                        <button class="btn btn-success w-100" onclick="addToCart('${description}', 1, ${price})">
                            <i class="bi bi-cart-plus"></i> Thêm vào giỏ
                        </button>
                    </div>
                </div>
            </div>
        `;
        list.appendChild(card);
    });
}

// Cập nhật hàm renderPagination để nhận tham số container
function renderPagination(container) {
    if (!container) return;

    const paginationContainer = document.createElement('div');
    paginationContainer.className = 'd-flex justify-content-center mt-4';

    if (totalPages <= 1) return;

    let html = `
        <nav aria-label="Page navigation">
            <ul class="pagination">
                <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                    <a class="page-link" href="#" onclick="return changePage(${currentPage - 1})">Trước</a>
                </li>
    `;

    if (totalPages <= 7) {
        for (let i = 1; i <= totalPages; i++) {
            html += `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="return changePage(${i})">${i}</a>
                </li>
            `;
        }
    } else {
        if (currentPage <= 5) {
            for (let i = 1; i <= 5; i++) {
                html += `
                    <li class="page-item ${i === currentPage ? 'active' : ''}">
                        <a class="page-link" href="#" onclick="return changePage(${i})">${i}</a>
                    </li>
                `;
            }
            html += `
                <li class="page-item disabled"><span class="page-link">...</span></li>
                <li class="page-item ${totalPages === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="return changePage(${totalPages})">${totalPages}</a>
                </li>
            `;
        } else if (currentPage >= totalPages - 4) {
            html += `
                <li class="page-item"><a class="page-link" href="#" onclick="return changePage(1)">1</a></li>
                <li class="page-item disabled"><span class="page-link">...</span></li>
            `;
            for (let i = totalPages - 4; i <= totalPages; i++) {
                html += `
                    <li class="page-item ${i === currentPage ? 'active' : ''}">
                        <a class="page-link" href="#" onclick="return changePage(${i})">${i}</a>
                    </li>
                `;
            }
        } else {
            html += `
                <li class="page-item"><a class="page-link" href="#" onclick="return changePage(1)">1</a></li>
                <li class="page-item disabled"><span class="page-link">...</span></li>
            `;
            for (let i = currentPage - 1; i <= currentPage + 1; i++) {
                html += `
                    <li class="page-item ${i === currentPage ? 'active' : ''}">
                        <a class="page-link" href="#" onclick="return changePage(${i})">${i}</a>
                    </li>
                `;
            }
            html += `
                <li class="page-item disabled"><span class="page-link">...</span></li>
                <li class="page-item ${totalPages === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="return changePage(${totalPages})">${totalPages}</a>
                </li>
            `;
        }
    }

    html += `
                <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                    <a class="page-link" href="#" onclick="return changePage(${currentPage + 1})">Sau</a>
                </li>
            </ul>
        </nav>
    `;

    paginationContainer.innerHTML = html;
    const oldPagination = container.querySelector('.d-flex.justify-content-center.mt-4');
    if (oldPagination) {
        oldPagination.remove();
    }
    container.appendChild(paginationContainer);
}

// Hiển thị chi tiết sản phẩm
window.showProductDetail = async function (description) {
    try {
        // Hiển thị loading trước khi gọi API
        const productModal = new bootstrap.Modal(document.getElementById('productModal'));
        
        // Hiển thị thông tin sản phẩm trong modal trước khi gọi API
        document.getElementById('modalProductName').textContent = description;
        
        // Tìm giá của sản phẩm trong danh sách đã load
        let price = 0;
        const product = products.find(p => p.Description === description);
        if (product) {
            price = parseFloat(product.UnitPrice || 0);
        } else {
            // Tìm trong best sellers nếu không tìm thấy trong products
            const bestSellers = document.getElementById('best-seller-list');
            const bestSellerCards = bestSellers.querySelectorAll('.product-card');
            for (const card of bestSellerCards) {
                const titleEl = card.querySelector('.product-title');
                if (titleEl && titleEl.title === description) {
                    const priceText = card.querySelector('.text-danger').textContent;
                    price = parseFloat(priceText.replace(/[^\d]/g, ''));
                    break;
                }
            }
            
            if (price === 0) {
                // Giá mặc định nếu không tìm thấy
                price = Math.floor(Math.random() * 500000) + 100000;
            }
        }
        
        // Xóa giá cũ (nếu có) khỏi header
        const modalHeader = document.getElementById('modalProductName').closest('.modal-header');
        if (modalHeader.querySelector('.text-danger')) {
            modalHeader.querySelector('.text-danger').remove();
        }
        
        // Thêm giá vào bên dưới hình ảnh và trên số lượng
        const priceContainer = document.createElement('div');
        priceContainer.className = 'text-danger fw-bold mt-2 mb-3';
        priceContainer.style.fontSize = '24px';
        priceContainer.textContent = `${numberWithCommas(price)}đ`;
        
        // Tải hình ảnh sản phẩm
        const imagePath = `imagesProduct/${encodeURIComponent(description)}.jpg`;
        document.getElementById('modalProductImage').src = imagePath;
        document.getElementById('modalProductImage').onerror = function () {
            this.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9IjEwMCIgeT0iMTAwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5ObyBJbWFnZTwvdGV4dD48L3N2Zz4=';
        };
        
        // Thêm giá sau khi hình ảnh được tải
        const imageCol = document.getElementById('modalProductImage').closest('.col-md-4');
        
        // Xóa giá cũ (nếu có)
        const oldPrice = imageCol.querySelector('.text-danger');
        if (oldPrice) {
            oldPrice.remove();
        }
        
        // Thêm giá mới sau hình ảnh
        document.getElementById('modalProductImage').insertAdjacentElement('afterend', priceContainer);
        
        // Reset số lượng
        document.getElementById('product-quantity').value = 1;
        
        // Hiển thị loading cho phần đề xuất
        const recommendList = document.getElementById('recommend-list');
        recommendList.innerHTML = '<div class="col-12 text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Đang tải...</span></div><p>Đang tải sản phẩm đề xuất...</p></div>';
        
        // Hiện modal trước khi gọi API
        productModal.show();
        
        // Cập nhật nút thêm vào giỏ
        document.getElementById('addToCartBtn').onclick = () => {
            const quantity = parseInt(document.getElementById('product-quantity').value);
            addToCart(description, quantity, price);
        };
        
        // Gọi API để lấy sản phẩm gợi ý (không chặn UI)
        const response = await fetch(`${API_URL}/recommend-for-product/${encodeURIComponent(description)}`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        
        // Cập nhật gợi ý sản phẩm sau khi có dữ liệu
        recommendList.innerHTML = '';

        if (!data.recommendations || data.recommendations.length === 0) {
            recommendList.innerHTML = '<div class="col-12 text-center">Không có sản phẩm gợi ý.</div>';
        } else {
            // Hiển thị tối đa 6 sản phẩm đề xuất để tránh quá nhiều render
            const limitedRecommendations = data.recommendations.slice(0, 6);
            limitedRecommendations.forEach(rec => {
                const recImagePath = `imagesProduct/${encodeURIComponent(rec.Description)}.jpg`;
                const col = document.createElement('div');
                col.className = 'col-6 col-md-4 mb-2';
                col.innerHTML = `
                    <div class="border rounded p-2 text-center">
                        <img src="${recImagePath}" class="product-image mb-1" style="width:80px;height:80px;object-fit:cover" 
                             onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAiIGhlaWdodD0iODAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjgwIiBoZWlnaHQ9IjgwIiBmaWxsPSIjZWVlIi8+PHRleHQgeD0iNDAiIHk9IjQwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTIiIGZpbGw9IiM5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5ObyBJbWFnZTwvdGV4dD48L3N2Zz4='" 
                             loading="lazy" />
                        <div style="font-size:13px">${truncateText(rec.Description, 30)}</div>
                        <div class="text-muted small">Tỷ lệ mua kèm: ${(rec.confidence * 100).toFixed(1)}%</div>
                        <button class="btn btn-sm btn-outline-success mt-1" onclick="showProductDetail('${rec.Description}')">Xem</button>
                    </div>
                `;
                recommendList.appendChild(col);
            });
        }
    } catch (error) {
        console.error('Error loading product details:', error);
        // Hiển thị lỗi trong modal thay vì alert
        const recommendList = document.getElementById('recommend-list');
        recommendList.innerHTML = '<div class="col-12 text-center text-danger">Đã xảy ra lỗi khi tải đề xuất sản phẩm. Vui lòng thử lại sau.</div>';
    }
}

// Mở giỏ hàng
function openCart() {
    if (!currentUser) {
        alert('Vui lòng đăng nhập để xem giỏ hàng!');
        new bootstrap.Modal(document.getElementById('loginModal')).show();
        return;
    }

    const list = document.getElementById('cart-list');
    list.innerHTML = '';
    let total = 0;

    if (cart.length === 0) {
        list.innerHTML = '<tr><td colspan="5" class="text-center">Giỏ hàng trống</td></tr>';
    } else {
        cart.forEach(item => {
            const tr = document.createElement('tr');
            const subtotal = (item.price || 0) * (item.qty || 0);
            total += subtotal;

            tr.innerHTML = `
                <td>${item.id || ''}</td>
                <td>
                    <div class="input-group input-group-sm" style="width: 120px;">
                        <button class="btn btn-outline-secondary" type="button" onclick="updateCartItemQuantity('${item.id}', ${(item.qty || 0) - 1})">-</button>
                        <input type="number" class="form-control text-center" value="${item.qty || 0}" min="1" onchange="updateCartItemQuantity('${item.id}', this.value)">
                        <button class="btn btn-outline-secondary" type="button" onclick="updateCartItemQuantity('${item.id}', ${(item.qty || 0) + 1})">+</button>
                    </div>
                </td>
                <td>${(item.price || 0).toLocaleString()}đ</td>
                <td>${subtotal.toLocaleString()}đ</td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="removeFromCart('${item.id}')">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
            list.appendChild(tr);
        });
    }

    document.getElementById('cart-total').textContent = total.toLocaleString() + 'đ';
    new bootstrap.Modal(document.getElementById('cartModal')).show();
}

// Cập nhật số lượng giỏ hàng
function updateCartCount() {
    const cartCount = cart.reduce((total, item) => total + (parseInt(item.qty) || 0), 0);
    document.getElementById('navbar-cart-count').textContent = cartCount;
    document.getElementById('floating-cart-count').textContent = cartCount;
}

// Chuyển trang
window.changePage = function (page) {
    if (page < 1 || page > totalPages) return false;
    loadAllProducts(page);
    window.scrollTo(0, document.getElementById('all-products-list').offsetTop - 100);
    return false;
};

// Sự kiện khi DOM đã tải xong
document.addEventListener('DOMContentLoaded', () => {
    // Khởi tạo
    updateAuthUI();
    updateCartCount();

    // Tải sản phẩm bán chạy
    loadBestSellers();

    // Tải tất cả sản phẩm
    loadAllProducts();

    // Đăng ký sự kiện cho các nút mở giỏ hàng
    document.getElementById('floating-cart-btn').addEventListener('click', openCart);
    document.getElementById('navbar-cart-btn').addEventListener('click', openCart);
});