// ==========================================
// Notebook JavaScript
// ==========================================

// Đọc dữ liệu từ data container
const notebookData = document.getElementById('notebook-data');
const removeUrl = notebookData.dataset.removeUrl;
const updateUrl = notebookData.dataset.updateUrl;
const csrfToken = notebookData.dataset.csrf;

// --- PHÁT AUDIO ---
function playAudio(btn) {
    const player = document.getElementById('audio-player');
    player.src = btn.dataset.src;
    player.play();
}

// --- XÓA ENTRY ---
function removeEntry(vocabId) {
    if (!confirm('Xóa từ này khỏi sổ tay?')) return;
    
    fetch(removeUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({ vocabulary_id: vocabId })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById('entry-' + vocabId).remove();
    });
}

// --- HIỂN THỊ FORM EDIT GHI CHÚ ---
function showEditNote(vocabId) {
    document.getElementById('note-display-' + vocabId).classList.add('d-none');
    document.getElementById('add-note-btn-' + vocabId).classList.add('d-none');
    document.getElementById('note-edit-' + vocabId).classList.remove('d-none');
    document.getElementById('note-input-' + vocabId).focus();
}

// --- HỦY EDIT GHI CHÚ ---
function cancelEditNote(vocabId) {
    document.getElementById('note-edit-' + vocabId).classList.add('d-none');
    const noteDisplay = document.getElementById('note-display-' + vocabId);
    const noteText = noteDisplay.querySelector('.note-text').textContent;
    if (noteText) {
        noteDisplay.classList.remove('d-none');
    } else {
        document.getElementById('add-note-btn-' + vocabId).classList.remove('d-none');
    }
}

// --- LƯU GHI CHÚ ---
function saveNote(vocabId) {
    const note = document.getElementById('note-input-' + vocabId).value.trim();
    
    fetch(updateUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({ vocabulary_id: vocabId, note: note })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById('note-edit-' + vocabId).classList.add('d-none');
        const noteDisplay = document.getElementById('note-display-' + vocabId);
        noteDisplay.querySelector('.note-text').textContent = note;
        
        if (note) {
            noteDisplay.classList.remove('d-none');
            document.getElementById('add-note-btn-' + vocabId).classList.add('d-none');
        } else {
            noteDisplay.classList.add('d-none');
            document.getElementById('add-note-btn-' + vocabId).classList.remove('d-none');
        }
    });
}
