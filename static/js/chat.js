const telegramForm = document.getElementById("messageForm");
const messageHint = document.getElementById('message-hint');
const messageField = document.getElementById('message');
const submitButton = document.getElementById('tg-submit-btn');
const progressIndicator = document.getElementById('progress-indicator');

function toggleSubmitButton() {
  if (messageField.value.trim() === '') {
      submitButton.disabled = true;
  } else {
      submitButton.disabled = false;
  }
}

messageField.addEventListener('input', toggleSubmitButton);

telegramForm.addEventListener('submit', function(e) {
  e.preventDefault();
  const message = messageField.value;
  telegramForm.style.display = 'none';
  progressIndicator.innerHTML = 'Надсилаємо повідомлення...';
  progressIndicator.style.display = 'block';

  fetch('/send_message', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message })
  })
  .then(response => response.json())
  .then(data => {
      if (data.ok) {
          progressIndicator.innerHTML = '✅ Повідомлення надіслано!';
      } else {
          progressIndicator.innerHTML = '⚠️ Трясця, помилка: ' + (data.error || 'Невідома помилка');
      }
  })
  .catch(error => {
      console.error('Error:', error);
      progressIndicator.innerHTML = '⚠️ Трясця, сталася помилка!';
  });
});

window.onload = function() {
  messageField.value = '';
  toggleSubmitButton();
};
