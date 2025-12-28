document.addEventListener('DOMContentLoaded', function() {
    fetchTopics();
});

function fetchTopics() {
    fetch('/api/topics/')
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            renderTopics(data);
        })
        .catch(error => {
            console.error('Lỗi tải chủ đề:', error);
            document.getElementById('topic-list-container').innerHTML = `
                <div class="text-center text-danger py-5">
                    <i class="fas fa-exclamation-triangle fa-2x mb-3"></i>
                    <p>Không thể tải danh sách chủ đề. Vui lòng thử lại sau.</p>
                </div>
            `;
        });
}

function renderTopics(topics) {
    const container = document.getElementById('topic-list-container');
    container.innerHTML = ''; // Xóa loading spinner

    // 1. Kiểm tra nếu danh sách trống
    if (topics.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="fas fa-book-open fa-3x mb-3"></i>
                <p>Chưa có chủ đề nào. Vui lòng liên hệ admin để thêm chủ đề.</p>
            </div>
        `;
        return;
    }

    // 2. Duyệt qua từng topic và tạo HTML
    topics.forEach(topic => {
        // Xử lý ảnh (nếu có ảnh thì dùng thẻ img, không thì dùng icon chữ cái đầu)
        let imageHtml = '';
        if (topic.image) {
            imageHtml = `
                <img src="${topic.image}" 
                     class="rounded-circle" 
                     width="60" height="60" 
                     style="object-fit: cover" />
            `;
        } else {
            // Lấy chữ cái đầu của title
            const firstLetter = topic.title ? topic.title.charAt(0).toUpperCase() : '?';
            imageHtml = `
                <div class="rounded-circle d-flex align-items-center justify-content-center text-white fw-bold topic-icon">
                    ${firstLetter}
                </div>
            `;
        }

        // Xử lý progress (nếu API chưa trả về thì mặc định là 0)
        const progress = topic.progress || 0;

        // Tạo chuỗi HTML (Template String)
        // Lưu ý đường dẫn href: trỏ về trang HTML study_page.html mà ta đã làm
        // Giả sử URL trang học là /study/<id>/
        const html = `
        <a href="/study/${topic.id}/" class="text-decoration-none">
            <div class="card p-3 hover-effect">
                <div class="d-flex align-items-center">
                    <div class="me-3">
                        ${imageHtml}
                    </div>

                    <div class="flex-grow-1">
                        <div class="d-flex justify-content-between align-items-center">
                            <h5 class="fw-bold text-dark mb-1">${topic.title}</h5>
                            <span class="badge bg-light text-dark border">${progress}%</span>
                        </div>
                        <small class="text-muted d-block mb-2">
                            ${topic.description ? truncateString(topic.description, 50) : ''}
                        </small>

                        <div class="progress" style="height: 6px">
                            <div class="progress-bar bg-primary" 
                                 role="progressbar" 
                                 style="width: ${progress}%" 
                                 aria-valuenow="${progress}" 
                                 aria-valuemin="0" 
                                 aria-valuemax="100">
                            </div>
                        </div>
                    </div>

                    <div class="ms-3 text-muted">
                        <i class="fas fa-chevron-right"></i>
                    </div>
                </div>
            </div>
        </a>
        `;

        // Thêm vào container
        container.insertAdjacentHTML('beforeend', html);
    });
}

// Hàm phụ trợ cắt chuỗi (thay thế cho filter truncatewords của Django)
function truncateString(str, num) {
    if (str.length <= num) return str;
    return str.slice(0, num) + '...';
}