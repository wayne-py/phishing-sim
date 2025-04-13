document.addEventListener('DOMContentLoaded', function() {
    const previewButton = document.getElementById('preview-button');
    const contentInput = document.getElementById('content');
    const templatePreview = document.getElementById('template-preview');
    
    if (previewButton && contentInput && templatePreview) {
        previewButton.addEventListener('click', function(event) {
            event.preventDefault();
            const content = contentInput.value;
            templatePreview.innerHTML = content;
        });
    }
    
    // Helper function to insert text at cursor position in textarea
    function insertTextAtCursor(textarea, text) {
        const startPos = textarea.selectionStart;
        const endPos = textarea.selectionEnd;
        const scrollTop = textarea.scrollTop;
        
        textarea.value = textarea.value.substring(0, startPos) + text + textarea.value.substring(endPos, textarea.value.length);
        textarea.focus();
        textarea.selectionStart = startPos + text.length;
        textarea.selectionEnd = startPos + text.length;
        textarea.scrollTop = scrollTop;
    }
    
    // Add event listeners for template elements
    const templateButtons = document.querySelectorAll('.template-element-btn');
    templateButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            const element = button.getAttribute('data-element');
            insertTextAtCursor(contentInput, element);
        });
    });
});