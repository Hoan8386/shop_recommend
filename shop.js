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
    const orderHistoryNav = document.getElementById('order-history-nav');
    const forYouSection = document.getElementById('for-you-section');

    if (currentUser) {
        loginBtn.textContent = `👤 ${currentUser.name}`;
        loginBtn.onclick = logout;
        registerBtn.textContent = 'Đăng xuất';
        registerBtn.onclick = logout;
        orderHistoryNav.style.display = 'block';

        // Hiển thị phần For You nếu người dùng đã đăng nhập
        forYouSection.style.display = 'block';
        // Cập nhật tên người dùng trong phần For You
        document.getElementById('for-you-user-name').textContent = currentUser.name;
        // Tải gợi ý cá nhân hóa
        loadPersonalizedRecommendations();
    } else {
        loginBtn.textContent = 'Đăng nhập';
        loginBtn.onclick = () => new bootstrap.Modal(document.getElementById('loginModal')).show();
        registerBtn.textContent = 'Đăng ký';
        registerBtn.onclick = () => new bootstrap.Modal(document.getElementById('registerModal')).show();
        orderHistoryNav.style.display = 'none';

        // Ẩn phần For You nếu chưa đăng nhập
        forYouSection.style.display = 'none';
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
        // Gọi API đăng nhập thực tế
        const response = await fetch(`${API_URL}/api/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.message || 'Đăng nhập thất bại');
        }

        // Lưu thông tin người dùng và token
        currentUser = data.user;
        localStorage.setItem('user', JSON.stringify(currentUser));
        localStorage.setItem('token', data.token);

        updateAuthUI();
        bootstrap.Modal.getInstance(document.getElementById('loginModal')).hide();

        // Đồng bộ giỏ hàng từ server sau khi đăng nhập
        syncCartAfterLogin();

        alert('Đăng nhập thành công!');
    } catch (error) {
        alert(error.message || 'Đăng nhập thất bại. Vui lòng thử lại.');
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
        // Gọi API đăng ký thực tế
        const response = await fetch(`${API_URL}/api/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, email, password })
        });

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.message || 'Đăng ký thất bại');
        }

        // Lưu thông tin người dùng và token
        currentUser = data.user;
        localStorage.setItem('user', JSON.stringify(currentUser));
        localStorage.setItem('token', data.token);

        updateAuthUI();
        bootstrap.Modal.getInstance(document.getElementById('registerModal')).hide();
        alert('Đăng ký thành công!');
    } catch (error) {
        alert(error.message || 'Đăng ký thất bại. Vui lòng thử lại.');
    }
});

// Đăng xuất
window.logout = function () {
    currentUser = null;
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    // Xóa giỏ hàng khi đăng xuất
    cart = [];
    localStorage.removeItem('cart');
    updateCartCount();
    updateAuthUI();
    alert('Đã đăng xuất!');
};

// Đồng bộ giỏ hàng từ server sau khi đăng nhập
async function syncCartAfterLogin() {
    try {
        const token = localStorage.getItem('token');
        if (!token) return;

        // Lấy giỏ hàng từ server
        const response = await fetch(`${API_URL}/api/cart`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Không thể lấy thông tin giỏ hàng');
        }

        const data = await response.json();

        if (data.success && data.items && Array.isArray(data.items)) {
            // Chuyển đổi format giỏ hàng từ server sang local
            cart = data.items.map(item => ({
                id: item.description,
                qty: item.quantity,
                price: item.price,
                cart_item_id: item.cart_item_id,
                product_id: item.product_id
            }));

            localStorage.setItem('cart', JSON.stringify(cart));
            updateCartCount();
        }
    } catch (error) {
        console.error('Lỗi khi đồng bộ giỏ hàng:', error);
        // Không hiển thị thông báo lỗi để không làm phiền người dùng
    }
}

