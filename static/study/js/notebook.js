// Biến toàn cục lưu danh sách để dễ thao tác
let notebookData = [];

document.addEventListener('DOMContentLoaded', function() {
    fetchNotebook();
});

// --- 1. API GET DANH SÁCH ---
function fetchNotebook() {
    fetch('/api/notebook/')
        .then(response => response.json())
        .then(data => {
            notebookData = data;
            renderNotebook(data);
            updateHeader(data.length);
        })
        .catch(err => console.error("Lỗi tải sổ tay:", err));
}

// --- 2. HÀM RENDER UI ---
function renderNotebook(entries) {
    const container = document.getElementById('notebook-list');
    container.innerHTML = ''; // Xóa loading

    if (entries.length === 0) {
        document.getElementById('empty-state').classList.remove('d-none');
        return;
    }
    
    document.getElementById('empty-state').classList.add('d-none');

    entries.forEach(entry => {
        // entry.vocabulary là object con, chứa word, audio, v.v.
        const vocab = entry.vocabulary; 
        const note = entry.note || '';
        
        // Logic hiển thị nút Edit/Display Note
        const noteDisplayClass = note ? '' : 'd-none';
        const addBtnClass = note ? 'd-none' : '';

        const html = `
        <div class="card p-3 shadow-sm" id="entry-${entry.id}">
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <div class="d-flex align-items-center gap-2 mb-2">
                        <h4 class="fw-bold text-primary mb-0">${vocab.word}</h4>
                        <span class="text-muted fst-italic">/${vocab.phonetic}/</span>
                        ${vocab.audio ? `
                        <button onclick="playAudio('${vocab.audio}')" 
                                class="btn btn-sm btn-outline-warning rounded-circle">
                            <i class="fas fa-volume-up"></i>
                        </button>` : ''}
                    </div>
                    <p class="text-dark mb-1">${vocab.meaning_sentence}</p>
                    <small class="text-muted">
                        <i class="fas fa-folder me-1"></i>${vocab.topic_title || 'Từ vựng'}
                    </small>
                    
                    <div class="mt-2">
                        <div class="note-display ${noteDisplayClass}" id="note-display-${entry.id}">
                            <div class="p-2 bg-light rounded d-flex justify-content-between align-items-center">
                                <small class="text-secondary">
                                    <i class="fas fa-sticky-note me-1"></i>
                                    <span class="note-text" id="note-text-${entry.id}">${note}</span>
                                </small>
                                <button onclick="showEditNote(${entry.id})" class="btn btn-sm btn-link text-muted p-0">
                                    <i class="fas fa-edit"></i>
                                </button>
                            </div>
                        </div>

                        <div class="note-edit d-none" id="note-edit-${entry.id}">
                            <div class="input-group">
                                <input type="text" class="form-control form-control-sm" 
                                       id="note-input-${entry.id}" 
                                       value="${note}" placeholder="Thêm ghi chú...">
                                <button onclick="saveNote(${entry.id})" class="btn btn-sm btn-primary">Lưu</button>
                                <button onclick="cancelEditNote(${entry.id})" class="btn btn-sm btn-outline-secondary">Hủy</button>
                            </div>
                        </div>

                        <button onclick="showEditNote(${entry.id})" 
                                class="btn btn-sm btn-link text-muted p-0 add-note-btn ${addBtnClass}" 
                                id="add-note-btn-${entry.id}">
                            <i class="fas fa-plus me-1"></i>Thêm ghi chú
                        </button>
                    </div>
                </div>

                <button onclick="removeEntry(${entry.id})" class="btn btn-outline-danger btn-sm ms-3">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
        `;
        container.insertAdjacentHTML('beforeend', html);
    });
}

function updateHeader(count) {
    const container = document.getElementById('header-actions');
    let html = `<span class="badge bg-primary fs-6">${count} từ</span>`;
    
    // Nếu có từ 2 từ trở lên -> Hiện nút ôn tập
    if (count >= 2) {
        html += `
        <a href="/notebook-review/question/" class="btn btn-warning btn-sm text-white">
            <i class="fas fa-headphones me-1"></i>Ôn tập
        </a>`;
    }
    container.innerHTML = html;
}

// --- 3. CÁC HÀM XỬ LÝ SỰ KIỆN ---

function playAudio(url) {
    const player = document.getElementById('audio-player');
    player.src = url;
    player.play();
}

function removeEntry(id) {
    if (!confirm('Bạn có chắc muốn xóa từ này khỏi sổ tay?')) return;

    fetch(`/api/notebook/${id}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(res => {
        if (res.ok) {
            // Xóa phần tử khỏi giao diện
            document.getElementById(`entry-${id}`).remove();
            // Cập nhật lại số lượng
            notebookData = notebookData.filter(item => item.id !== id);
            updateHeader(notebookData.length);
            
            if (notebookData.length === 0) {
                document.getElementById('empty-state').classList.remove('d-none');
            }
        } else {
            alert('Lỗi khi xóa!');
        }
    });
}

// --- Logic Sửa Ghi chú ---

function showEditNote(id) {
    document.getElementById(`note-display-${id}`).classList.add('d-none');
    document.getElementById(`add-note-btn-${id}`).classList.add('d-none');
    document.getElementById(`note-edit-${id}`).classList.remove('d-none');
    
    // Focus vào ô input
    const input = document.getElementById(`note-input-${id}`);
    input.focus();
}

function cancelEditNote(id) {
    const noteText = document.getElementById(`note-text-${id}`).innerText;
    
    // Reset input về giá trị cũ
    document.getElementById(`note-input-${id}`).value = noteText;
    
    document.getElementById(`note-edit-${id}`).classList.add('d-none');
    
    if (noteText) {
        document.getElementById(`note-display-${id}`).classList.remove('d-none');
    } else {
        document.getElementById(`add-note-btn-${id}`).classList.remove('d-none');
    }
}

function saveNote(id) {
    const newNote = document.getElementById(`note-input-${id}`).value;

    fetch(`/api/notebook/${id}/`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ note: newNote })
    })
    .then(res => res.json())
    .then(data => {
        // Cập nhật UI
        document.getElementById(`note-text-${id}`).innerText = data.note;
        cancelEditNote(id); // Đóng form edit, hiện lại text
    })
    .catch(err => alert("Lỗi cập nhật ghi chú"));
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}