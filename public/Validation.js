function validate(){

    document.addEventListener('DOMContentLoaded', () => {
        const form = document.getElementById('registerForm');
    
        form.addEventListener('submit', async function(event) {
            event.preventDefault(); // Prevent the default form submission
    
            const formData = new FormData(form);
    
            try {
                const response = await fetch('/submit', {
                    method: 'POST',
                    body: formData
                });
    
                const result = await response.json();
    
                if (response.ok) {
                    // Successful submission
                    alert('Data successfully stored!');
                    window.location.href = '/index.html'; // Redirect after success
                } else {
                    // Handle validation errors
                    handleErrors(result);
                }
            } catch (error) {
                console.error('Error:', error);
            }
        });
    
        function handleErrors(errors) {
            resetAlerts();
            if (errors.email) {
                document.getElementById('emailalert').textContent = errors.email;
            }
            if (errors.password) {
                document.getElementById('passalert').textContent = errors.password;
            }
            if (errors.conpassword) {
                document.getElementById('conpassalert').textContent = errors.conpassword;
            }
        }
    
        function resetAlerts() {
            document.getElementById('fnamealert').textContent = '';
            document.getElementById('lnamealert').textContent = '';
            document.getElementById('emailalert').textContent = '';
            document.getElementById('companyalert').textContent = '';
            document.getElementById('passalert').textContent = '';
            document.getElementById('conpassalert').textContent = '';
        }
    });
    

}