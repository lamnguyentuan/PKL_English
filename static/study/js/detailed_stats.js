// ==========================================
// Detailed Stats JavaScript
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    // Read data from JSON script tag
    const statsData = JSON.parse(document.getElementById('stats-data').textContent);
    const dailyStats = statsData.dailyStats || [];
    const masteredCount = statsData.masteredCount || 0;
    const totalWords = statsData.totalWords || 0;

    // Chuẩn bị dữ liệu cho biểu đồ
    const labels = dailyStats.map(d => {
        const date = new Date(d.study_date);
        return date.toLocaleDateString('vi-VN', { weekday: 'short', day: 'numeric' });
    });
    const correctData = dailyStats.map(d => d.correct);
    const wrongData = dailyStats.map(d => d.total - d.correct);

    // Biểu đồ 7 ngày
    new Chart(document.getElementById('weeklyChart'), {
        type: 'bar',
        data: {
            labels: labels.length ? labels : ['Chưa có dữ liệu'],
            datasets: [
                {
                    label: 'Đúng',
                    data: correctData.length ? correctData : [0],
                    backgroundColor: 'rgba(40, 167, 69, 0.8)',
                    borderRadius: 5
                },
                {
                    label: 'Sai',
                    data: wrongData.length ? wrongData : [0],
                    backgroundColor: 'rgba(220, 53, 69, 0.8)',
                    borderRadius: 5
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            scales: {
                x: { stacked: true },
                y: { stacked: true, beginAtZero: true }
            }
        }
    });

    // Biểu đồ tiến độ (Doughnut)
    const remaining = totalWords - masteredCount;

    new Chart(document.getElementById('progressChart'), {
        type: 'doughnut',
        data: {
            labels: ['Đã thuộc', 'Chưa thuộc'],
            datasets: [{
                data: [masteredCount, remaining > 0 ? remaining : 0],
                backgroundColor: ['#ffc107', '#e9ecef'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            cutout: '70%',
            plugins: {
                legend: { display: false }
            }
        }
    });
});
