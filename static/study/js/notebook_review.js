// BIẾN TOÀN CỤC
let currentQuestion = null; // Lưu dữ liệu câu hỏi hiện tại
let reviewedIds = [];       // Danh sách ID các từ đã ôn trong phiên
let selectedOptionId = null; // ID đáp án người dùng chọn (cho bài nghe)

document.addEventListener('DOMContentLoaded', function() {
    loadNextQuestion();

    // Sự kiện Enter cho ô input (bài điền từ)
    const input = document.getElementById("user-input");
    if (input) {
        input.addEventListener("keypress", function(event) {
            if (event.key === "Enter") {
                submitAnswer();
            }
        });
        
        // Mở nút kiểm tra khi có nhập liệu
        input.addEventListener("input", function() {
            const btn = document.getElementById('btn-check');
            if (this.value.trim().length > 0) {
                btn.removeAttribute('disabled');
            } else {
                btn.setAttribute('disabled', 'true');
            }
        });
    }
});

// --- API FUNCTIONS ---

function loadNextQuestion() {
    showScreen('screen-loading');
    
    // Tạo tham số excluded_ids để API không trả về câu hỏi trùng
    const excludedParam = reviewedIds.join(',');

    fetch(`/api/notebook-review/question/?excluded_ids=${excludedParam}`)
        .then(response => response.json())
        .then(data => {
            if (data.finished) {
                showScreen('screen-finished');
                return;
            }
            
            currentQuestion = data;
            renderQuestion(data);
        })
        .catch(err => {
            console.error("Lỗi tải câu hỏi:", err);
            // Nếu lỗi (VD: server 500), thử reload lại sau 2s hoặc báo lỗi
            alert("Có lỗi xảy ra, vui lòng thử lại!");
        });
}

function submitAnswer() {
    if (!currentQuestion) return;

    let payload = {
        vocabulary_id: currentQuestion.vocabulary_id,
        type: currentQuestion.type
    };

    // Lấy đáp án tùy theo loại câu hỏi
    if (currentQuestion.type === 'fill_blank') {
        const val = document.getElementById('user-input').value;
        if (!val.trim()) return;
        payload.user_answer = val;
    } else {
        // Listening
        if (!selectedOptionId) return;
        payload.selected_id = selectedOptionId;
    }

    // Gọi API chấm điểm
    fetch('/api/notebook-review/submit/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(result => {
        // Đánh dấu đã ôn
        if (!reviewedIds.includes(currentQuestion.vocabulary_id)) {
            reviewedIds.push(currentQuestion.vocabulary_id);
        }
        
        // Cập nhật progress bar giả lập
        updateProgressBar();

        // Hiển thị kết quả
        if (result.is_correct) {
            showResultScreen('screen-correct');
        } else {
            showResultScreen('screen-wrong');
        }
    });
}

// --- UI FUNCTIONS ---

function renderQuestion(data) {
    // Reset inputs
    document.getElementById('user-input').value = '';
    selectedOptionId = null;
    document.getElementById('btn-check').setAttribute('disabled', 'true');

    // Điền hướng dẫn
    document.getElementById('q-instruction').innerText = data.instruction;

    // Xử lý Audio
    const audioDiv = document.getElementById('q-audio-container');
    const audioSrc = document.getElementById('q-audio-src');
    
    // Xử lý Options (Listening) vs Input (Fill Blank)
    const optionsDiv = document.getElementById('q-options-container');
    const inputEl = document.getElementById('user-input');
    const contentEl = document.getElementById('q-content');

    if (data.type === 'listening') {
        // Hiện Audio
        audioDiv.classList.remove('d-none');
        audioSrc.src = data.audio;
        // Tự động phát nếu muốn: audioSrc.play().catch(()=>{});

        // Ẩn Fill blank
        inputEl.classList.add('d-none');
        contentEl.classList.add('d-none');
        
        // Hiện Options
        optionsDiv.classList.remove('d-none');
        optionsDiv.innerHTML = ''; // Xóa cũ
        
        // Tạo các nút đáp án
        if (data.options) {
            data.options.forEach((opt, index) => {
                const btn = document.createElement('button');
                btn.className = 'btn btn-outline-secondary py-3 px-4 rounded-pill text-start option-btn';
                btn.innerHTML = `<span class="badge bg-light text-dark me-2">${index + 1}</span> ${opt.word}`;
                btn.onclick = () => selectOption(btn, opt.vocabulary_id);
                optionsDiv.appendChild(btn);
            });
        }

    } else {
        // Fill Blank
        audioDiv.classList.add('d-none');
        optionsDiv.classList.add('d-none');
        
        // Hiện Input & Nội dung câu
        inputEl.classList.remove('d-none');
        contentEl.classList.remove('d-none');
        contentEl.innerText = data.content;
        
        // Focus vào input
        setTimeout(() => inputEl.focus(), 100);
    }

    showScreen('screen-question');
}

function selectOption(btnElement, vocabId) {
    // Xóa class active ở các nút khác
    document.querySelectorAll('.option-btn').forEach(b => {
        b.classList.remove('active', 'btn-primary');
        b.classList.add('btn-outline-secondary');
    });

    // Active nút này
    btnElement.classList.remove('btn-outline-secondary');
    btnElement.classList.add('active', 'btn-primary'); // CSS bootstrap

    selectedOptionId = vocabId;
    document.getElementById('btn-check').removeAttribute('disabled');
}

function showResultScreen(screenId) {
    // Điền thông tin từ vựng vào màn hình kết quả
    // Lưu ý: API submit trả về is_correct, nhưng ta dùng data từ currentQuestion để hiển thị
    const prefix = screenId === 'screen-correct' ? 'res-correct' : 'res-wrong';
    
    document.getElementById(`${prefix}-word`).innerText = currentQuestion.word;
    document.getElementById(`${prefix}-phonetic`).innerText = `/${currentQuestion.phonetic}/`;
    document.getElementById(`${prefix}-def`).innerText = currentQuestion.definition || currentQuestion.meaning;

    showScreen(screenId);
}

function skipQuestion() {
    // Coi như sai -> Hiện đáp án đúng
    showResultScreen('screen-wrong');
}

function showScreen(screenId) {
    ['screen-loading', 'screen-finished', 'screen-question', 'screen-correct', 'screen-wrong'].forEach(id => {
        document.getElementById(id).classList.add('d-none');
    });
    document.getElementById(screenId).classList.remove('d-none');
}

function playAudio(id) {
    const el = document.getElementById(id);
    if(el) el.play();
}

function updateProgressBar() {
    const bar = document.getElementById('progress-bar');
    let w = parseInt(bar.style.width) || 0;
    if (w < 100) bar.style.width = (w + 10) + '%';
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