// Tải gợi ý sản phẩm cá nhân hóa cho người dùng
async function loadPersonalizedRecommendations() {
    if (!currentUser) return;

    try {
        // Hiển thị trạng thái loading
        document.getElementById('for-you-loading').style.display = 'block';
        const forYouList = document.getElementById('for-you-list');
        forYouList.innerHTML = '<div class="col-12 text-center"><p>Đang tải gợi ý cá nhân hóa...</p></div>';

        // Gọi API để lấy gợi ý cá nhân hóa dựa trên lịch sử mua hàng
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_URL}/api/recommendations/personalized`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Không thể tải gợi ý cá nhân hóa');
        }

        const data = await response.json();

        // Ẩn icon loading
        document.getElementById('for-you-loading').style.display = 'none';

        // Kiểm tra số lượng sản phẩm API trả về
        console.log('API trả về số lượng sản phẩm gợi ý:', data.recommendations ? data.recommendations.length : 0);

        // Hiển thị gợi ý nếu có
        if (!data.success || !data.recommendations || data.recommendations.length === 0) {
            forYouList.innerHTML = '<div class="col-12 text-center"><p class="text-muted">Chưa có gợi ý nào dành cho bạn. Hãy mua sắm thêm để nhận gợi ý phù hợp!</p></div>';
            return;
        }

        forYouList.innerHTML = '';

        // Hiển thị tất cả 8 sản phẩm trong một grid 4x2
        const recommendProducts = data.recommendations.slice(0, 8);
        recommendProducts.forEach(product => {
            const card = document.createElement('div');
            // Sử dụng col-6 col-sm-4 col-md-3 để đảm bảo hiển thị 4 sản phẩm trên một hàng ở màn hình trung bình trở lên
            card.className = 'col-6 col-sm-4 col-md-3 mb-3';
            const defaultImage = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTUwIiBoZWlnaHQ9IjE1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTUwIiBoZWlnaHQ9IjE1MCIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9Ijc1IiB5PSI3NSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiBmaWxsPSIjOTk5IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+Tm8gSW1hZ2U8L3RleHQ+PC9zdmc+';

            const description = product.Description || '';
            const price = parseFloat(product.UnitPrice || 0);
            const stockCode = product.StockCode || '';
            const score = product.recommendation_score || 0;
            const scoreDisplay = Math.round(score * 100);
            const imagePath = `imagesProduct/${encodeURIComponent(description)}.jpg`;

            card.innerHTML = `
                <div class="product-card border-primary h-100">
                    <div class="position-absolute top-0 end-0 p-2">
                        <span class="badge bg-primary">${scoreDisplay}% phù hợp</span>
                    </div>
                    <div class="text-center mb-2">
                        <img src="${imagePath}" 
                             class="product-image" 
                             alt="${description}" 
                             onerror="this.src='${defaultImage}'"
                             loading="lazy">
                    </div>
                    <div class="d-flex flex-column flex-grow-1">
                        <div class="product-title" title="${description}">${truncateText(description, 35)}</div>
                        <div class="text-danger fw-bold mb-2">${numberWithCommas(price)}đ</div>
                        <div class="text-muted small mb-2">Mã SP: ${stockCode}</div>
                        <div class="mt-auto">
                            <button class="btn btn-outline-primary w-100 btn-sm mb-1" onclick="showProductDetail('${description}', 'for-you')">Chi tiết</button>
                            <button class="btn btn-success w-100 btn-sm" onclick="addToCart('${description}', 1, ${price})">
                                <i class="bi bi-cart-plus"></i> Thêm vào giỏ
                            </button>
                        </div>
                    </div>
                </div>
            `;
            forYouList.appendChild(card);
        });
    } catch (error) {
        console.error('Lỗi khi tải gợi ý cá nhân hóa:', error);
        document.getElementById('for-you-loading').style.display = 'none';
        document.getElementById('for-you-list').innerHTML = '<div class="col-12 text-center text-danger">Đã xảy ra lỗi khi tải gợi ý sản phẩm. Vui lòng thử lại sau.</div>';
    }
}

// Cập nhật hàm renderPagination để nhận tham số container
function renderPagination(container) {
    const paginationContainer = document.createElement('div');
    paginationContainer.className = 'd-flex justify-content-center mt-4';

    let html = `
        <nav aria-label="Page navigation">
            <ul class="pagination">
                <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                    <a class="page-link" href="#" onclick="return changePage(${currentPage - 1})">Trước</a>
                </li>
    `;

    if (totalPages <= 7) {
        // Nếu tổng số trang <= 7, hiển thị tất cả các trang
        for (let i = 1; i <= totalPages; i++) {
            html += `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="return changePage(${i})">${i}</a>
                </li>
            `;
        }
    } else {
        // Nếu tổng số trang > 7, hiển thị một số trang và dấu "..."
        if (currentPage <= 3) {
            // Các trang đầu
            for (let i = 1; i <= 5; i++) {
                html += `
                    <li class="page-item ${i === currentPage ? 'active' : ''}">
                        <a class="page-link" href="#" onclick="return changePage(${i})">${i}</a>
                    </li>
                `;
            }
            html += `
                <li class="page-item disabled"><span class="page-link">...</span></li>
                <li class="page-item">
                    <a class="page-link" href="#" onclick="return changePage(${totalPages})">${totalPages}</a>
                </li>
            `;
        } else if (currentPage >= totalPages - 2) {
            // Các trang cuối
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
            // Ở giữa
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

// Thêm sản phẩm vào giỏ hàng
window.addToCart = async function (id, quantity = 1, price = 0) {
    if (!currentUser) {
        alert('Vui lòng đăng nhập để thêm sản phẩm vào giỏ hàng!');
        new bootstrap.Modal(document.getElementById('loginModal')).show();
        return;
    }

    try {
        const token = localStorage.getItem('token');
        if (!token) {
            throw new Error('Vui lòng đăng nhập lại');
        }

        // Tìm product_id từ description (id)
        let productId = null;

        // Tìm product_id từ danh sách sản phẩm đã hiển thị
        const allProductsResponse = await fetch(`${API_URL}/api/product-info?description=${encodeURIComponent(id)}`);
        if (allProductsResponse.ok) {
            const productData = await allProductsResponse.json();
            if (productData.success && productData.product) {
                productId = productData.product.ProductId;
            }
        }

        if (!productId) {
            throw new Error('Không tìm thấy thông tin sản phẩm');
        }

        // Gọi API thêm vào giỏ hàng
        const response = await fetch(`${API_URL}/api/cart/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                product_id: productId,
                quantity: parseInt(quantity)
            })
        });

        if (!response.ok) {
            throw new Error('Không thể thêm vào giỏ hàng');
        }

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.message || 'Không thể thêm vào giỏ hàng');
        }

        // Cập nhật giỏ hàng local từ dữ liệu server
        cart = data.items.map(item => ({
            id: item.description,
            qty: item.quantity,
            price: item.price,
            cart_item_id: item.cart_item_id,
            product_id: item.product_id
        }));

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

    } catch (error) {
        console.error('Lỗi khi thêm vào giỏ hàng:', error);
        alert(error.message || 'Không thể thêm vào giỏ hàng. Vui lòng thử lại sau.');
    }
};

