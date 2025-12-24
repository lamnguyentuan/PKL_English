// ==========================================
// Topic List JavaScript
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    // Set progress bar widths from data attributes
    document.querySelectorAll('.progress-bar[data-progress]').forEach(function(bar) {
        bar.style.width = bar.dataset.progress + '%';
    });
});
