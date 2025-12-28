document.addEventListener('DOMContentLoaded', function() {
    fetchStats();
});

function fetchStats() {
    fetch('/api/stats/')
        .then(response => response.json())
        .then(data => {
            renderOverview(data);
            renderChart(data.daily_stats);
            renderWrongWords(data.most_wrong);
        })
        .catch(err => console.error("Lỗi tải thống kê:", err));
}

function renderOverview(data) {
    // Điền các con số tổng quan
    // Sử dụng || 0 để tránh hiển thị undefined nếu dữ liệu null
    animateValue("stat-total", 0, data.total_words || 0, 1000);
    animateValue("stat-mastered", 0, data.mastered_count || 0, 1000);
    document.getElementById('stat-streak').innerText = data.streak || 0;
    document.getElementById('stat-accuracy').innerText = data.accuracy || 0;
}

function renderWrongWords(words) {
    const container = document.getElementById('wrong-words-list');
    container.innerHTML = '';

    if (!words || words.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-check-circle fa-2x text-success mb-2"></i>
                <p class="small">Bạn làm rất tốt! Không có từ nào sai nhiều.</p>
            </div>`;
        return;
    }

    words.forEach(item => {
        const html = `
            <div class="d-flex align-items-center justify-content-between p-2 border rounded bg-light">
                <div>
                    <strong class="text-danger">${item.word}</strong>
                    <div class="small text-muted text-truncate" style="max-width: 150px;">
                        ${item.meaning_sentence}
                    </div>
                </div>
                <span class="badge bg-danger rounded-pill">${item.wrong_count} lần sai</span>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', html);
    });
}

function renderChart(dailyStats) {
    const ctx = document.getElementById('studyChart').getContext('2d');
    
    // Chuẩn bị dữ liệu cho Chart
    // Nếu API trả về mảng rỗng, ta tạo dữ liệu giả cho đẹp hoặc để trống
    const labels = dailyStats.map(item => formatDate(item.study_date));
    const dataTotal = dailyStats.map(item => item.total);
    const dataCorrect = dailyStats.map(item => item.correct);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Số câu đúng',
                    data: dataCorrect,
                    backgroundColor: 'rgba(25, 135, 84, 0.7)', // Màu xanh success
                    borderColor: 'rgba(25, 135, 84, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Tổng số câu trả lời',
                    data: dataTotal,
                    backgroundColor: 'rgba(13, 110, 253, 0.3)', // Màu xanh primary nhạt
                    borderColor: 'rgba(13, 110, 253, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Hàm hiệu ứng chạy số (Counter Animation)
function animateValue(id, start, end, duration) {
    const obj = document.getElementById(id);
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.innerHTML = Math.floor(progress * (end - start) + start);
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// Hàm format ngày tháng (YYYY-MM-DD -> DD/MM)
function formatDate(dateString) {
    const date = new Date(dateString);
    return `${date.getDate()}/${date.getMonth() + 1}`;
}