// Cập nhật số lượng sản phẩm trong giỏ hàng
window.updateCartItemQuantity = async function (id, newQuantity) {
    newQuantity = parseInt(newQuantity);
    if (newQuantity < 1) return;

    try {
        const token = localStorage.getItem('token');
        if (!token) {
            throw new Error('Vui lòng đăng nhập lại');
        }

        // Tìm cart_item_id từ id (description)
        const cartItem = cart.find(item => item.id === id);
        if (!cartItem || !cartItem.cart_item_id) {
            throw new Error('Không tìm thấy sản phẩm trong giỏ hàng');
        }

        // Gọi API cập nhật giỏ hàng
        const response = await fetch(`${API_URL}/api/cart/update`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                cart_item_id: cartItem.cart_item_id,
                quantity: newQuantity
            })
        });

        if (!response.ok) {
            throw new Error('Không thể cập nhật giỏ hàng');
        }

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.message || 'Không thể cập nhật giỏ hàng');
        }

        // Cập nhật giỏ hàng local từ dữ liệu server
        cart = data.items.map(item => ({
            id: item.description,
            qty: item.quantity,
            price: item.price,
            cart_item_id: item.cart_item_id,
            product_id: item.product_id
        }));

        localStorage.setItem('cart', JSON.stringify(cart));
        updateCartCount();
        updateCartDisplay();

    } catch (error) {
        console.error('Lỗi khi cập nhật giỏ hàng:', error);
        alert(error.message || 'Không thể cập nhật giỏ hàng. Vui lòng thử lại sau.');
    }
};

