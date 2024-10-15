let currentMarqueeText = '';
let scrollSpeed = 200;  // Default value
let updateInterval = 60000;  // Default value (in ms)

async function fetchSettings() {
  const response = await fetch('/get_settings');
  const settings = await response.json();

  scrollSpeed = parseInt(settings.scroll_speed, 10);
  updateInterval = parseInt(settings.update_interval, 10) * 1000;  // Convert to ms
}

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
    const duration = (textWidth + containerWidth) / scrollSpeed;

    // Apply the animation duration
    marqueeText.style.animationDuration = `${duration}s`;
}

document.addEventListener("DOMContentLoaded", function() {
    fetchSettings();  // Initial fetch of settings
    fetchMessages();  // Initial fetch of messages
    setInterval(fetchMessages, updateInterval);  // Update messages periodically
});
