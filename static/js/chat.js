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