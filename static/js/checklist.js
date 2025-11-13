document.addEventListener('DOMContentLoaded', function() {
    
    const checklistForm = document.getElementById('checklist-form');
    const checklistInput = document.getElementById('checklist-input');
    const checklist = document.getElementById('checklist');

    // --- 1. LOGIC TO ADD A NEW ITEM ---
    if (checklistForm) {
        checklistForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            const content = checklistInput.value.trim();
            if (!content) return;

            try {
                const response = await fetch('/add_checklist_item', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content: content })
                });
                const result = await response.json();

                if (response.ok) {
                    addNewItemToUI(result.item);
                    checklistInput.value = '';
                } else {
                    alert('Error: ' + result.message);
                }
            } catch (error) {
                console.error('Error adding item:', error);
                alert('An error occurred. Please try again.');
            }
        });
    }

    // --- 2. LOGIC FOR UPDATE (CHECK) AND DELETE ---
    if (checklist) {
        checklist.addEventListener('click', function(event) {
            const target = event.target;
            const li = target.closest('li'); // Find the list item
            if (!li) return; // If they clicked outside an item, do nothing
            
            const itemId = li.dataset.id; // Get the item ID we stored in data-id

            // Case 1: User clicked the checkbox
            if (target.type === 'checkbox') {
                const isCompleted = target.checked;
                updateChecklistItem(itemId, isCompleted, li);
            }

            // Case 2: User clicked the delete button
            if (target.tagName === 'BUTTON') {
                deleteChecklistItem(itemId, li);
            }
        });
    }
});

// --- 3. HELPER FUNCTIONS ---

function addNewItemToUI(item) {
    const checklist = document.getElementById('checklist');
    const li = document.createElement('li');
    li.dataset.id = item.item_id; // Add the data-id
    li.innerHTML = `
        <input type="checkbox" ${item.is_completed ? 'checked' : ''}>
        <span>${item.content}</span>
        <button>&times;</button>
    `;
    
    // Add strikethrough if it's already completed
    if (item.is_completed) {
        li.classList.add('completed');
    }
    
    checklist.appendChild(li);
}

async function updateChecklistItem(itemId, isCompleted, liElement) {
    try {
        await fetch(`/update_checklist_item/${itemId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_completed: isCompleted })
        });
        
        // Update the UI instantly
        liElement.classList.toggle('completed', isCompleted);
    } catch (error) {
        console.error('Error updating item:', error);
    }
}

async function deleteChecklistItem(itemId, liElement) {
    if (!confirm('Are you sure you want to delete this item?')) {
        return;
    }
    
    try {
        await fetch(`/delete_checklist_item/${itemId}`, {
            method: 'POST'
        });
        
        // Remove from the UI instantly
        liElement.remove();
    } catch (error) {
        console.error('Error deleting item:', error);
    }
}