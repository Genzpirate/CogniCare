// This file contains the JavaScript "messenger" code to connect our HTML forms to our Python backend.

// --- REGISTRATION LOGIC ---
// First, we find the registration form in our register.html page.
const registerForm = document.getElementById('registerForm');

// We only run this code if the registration form actually exists on the current page.
if (registerForm) {
    // We add an "event listener" that waits for the user to submit the form (by clicking the button).
    registerForm.addEventListener('submit', async function(event) {
        // Prevent the browser from its default behavior of reloading the page.
        event.preventDefault();

        // Create a package (FormData) of the information the user typed in.
        const formData = new FormData(registerForm);
        // Convert the package to a simple object.
        const data = Object.fromEntries(formData.entries());

        // Send the data to our backend's "/register" address using the "fetch" command.
        const response = await fetch('/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        // Get the reply from the backend.
        const result = await response.json();

        // Show the reply to the user.
        alert(result.message);

        // If registration was successful, automatically send the user to the login page.
        if (response.ok) {
            window.location.href = '/';
        }
    });
}


// --- LOGIN LOGIC ---
// This works exactly like the registration logic, but for the login form.
const loginForm = document.getElementById('loginForm');

if (loginForm) {
    loginForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        const formData = new FormData(loginForm);
        const data = Object.fromEntries(formData.entries());

        // We send the data to the "/login" address this time.
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        // If the login was successful, the backend will say "ok".
        // If so, we send the user to their dashboard.
        if (response.ok) {
            window.location.href = '/dashboard.html';
        } else {
            // Otherwise, we show the error message from the backend.
            alert(result.message);
        }
    });
}


// --- LOGOUT LOGIC ---
// Finally, we find the logout button on the dashboard.
const logoutButton = document.getElementById('logoutButton');

if (logoutButton) {
    // We listen for a simple "click" event.
    logoutButton.addEventListener('click', async function(event) {
        // We send a request to a "/logout" address that we'll create in the backend.
        const response = await fetch('/logout', {
            method: 'POST'
        });

        // If logout is successful, send the user back to the login page.
        if (response.ok) {
            window.location.href = '/';
        }
    });
}