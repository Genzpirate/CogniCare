// --- Myth Card Flip Logic ---
const mythCard = document.getElementById('myth-card');

if (mythCard) {
    mythCard.addEventListener('click', function() {
        mythCard.classList.toggle('is-flipped');
    });
}


// Find all the chat elements on the page
const chatForm = document.getElementById('chat-form');
const messageInput = document.getElementById('message-input');
const chatHistory = document.getElementById('chat-history');

// Listen for when the user submits the form
chatForm.addEventListener('submit', async function(event) {
    event.preventDefault(); // Stop the page from reloading

    const userMessage = messageInput.value.trim(); // Get the user's message
    if (!userMessage) return; // Don't send empty messages

    // 1. Display the user's message immediately
    appendMessage(userMessage, 'user-message');
    messageInput.value = ''; // Clear the input box

    // 2. Send the message to the backend and get the bot's response
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: userMessage })
        });
        const result = await response.json();
        const botMessage = result.reply;

        // 3. Display the bot's message
        appendMessage(botMessage, 'bot-message');

    } catch (error) {
        // Handle any errors
        console.error('Error:', error);
        appendMessage('Sorry, something went wrong. Please try again.', 'bot-message');
    }
});

// A helper function to add a new message to the chat history
function appendMessage(message, className) {
    const messageElement = document.createElement('div');
    messageElement.classList.add(className);
    messageElement.innerText = message;
    chatHistory.appendChild(messageElement);
    chatHistory.scrollTop = chatHistory.scrollHeight; // Auto-scroll to the bottom
}

// --- Async Myth Loader ---
document.addEventListener('DOMContentLoaded', async function() {
    const mythLoading = document.getElementById('myth-loading');
    const mythContent = document.getElementById('myth-content');
    const mythHint = document.getElementById('myth-hint');
    const factContent = document.getElementById('fact-content');

    // Only run if the myth card exists on this page
    if (mythLoading) {
        try {
            // 1. Call our new internal API
            const response = await fetch('/api/get_myth');
            const data = await response.json();

            // 2. Update the HTML with the data
            mythContent.innerText = `"${data.myth}"`;
            factContent.innerText = data.fact;

            // 3. Hide loader and show content
            mythLoading.style.display = 'none';
            mythContent.style.display = 'block';
            mythHint.style.display = 'block';

        } catch (error) {
            console.error('Error fetching myth:', error);
            mythLoading.innerHTML = '<p>Failed to load myth.</p>';
        }
    }
});