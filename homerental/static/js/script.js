// Basic form validation and interactive features
document.addEventListener('DOMContentLoaded', function() {
    // Auto-format contact number input
    const contactInputs = document.querySelectorAll('input[type="tel"]');
    contactInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 0) {
                value = '+' + value;
            }
            e.target.value = value;
        });
    });

    // Auto-fill current month in bill form
    const monthInput = document.getElementById('month');
    if (monthInput && !monthInput.value) {
        const now = new Date();
        const month = now.toLocaleString('default', { month: 'long' });
        const year = now.getFullYear();
        monthInput.value = `${month} ${year}`.toLowerCase();
    }

    // Calculate bill total automatically
    const billInputs = document.querySelectorAll('#rent, #water, #electricity, #extra');
    billInputs.forEach(input => {
        input.addEventListener('input', calculateTotal);
    });

    function calculateTotal() {
        const rent = parseFloat(document.getElementById('rent').value) || 0;
        const water = parseFloat(document.getElementById('water').value) || 0;
        const electricity = parseFloat(document.getElementById('electricity').value) || 0;
        const extra = parseFloat(document.getElementById('extra').value) || 0;
        
        // You could display this total somewhere if needed
        const total = rent + water + electricity + extra;
        console.log('Total bill:', total);
    }

    // Confirm before deleting
    const deleteLinks = document.querySelectorAll('a[href*="delete"]');
    deleteLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this portion? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Image preview for gallery uploads
    const photoInputs = document.querySelectorAll('input[type="file"][name="photo"]');
    photoInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            if (e.target.files && e.target.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    // You could show a preview here if needed
                    console.log('File selected:', e.target.result);
                };
                reader.readAsDataURL(e.target.files[0]);
            }
        });
    });
});