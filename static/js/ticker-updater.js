const settingsUpdateInterval = 60000;
let currentMarqueeText = '';
let scrollSpeed = 200;  // Default value
let msgUpdateInterval = 60000;  // Default value (in ms)
let messageFetchInterval;

async function fetchSettings() {
  const response = await fetch('/get_settings');
  const settings = await response.json();

  if (settings.scroll_speed) scrollSpeed = parseInt(settings.scroll_speed, 10);
  if (settings.update_interval) msgUpdateInterval = parseInt(settings.update_interval, 10) * 1000;  // Convert to ms

  // Set the interval to fetch messages after settings are fetched
  clearInterval(messageFetchInterval);
  messageFetchInterval = setInterval(fetchMessages, msgUpdateInterval);

  // Recalculate the marquee speed with the new scrollSpeed
  adjustMarqueeSpeed();
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

    // Restart the marquee animation to apply the new speed
    marqueeText.offsetHeight;  // Force reflow to restart the animation
}

document.addEventListener("DOMContentLoaded", function() {
    fetchSettings();  // Initial fetch of settings
    fetchMessages();  // Initial fetch of messages
    // Set the interval to fetch settings periodically
    setInterval(fetchSettings, settingsUpdateInterval);
});
