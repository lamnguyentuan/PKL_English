// BIẾN TOÀN CỤC
let currentTopicId = null;
let currentCardData = null; // Lưu dữ liệu thẻ hiện tại
let studiedCardIds = [];    // Danh sách các thẻ đã học trong phiên này (để gửi lên API trừ ra)

document.addEventListener('DOMContentLoaded', function() {
    // 1. Lấy Topic ID từ HTML
    currentTopicId = document.getElementById('topic-id').value;
    
    // 2. Tải thẻ đầu tiên
    loadNextCard();

    // 3. Sự kiện nhấn Enter để nộp bài
    document.getElementById("user-input").addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            submitAnswer();
        }
    });
});

// --- API FUNCTIONS ---

function loadNextCard() {
    // Reset giao diện về mặc định
    resetUI();

    // Tạo chuỗi ID đã học để API loại trừ: ?excluded_ids=1,2,3
    const excludedParam = studiedCardIds.join(',');

    fetch(`/api/study/card/${currentTopicId}/?excluded_ids=${excludedParam}`)
        .then(response => response.json())
        .then(data => {
            if (data.finished) {
                // Nếu API báo hết bài -> Chuyển về Dashboard hoặc hiện thông báo
                alert("Chúc mừng! Bạn đã hoàn thành tất cả từ vựng trong chủ đề này.");
                window.location.href = "/"; // Hoặc trang dashboard
                return;
            }
            
            // Lưu dữ liệu thẻ hiện tại
            currentCardData = data;
            
            // Render dữ liệu lên màn hình
            renderFlashcard(data);
        })
        .catch(err => console.error("Lỗi tải thẻ:", err));
}

function submitAnswer() {
    const userAnswer = document.getElementById('user-input').value;
    const cardId = currentCardData.card_id;

    fetch('/api/study/submit/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken') // Hàm lấy token Django
        },
        body: JSON.stringify({
            card_id: cardId,
            user_answer: userAnswer
        })
    })
    .then(response => response.json())
    .then(result => {
        // Đánh dấu thẻ này đã học xong trong phiên
        if (!studiedCardIds.includes(cardId)) {
            studiedCardIds.push(cardId);
        }

        // Cập nhật Progress bar (Logic đơn giản: đếm số thẻ đã qua)
        updateProgressBar();

        if (result.is_correct) {
            showCorrectScreen();
        } else {
            showWrongScreen(result);
        }
    })
    .catch(err => console.error("Lỗi nộp bài:", err));
}

function saveToNotebook() {
    if (!currentCardData) return;

    fetch('/api/notebook/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            vocabulary_id: currentCardData.vocabulary_id,
            note: "Lưu từ màn hình học"
        })
    })
    .then(res => {
        if (res.ok) alert("Đã lưu vào sổ tay!");
        else alert("Lỗi khi lưu sổ tay");
    });
}

// --- UI FUNCTIONS ---

function renderFlashcard(data) {
    // Điền thông tin Flashcard
    document.getElementById('fc-front-word').innerText = data.word;
    document.getElementById('fc-back-word').innerText = data.word;
    document.getElementById('fc-phonetic').innerText = `/${data.phonetic}/`;
    document.getElementById('fc-definition').innerText = data.definition;

    // Xử lý Audio Flashcard
    const fcAudioDiv = document.getElementById('fc-audio-container');
    const fcAudioSrc = document.getElementById('fc-audio-src');
    if (data.audio) {
        fcAudioDiv.style.display = 'block';
        fcAudioSrc.src = data.audio;
    } else {
        fcAudioDiv.style.display = 'none';
    }

    // Điền thông tin Quiz (ẩn sẵn để dùng sau)
    document.getElementById('quiz-instruction').innerText = data.instruction;
    
    // Ảnh
    const quizImg = document.getElementById('quiz-image');
    if (data.image) {
        quizImg.src = data.image;
        quizImg.classList.remove('d-none');
    } else {
        quizImg.classList.add('d-none');
    }

    // Audio Quiz
    const quizAudioDiv = document.getElementById('quiz-audio-container');
    const quizAudioSrc = document.getElementById('quiz-audio-src');
    if (data.type === 'listening' && data.audio) {
        quizAudioDiv.classList.remove('d-none');
        quizAudioSrc.src = data.audio;
    } else {
        quizAudioDiv.classList.add('d-none');
    }

    // Text Quiz (Điền từ)
    const quizContent = document.getElementById('quiz-content');
    if (data.content) {
        quizContent.innerText = data.content;
        quizContent.classList.remove('d-none');
    } else {
        quizContent.classList.add('d-none');
    }

    // Hiện màn hình Flashcard
    showScreen('screen-flashcard');
}

function startQuiz() {
    showScreen('screen-quiz');
    // Focus vào ô input và xóa nội dung cũ
    const input = document.getElementById('user-input');
    input.value = '';
    input.focus();
}

function showCorrectScreen() {
    showScreen('screen-correct');
    playSuccessSound(); // Tùy chọn nếu bạn có âm thanh
}

function showWrongScreen(result) {
    // Điền thông tin đáp án đúng
    document.getElementById('wrong-correct-word').innerText = result.word;
    document.getElementById('wrong-meaning').innerText = result.meaning;
    showScreen('screen-wrong');
}

// --- HELPER FUNCTIONS ---

function toggleCard() {
    document.getElementById('my-card').classList.toggle('flipped');
}

function showScreen(screenId) {
    // Ẩn tất cả các màn hình
    ['screen-flashcard', 'screen-quiz', 'screen-correct', 'screen-wrong'].forEach(id => {
        document.getElementById(id).classList.add('d-none');
    });
    // Hiện màn hình cần thiết
    document.getElementById(screenId).classList.remove('d-none');
}

function resetUI() {
    // Lật thẻ về mặt trước
    document.getElementById('my-card').classList.remove('flipped');
}

function playAudio(elementId) {
    const audio = document.getElementById(elementId);
    if (audio) audio.play();
}

function updateProgressBar() {
    // Giả lập progress bar (bạn có thể cải tiến logic này bằng cách lấy total từ API)
    const progressBar = document.getElementById('progress-bar');
    let currentWidth = parseInt(progressBar.style.width) || 0;
    if (currentWidth < 100) {
        progressBar.style.width = (currentWidth + 10) + '%';
    }
}

// Hàm lấy CSRF Token mặc định của Django
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