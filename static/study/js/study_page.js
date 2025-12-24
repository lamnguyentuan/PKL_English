// ==========================================
// Study Page JavaScript
// ==========================================

// --- KHAI BÁO BIẾN ---
const screenFlashcard = document.getElementById('screen-flashcard');
const screenQuiz = document.getElementById('screen-quiz');
const screenCorrect = document.getElementById('screen-correct');
const screenWrong = document.getElementById('screen-wrong');
const userInput = document.getElementById('user-input');
const myCard = document.getElementById('my-card');

// Đọc dữ liệu từ data container
const pageData = document.getElementById('page-data');
const submitUrl = pageData.dataset.submitUrl;
const notebookUrl = pageData.dataset.notebookUrl;
const csrfToken = pageData.dataset.csrf;
const cardId = pageData.dataset.cardId;
const topicId = pageData.dataset.topicId;
const vocabId = pageData.dataset.vocabId;

let isFlipped = false;

// --- 1. HÀM LẬT THẺ (Toggle Class) ---
function toggleCard() {
    if (!isFlipped) {
        myCard.classList.add('is-flipped');
        setTimeout(() => { playAudio('fc-audio'); }, 300);
        isFlipped = true;
    } else {
        myCard.classList.remove('is-flipped');
        isFlipped = false;
    }
}

// --- 2. CHUYỂN SANG QUIZ ---
function startQuiz() {
    screenFlashcard.classList.add('hidden'); 
    screenQuiz.classList.remove('hidden');   
    userInput.focus();                       
}

// --- 3. NỘP BÀI (GỌI API) ---
function submitAnswer() {
    const answer = userInput.value.trim();

    if (!answer) return; 

    // Khóa nút để tránh spam click
    document.getElementById('btn-check').disabled = true;

    fetch(submitUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({ card_id: cardId, user_answer: answer, topic_id: topicId })
    })
    .then(res => res.json())
    .then(data => {
        handleResult(data);
    })
    .catch(err => {
        console.error(err);
        alert("Lỗi kết nối server!");
        document.getElementById('btn-check').disabled = false;
    });
}

function handleResult(data) {
    screenQuiz.classList.add('hidden'); 

    if (data.is_correct) {
        screenCorrect.classList.remove('hidden');
    } else {
        screenWrong.classList.remove('hidden');
    }
}

// --- CÁC HÀM TIỆN ÍCH ---
function playAudio(id) {
    const audio = document.getElementById(id);
    if(audio && audio.src) audio.play();
}

function nextQuestion() {
    location.reload();
}

function saveToNotebook() {
    fetch(notebookUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({ vocabulary_id: vocabId })
    })
    .then(res => res.json())
    .then(data => {
        // Cập nhật cả 2 nút (correct và wrong)
        const btns = document.querySelectorAll('#btn-save-correct, #btn-save-wrong');
        btns.forEach(btn => {
            btn.innerHTML = '<i class="fas fa-check me-1"></i> Đã lưu';
            btn.classList.remove('btn-outline-primary');
            btn.classList.add('btn-success');
            btn.disabled = true;
        });
    });
}

// --- KHỞI TẠO ---
document.addEventListener('DOMContentLoaded', function() {
    // Bắt sự kiện phím Enter ở ô input
    if (userInput) {
        userInput.addEventListener("keypress", function(event) {
            if (event.key === "Enter") submitAnswer();
        });
    }
});
