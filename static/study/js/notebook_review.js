// ==========================================
// Notebook Review JavaScript
// ==========================================

// --- KHAI BÁO BIẾN ---
const screenQuestion = document.getElementById('screen-question');
const screenCorrect = document.getElementById('screen-correct');
const screenWrong = document.getElementById('screen-wrong');
const btnCheck = document.getElementById('btn-check');
const btnCheckFill = document.getElementById('btn-check-fill');
const userInput = document.getElementById('user-input');

// Đọc dữ liệu từ data container
const questionData = document.getElementById('question-data');
const questionType = questionData.dataset.type;
const currentVocabId = questionData.dataset.vocabId;
const csrfToken = questionData.dataset.csrf;
const submitUrl = document.getElementById('submit-url').dataset.url;

let selectedVocabId = null;
let isCorrect = false;

// --- KHỞI TẠO ---
document.addEventListener('DOMContentLoaded', function() {
    // Add click handlers to option buttons
    document.querySelectorAll('.option-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            selectOption(this, parseInt(this.dataset.vocabId), this.dataset.isCorrect === 'true');
        });
    });

    // Tự động phát audio khi vào trang (chỉ với listening)
    if (questionType === 'listening') {
        setTimeout(playAudio, 500);
    } else if (userInput) {
        userInput.focus();
    }

    // Bắt Enter cho fill_blank
    if (userInput) {
        userInput.addEventListener("keypress", function(event) {
            if (event.key === "Enter") submitFillBlankAnswer();
        });
    }
});

// --- PHÁT AUDIO ---
function playAudio() {
    const audio = document.getElementById('question-audio');
    if (audio && audio.src) {
        audio.play();
        // Animation cho nút
        const btn = document.getElementById('btn-audio');
        if (btn) {
            btn.classList.add('animate__animated', 'animate__pulse');
            setTimeout(() => {
                btn.classList.remove('animate__animated', 'animate__pulse');
            }, 1000);
        }
    }
}

// --- CHỌN ĐÁP ÁN ---
function selectOption(btn, vocabId, correct) {
    // Bỏ chọn tất cả
    document.querySelectorAll('.option-btn').forEach(b => {
        b.classList.remove('btn-primary', 'text-white');
        b.classList.add('btn-outline-secondary');
    });
    
    // Chọn option này
    btn.classList.remove('btn-outline-secondary');
    btn.classList.add('btn-primary', 'text-white');
    
    selectedVocabId = vocabId;
    isCorrect = correct;
    if (btnCheck) btnCheck.disabled = false;
}

// --- NỘP BÀI LISTENING ---
function submitListeningAnswer() {
    if (!selectedVocabId) return;
    
    btnCheck.disabled = true;
    
    fetch(submitUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({ 
            vocabulary_id: currentVocabId, 
            selected_id: selectedVocabId,
            question_type: 'listening'
        })
    })
    .then(res => res.json())
    .then(data => {
        screenQuestion.classList.add('hidden');
        if (data.is_correct) {
            screenCorrect.classList.remove('hidden');
        } else {
            screenWrong.classList.remove('hidden');
        }
    });
}

// --- NỘP BÀI FILL BLANK ---
function submitFillBlankAnswer() {
    const answer = userInput.value.trim();
    if (!answer) return;
    
    btnCheckFill.disabled = true;
    
    fetch(submitUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({ 
            vocabulary_id: currentVocabId, 
            user_answer: answer,
            question_type: 'fill_blank'
        })
    })
    .then(res => res.json())
    .then(data => {
        screenQuestion.classList.add('hidden');
        if (data.is_correct) {
            screenCorrect.classList.remove('hidden');
        } else {
            screenWrong.classList.remove('hidden');
        }
    });
}

// --- BỎ QUA CÂU HỎI ---
function skipQuestion() {
    fetch(submitUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({ 
            vocabulary_id: currentVocabId, 
            selected_id: -1
        })
    })
    .then(() => {
        // Thêm ?continue=1 để giữ session khi chuyển câu
        window.location.href = window.location.pathname + '?continue=1';
    });
}

// --- TIẾP TỤC ---
function nextQuestion() {
    // Thêm ?continue=1 để giữ session khi chuyển câu
    window.location.href = window.location.pathname + '?continue=1';
}