// Xóa sản phẩm khỏi giỏ hàng
window.removeFromCart = async function (id) {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            throw new Error('Vui lòng đăng nhập lại');
        }

        // Tìm cart_item_id từ id (description)
        const cartItem = cart.find(item => item.id === id);
        if (!cartItem || !cartItem.cart_item_id) {
            throw new Error('Không tìm thấy sản phẩm trong giỏ hàng');
        }

        // Gọi API xóa sản phẩm khỏi giỏ hàng
        const response = await fetch(`${API_URL}/api/cart/remove?cart_item_id=${cartItem.cart_item_id}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Không thể xóa sản phẩm khỏi giỏ hàng');
        }

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.message || 'Không thể xóa sản phẩm khỏi giỏ hàng');
        }

        // Cập nhật giỏ hàng local từ dữ liệu server
        cart = data.items.map(item => ({
            id: item.description,
            qty: item.quantity,
            price: item.price,
            cart_item_id: item.cart_item_id,
            product_id: item.product_id
        }));

        localStorage.setItem('cart', JSON.stringify(cart));
        updateCartCount();
        updateCartDisplay();

    } catch (error) {
        console.error('Lỗi khi xóa sản phẩm khỏi giỏ hàng:', error);
        alert(error.message || 'Không thể xóa sản phẩm khỏi giỏ hàng. Vui lòng thử lại sau.');
    }
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
window.checkout = async function () {
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
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                throw new Error('Vui lòng đăng nhập lại');
            }

            // Gọi API tạo đơn hàng
            const response = await fetch(`${API_URL}/api/orders/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error('Không thể tạo đơn hàng');
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.message || 'Không thể tạo đơn hàng');
            }

            // Đơn hàng đã được tạo thành công, xóa giỏ hàng local
            cart = [];
            localStorage.setItem('cart', JSON.stringify(cart));
            updateCartCount();

            // Đóng modal giỏ hàng
            const cartModal = bootstrap.Modal.getInstance(document.getElementById('cartModal'));
            if (cartModal) {
                cartModal.hide();
            }

            alert(`Đặt hàng thành công! Mã đơn hàng của bạn là: ${data.order_id}`);

        } catch (error) {
            console.error('Lỗi khi tạo đơn hàng:', error);
            alert(error.message || 'Không thể tạo đơn hàng. Vui lòng thử lại sau.');
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
                        <button class="btn btn-outline-primary w-100 mb-2" onclick="showProductDetail('${description}', 'bestseller')">Xem chi tiết</button>
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
                    <div class="text-muted small mb-2">Còn lại: ${quantity}</div>
                    <div class="mt-auto">
                        <button class="btn btn-outline-primary w-100 mb-2" onclick="showProductDetail('${description}', 'all-products')">Xem chi tiết</button>
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

// Hiển thị chi tiết sản phẩm
window.showProductDetail = async function (description, sourceSection = null) {
    try {
        // Hiển thị loading trước khi gọi API
        const productModal = new bootstrap.Modal(document.getElementById('productModal'));

        // Hiển thị thông tin sản phẩm trong modal trước khi gọi API
        document.getElementById('modalProductName').textContent = description;
        // Xóa thông tin số lượng đã mua cũ (nếu có)
        document.getElementById('user-purchase-info').textContent = '';

        // Lấy thông tin sản phẩm từ API để có dữ liệu chính xác
        let productInfoResponse;
        try {
            // Truy vấn API để lấy thông tin đầy đủ và chính xác về sản phẩm
            productInfoResponse = await fetch(`${API_URL}/api/product-info?description=${encodeURIComponent(description)}`);
            if (!productInfoResponse.ok) {
                throw new Error('Không thể lấy thông tin sản phẩm');
            }
        } catch (error) {
            console.warn('Không thể lấy thông tin sản phẩm từ API:', error);
            // Tiếp tục với cách cũ nếu API chuyên biệt không tồn tại
        }

        // Tìm giá của sản phẩm
        let price = 0;
        let productDetail = null;

        // Cách 1: Nếu có API chuyên biệt, lấy giá từ API
        if (productInfoResponse && productInfoResponse.ok) {
            const productInfo = await productInfoResponse.json();
            if (productInfo && productInfo.product) {
                productDetail = productInfo.product;
                price = parseFloat(productDetail.UnitPrice || 0);
                console.log('Lấy giá từ API product-info:', price);
            }
        }

        // Cách 2: Nếu không có API chuyên biệt, tìm trong danh sách sản phẩm đã load
        if (!productDetail) {
            // Tìm trong danh sách sản phẩm đã được hiển thị trên trang
            // Tìm trong all-products-list
            const allProductCards = document.querySelectorAll('#all-products-list .product-card');
            for (const card of allProductCards) {
                const titleEl = card.querySelector('.product-title');
                if (titleEl && titleEl.title === description) {
                    const priceEl = card.querySelector('.text-danger');
                    if (priceEl) {
                        // Lấy giá từ text và chuyển đổi sang số (loại bỏ định dạng)
                        const priceText = priceEl.textContent;
                        price = parseFloat(priceText.replace(/[^\d]/g, ''));
                        console.log('Lấy giá từ all-products-list:', price);
                        break;
                    }
                }
            }

            // Nếu không tìm thấy trong all-products-list, tìm trong best-seller-list
            if (price === 0) {
                const bestSellerCards = document.querySelectorAll('#best-seller-list .product-card');
                for (const card of bestSellerCards) {
                    const titleEl = card.querySelector('.product-title');
                    if (titleEl && titleEl.title === description) {
                        const priceEl = card.querySelector('.text-danger');
                        if (priceEl) {
                            const priceText = priceEl.textContent;
                            price = parseFloat(priceText.replace(/[^\d]/g, ''));
                            console.log('Lấy giá từ best-seller-list:', price);
                            break;
                        }
                    }
                }
            }
        }

        // Nếu vẫn không tìm thấy giá, sử dụng giá mặc định hợp lý
        if (price === 0) {
            // Đặt giá mặc định nếu không tìm thấy
            price = 150000; // Một giá trị mặc định hợp lý
            console.log('Sử dụng giá mặc định:', price);
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

        // Lấy thông tin số lượng đã mua của khách hàng hiện tại
        if (currentUser) {
            try {
                const token = localStorage.getItem('token');
                if (token) {
                    // Gọi API để lấy số lượng đã mua của sản phẩm này
                    const userPurchaseResponse = await fetch(`${API_URL}/api/user/purchase-history?product=${encodeURIComponent(description)}`, {
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });

                    if (userPurchaseResponse.ok) {
                        const purchaseData = await userPurchaseResponse.json();
                        if (purchaseData.success && typeof purchaseData.quantity === 'number') {
                            if (purchaseData.quantity > 0) {
                                document.getElementById('user-purchase-info').textContent =
                                    `Bạn đã mua ${purchaseData.quantity} sản phẩm này`;
                            } else {
                                document.getElementById('user-purchase-info').textContent =
                                    'Bạn chưa từng mua sản phẩm này';
                            }
                        }
                    }
                }
            } catch (error) {
                console.warn('Không thể lấy thông tin số lượng đã mua:', error);
            }
        }

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

        // Xác định nguồn gọi nếu không được chỉ định rõ
        if (!sourceSection) {
            // Kiểm tra xem sản phẩm có nằm trong phần nào của trang
            const forYouItems = document.querySelectorAll('#for-you-list .product-title');
            let isFromForYou = false;
            
            for (const item of forYouItems) {
                if (item.title === description) {
                    isFromForYou = true;
                    break;
                }
            }
            
            if (isFromForYou) {
                sourceSection = 'for-you';
            }
        }

        // Dựa vào nguồn gọi để quyết định API phù hợp
        const token = localStorage.getItem('token');
        let apiUrl;
        let apiOptions = {};
        let apiSource;

        if (sourceSection === 'for-you' || (currentUser && sourceSection === 'personal')) {
            // Nếu từ phần For You hoặc yêu cầu cá nhân hóa rõ ràng, dùng API cá nhân hóa
            apiUrl = `${API_URL}/api/personal-product-recommendations/${encodeURIComponent(description)}`;
            apiOptions = {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            };
            apiSource = "lịch sử mua hàng của bạn";
        } else {
            // Nếu từ phần bestsellers hoặc all-products, dùng API gợi ý thông thường
            apiUrl = `${API_URL}/api/recommend-for-product/${encodeURIComponent(description)}`;
            apiSource = "dữ liệu chung";
        }

        console.log(`Đang gọi API từ nguồn: ${apiSource}, URL: ${apiUrl}`);
        
        try {
            const response = await fetch(apiUrl, apiOptions);
            
            if (!response.ok) {
                throw new Error('Không thể tải gợi ý sản phẩm');
            }
            
            const data = await response.json();

            // Hiển thị gợi ý
            displayRecommendations(data, apiSource);
        } catch (error) {
            console.error('Lỗi khi tải gợi ý sản phẩm:', error);
            
            // Nếu là API cá nhân hóa gặp lỗi, thử dùng API thông thường
            if (sourceSection === 'for-you' || sourceSection === 'personal') {
                try {
                    console.log('Dự phòng: Đang gọi API gợi ý thông thường');
                    const fallbackUrl = `${API_URL}/api/recommend-for-product/${encodeURIComponent(description)}`;
                    const fallbackResponse = await fetch(fallbackUrl);
                    
                    if (fallbackResponse.ok) {
                        const fallbackData = await fallbackResponse.json();
                        displayRecommendations(fallbackData, "dữ liệu chung (dự phòng)");
                        return;
                    }
                } catch (fallbackError) {
                    console.error('Lỗi khi gọi API dự phòng:', fallbackError);
                }
            }
            
            // Hiển thị thông báo lỗi nếu cả hai API đều thất bại
            recommendList.innerHTML = '<div class="col-12 text-center text-danger">Đã xảy ra lỗi khi tải đề xuất sản phẩm. Vui lòng thử lại sau.</div>';
        }
        
        // Hàm hiển thị gợi ý
        function displayRecommendations(data, source) {
            console.log('Dữ liệu từ API gợi ý:', data.recommendations);
            
            // Cập nhật gợi ý sản phẩm sau khi có dữ liệu
            recommendList.innerHTML = '';

            if (!data.recommendations || data.recommendations.length === 0) {
                recommendList.innerHTML = '<div class="col-12 text-center">Không có sản phẩm gợi ý.</div>';
            } else {
                // Thêm header hiển thị nguồn dữ liệu
                const recommendHeader = document.createElement('div');
                recommendHeader.className = 'col-12 mb-2';
                recommendHeader.innerHTML = `<h6 class="text-primary">Sản phẩm thường mua cùng (dựa trên ${source}):</h6>`;
                recommendList.appendChild(recommendHeader);

                // Hiển thị tối đa 6 sản phẩm đề xuất để tránh quá nhiều render
                const limitedRecommendations = data.recommendations.slice(0, 6);
                limitedRecommendations.forEach(rec => {
                    // Lấy giá trị thực tế từ API cho confidence
                    const confidence = typeof rec.confidence === 'number' && !isNaN(rec.confidence)
                        ? rec.confidence
                        : 0;

                    // Chuyển đổi thành phần trăm nếu nhỏ hơn 1
                    const displayConfidence = confidence <= 1 ? (confidence * 100) : confidence;

                    // Chỉ hiển thị lift nếu giá trị khác 1.00 và hợp lệ
                    const hasValidLift = typeof rec.lift === 'number' && !isNaN(rec.lift) && rec.lift > 0 && Math.abs(rec.lift - 1.0) > 0.01;
                    const lift = hasValidLift ? rec.lift : 0;

                    const recImagePath = `imagesProduct/${encodeURIComponent(rec.Description)}.jpg`;
                    const col = document.createElement('div');
                    col.className = 'col-6 col-md-4 mb-2';
                    col.innerHTML = `
                        <div class="border rounded p-2 text-center">
                            <img src="${recImagePath}" class="product-image mb-1" style="width:80px;height:80px;object-fit:cover" 
                                onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAiIGhlaWdodD0iODAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjgwIiBoZWlnaHQ9IjgwIiBmaWxsPSIjZWVlIi8+PHRleHQgeD0iNDAiIHk9IjQwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTIiIGZpbGw9IiM5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5ObyBJbWFnZTwvdGV4dD48L3N2Zz4='"
                                loading="lazy" />
                            <div style="font-size:13px">${truncateText(rec.Description, 30)}</div>
                            <div class="text-muted small">Tỷ lệ mua kèm: ${displayConfidence.toFixed(1)}%</div>
                            ${hasValidLift ? `<div class="text-muted small">Độ liên quan: ${lift.toFixed(2)}</div>` : ''}
                            <button class="btn btn-sm btn-outline-success mt-1" onclick="showProductDetail('${rec.Description}', '${source.includes('của bạn') ? 'personal' : 'general'}')">Xem</button>
                        </div>
                    `;
                    recommendList.appendChild(col);
                });
            }
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

    // Đăng ký sự kiện cho nút xem lịch sử đơn hàng
    document.getElementById('order-history-btn').addEventListener('click', openOrderHistory);
});

// Mở modal lịch sử đơn hàng
async function openOrderHistory() {
    if (!currentUser) {
        alert('Vui lòng đăng nhập để xem lịch sử đơn hàng!');
        new bootstrap.Modal(document.getElementById('loginModal')).show();
        return;
    }

    // Hiển thị modal trước khi tải dữ liệu
    const orderHistoryModal = new bootstrap.Modal(document.getElementById('orderHistoryModal'));
    orderHistoryModal.show();

    // Hiển thị loading
    document.getElementById('orders-loading').style.display = 'block';
    document.getElementById('orders-list-container').style.display = 'none';
    document.getElementById('no-orders').style.display = 'none';

    try {
        const token = localStorage.getItem('token');
        if (!token) {
            throw new Error('Vui lòng đăng nhập lại');
        }

        // Gọi API lấy danh sách đơn hàng
        const response = await fetch(`${API_URL}/api/orders`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Không thể lấy lịch sử đơn hàng');
        }

        const data = await response.json();

        // Ẩn loading
        document.getElementById('orders-loading').style.display = 'none';

        if (!data.success || !data.orders || data.orders.length === 0) {
            document.getElementById('no-orders').style.display = 'block';
            return;
        }

        // Hiển thị danh sách đơn hàng
        document.getElementById('orders-list-container').style.display = 'block';
        renderOrderHistory(data.orders);

    } catch (error) {
        console.error('Lỗi khi lấy lịch sử đơn hàng:', error);
        document.getElementById('orders-loading').style.display = 'none';
        document.getElementById('no-orders').style.display = 'block';
        document.getElementById('no-orders').innerHTML = `
            <i class="bi bi-exclamation-triangle" style="font-size: 48px;"></i>
            <p class="mt-3">Đã xảy ra lỗi khi tải lịch sử đơn hàng. Vui lòng thử lại sau.</p>
        `;
    }
}

// Hiển thị danh sách đơn hàng
function renderOrderHistory(orders) {
    const ordersList = document.getElementById('order-history-list');
    ordersList.innerHTML = '';

    orders.forEach(order => {
        const tr = document.createElement('tr');

        // Lấy ngày tháng từ created_at
        const orderDate = new Date(order.created_at);
        const formattedDate = orderDate.toLocaleDateString('vi-VN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });

        // Xác định màu badge dựa trên trạng thái đơn hàng
        let statusClass = 'bg-secondary'; // Mặc định
        switch (order.status?.toLowerCase()) {
            case 'pending':
                statusClass = 'bg-warning text-dark';
                break;
            case 'completed':
                statusClass = 'bg-success';
                break;
            case 'cancelled':
                statusClass = 'bg-danger';
                break;
            case 'processing':
                statusClass = 'bg-info';
                break;
            case 'delivered':
                statusClass = 'bg-primary';
                break;
        }

        // Dịch trạng thái sang tiếng Việt
        let statusText = 'Chưa xác định';
        switch (order.status?.toLowerCase()) {
            case 'pending':
                statusText = 'Chờ xác nhận';
                break;
            case 'completed':
                statusText = 'Hoàn thành';
                break;
            case 'cancelled':
                statusText = 'Đã hủy';
                break;
            case 'processing':
                statusText = 'Đang xử lý';
                break;
            case 'delivered':
                statusText = 'Đã giao hàng';
                break;
        }

        tr.innerHTML = `
            <td>#${order.order_id}</td>
            <td>${formattedDate}</td>
            <td>${numberWithCommas(order.total_amount)}đ</td>
            <td><span class="badge ${statusClass}">${statusText}</span></td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="showOrderDetail(${order.order_id})">
                    Chi tiết
                </button>
            </td>
        `;

        ordersList.appendChild(tr);
    });
}

// Hiển thị chi tiết đơn hàng
window.showOrderDetail = async function (orderId) {
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            throw new Error('Vui lòng đăng nhập lại');
        }

        // Đóng modal lịch sử đơn hàng
        bootstrap.Modal.getInstance(document.getElementById('orderHistoryModal')).hide();

        // Hiển thị modal chi tiết đơn hàng với trạng thái loading
        document.getElementById('detail-order-id').textContent = orderId;
        document.getElementById('detail-order-date').textContent = 'Đang tải...';
        document.getElementById('detail-order-status').textContent = 'Đang tải...';
        document.getElementById('detail-order-status').className = 'badge bg-secondary';
        document.getElementById('detail-order-total').textContent = 'Đang tải...';
        document.getElementById('order-items-list').innerHTML = `
            <tr>
            <td colspan="4" class="text-center">
                <div class="spinner-border spinner-border-sm text-primary" role="status">
                    <span class="visually-hidden">Đang tải...</span>
                </div>
                Đang tải thông tin đơn hàng...
            </td>
            </tr>
        `;

        const orderDetailModal = new bootstrap.Modal(document.getElementById('orderDetailModal'));
        orderDetailModal.show();

        // Gọi API lấy chi tiết đơn hàng
        const response = await fetch(`${API_URL}/api/orders/${orderId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Không thể lấy chi tiết đơn hàng');
        }

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.message || 'Không thể lấy chi tiết đơn hàng');
        }

        // Cập nhật thông tin đơn hàng
        const orderDate = new Date(data.created_at);
        document.getElementById('detail-order-date').textContent = orderDate.toLocaleDateString('vi-VN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });

        // Xác định màu badge và text cho trạng thái
        let statusClass = 'bg-secondary';
        let statusText = 'Chưa xác định';

        switch (data.status?.toLowerCase()) {
            case 'pending':
                statusClass = 'bg-warning text-dark';
                statusText = 'Chờ xác nhận';
                break;
            case 'completed':
                statusClass = 'bg-success';
                statusText = 'Hoàn thành';
                break;
            case 'cancelled':
                statusClass = 'bg-danger';
                statusText = 'Đã hủy';
                break;
            case 'processing':
                statusClass = 'bg-info';
                statusText = 'Đang xử lý';
                break;
            case 'delivered':
                statusClass = 'bg-primary';
                statusText = 'Đã giao hàng';
                break;
        }

        document.getElementById('detail-order-status').textContent = statusText;
        document.getElementById('detail-order-status').className = `badge ${statusClass}`;
        document.getElementById('detail-order-total').textContent = `${numberWithCommas(data.total_amount)}đ`;

        // Hiển thị danh sách sản phẩm trong đơn hàng
        const itemsList = document.getElementById('order-items-list');
        itemsList.innerHTML = '';

        if (!data.items || data.items.length === 0) {
            itemsList.innerHTML = '<tr><td colspan="4" class="text-center">Không có sản phẩm nào trong đơn hàng</td></tr>';
        } else {
            data.items.forEach(item => {
                const tr = document.createElement('tr');
                const subtotal = item.price * item.quantity;

                tr.innerHTML = `
                    <td>
                    <div class="d-flex align-items-center">
                        <img src="${item.image_path || `imagesProduct/${encodeURIComponent(item.product_name)}.jpg`}"
                            class="me-2" style="width: 50px; height: 50px; object-fit: cover"
                            onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNTAiIGhlaWdodD0iNTAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjUwIiBoZWlnaHQ9IjUwIiBmaWxsPSIjZWVlIi8+PHRleHQgeD0iMjUiIHk9IjI1IiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iOCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPk5vIEltYWdlPC90ZXh0Pjwvc3ZnPg=='">
                            <div>${item.product_name}</div>
                    </div>
                    </td>
                    <td>${item.quantity}</td>
                    <td>${numberWithCommas(item.price)}đ</td>
                    <td>${numberWithCommas(subtotal)}đ</td>
                `;

                itemsList.appendChild(tr);
            });
        }

    } catch (error) {
        console.error('Lỗi khi lấy chi tiết đơn hàng:', error);
        document.getElementById('order-items-list').innerHTML = `
            <tr>
            <td colspan="4" class="text-center text-danger">
                <i class="bi bi-exclamation-triangle me-1"></i>
                Đã xảy ra lỗi khi tải thông tin đơn hàng. Vui lòng thử lại sau.
            </td>
            </tr>
        `;
    }
};

// Quay lại danh sách đơn hàng
window.backToOrderHistory = function () {
    // Đóng modal chi tiết đơn hàng
    bootstrap.Modal.getInstance(document.getElementById('orderDetailModal')).hide();

    // Mở lại modal lịch sử đơn hàng
    new bootstrap.Modal(document.getElementById('orderHistoryModal')).show();
};