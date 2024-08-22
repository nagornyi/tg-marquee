let currentMarqueeText = '';

async function fetchMessages() {
    const response = await fetch('/get_messages');
    const newMessages = await response.json();
    if (newMessages.length > 0) {
        const newMarqueeText = newMessages.join(' &bull; ');
        if (newMarqueeText !== currentMarqueeText) {
            currentMarqueeText = newMarqueeText;
            const marqueeTextElement = document.getElementById('marquee-text');

            // Reset the marquee animation
            marqueeTextElement.style.animation = 'none';
            marqueeTextElement.offsetHeight; // Trigger reflow
            marqueeTextElement.style.animation = '';

            marqueeTextElement.innerHTML = currentMarqueeText;

            // Recalculate speed based on text width and container width
            adjustMarqueeSpeed();
        }
    }
}

function adjustMarqueeSpeed() {
    const marqueeText = document.getElementById('marquee-text');
    const marqueeContainer = document.querySelector('.marquee');

    // Get the width of the text and container
    const textWidth = marqueeText.scrollWidth;
    const containerWidth = marqueeContainer.clientWidth;

    // Calculate the duration for scrolling
    const speed = 200; // Adjust this value to control the speed
    const duration = (textWidth + containerWidth) / speed;

    // Apply the animation duration
    marqueeText.style.animationDuration = `${duration}s`;
}

document.addEventListener("DOMContentLoaded", function() {
    fetchMessages();  // Initial fetch
    setInterval(fetchMessages, 60000);  // Update messages every 60 seconds
});
