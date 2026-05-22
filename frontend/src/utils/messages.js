// static/js/utils/messages.js
export function showMessage(message, type = 'error') {
  const messagesContainer = document.querySelector('.messages-container') || createMessagesContainer();

  const messageId = Date.now();
  const messageHTML = `
    <div data-reveal-target="item" data-message-id="${messageId}" class="rounded-[2px] border p-4 shadow-low transition duration-300 ${type === 'error' ? 'border-danger/25 bg-danger-soft' : 'border-success/25 bg-success-soft'} translate-x-full transform opacity-0">
      <div class="flex items-start">
        <div class="flex-shrink-0 mr-3">
          <svg class="w-5 h-5" viewBox="0 0 24 24">
            <circle class="text-line" stroke-width="2" stroke="currentColor" fill="transparent" r="10" cx="12" cy="12"/>
            <circle class="${type === 'error' ? 'text-danger' : 'text-success'}" stroke-width="2" stroke="currentColor" fill="transparent" r="10" cx="12" cy="12" data-timer-circle/>
          </svg>
        </div>
        <div class="flex-grow">
          <p class="text-sm font-bold text-ink">
            ${message}
          </p>
        </div>
        <div class="flex-shrink-0 ml-3">
          <button onclick="this.closest('[data-reveal-target=item]').remove()" type="button" class="inline-flex h-7 w-7 items-center justify-center rounded-[2px] border border-line bg-paper text-muted transition hover:border-accent/35 hover:bg-accent-soft hover:text-accent-dark focus:outline-none focus:ring-4 focus:ring-accent/20">
            <span class="sr-only">Dismiss</span>
            <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  `;

  messagesContainer.insertAdjacentHTML('beforeend', messageHTML);

  const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
  setTimeout(() => {
    messageElement.classList.remove('opacity-0', 'translate-x-full');
    startTimer(messageElement);
  }, 100);
}

function createMessagesContainer() {
  const container = document.createElement('div');
  container.className = 'messages-container fixed right-4 top-[5.4rem] z-50 grid w-[min(24rem,calc(100vw_-_2rem))] gap-3';
  document.body.appendChild(container);
  return container;
}

function startTimer(item) {
  const timerCircle = item.querySelector('[data-timer-circle]');
  const radius = 10;
  const circumference = 2 * Math.PI * radius;

  timerCircle.style.strokeDasharray = `${circumference} ${circumference}`;
  timerCircle.style.strokeDashoffset = circumference;

  let progress = 0;
  const interval = setInterval(() => {
    if (progress >= 100) {
      clearInterval(interval);
      hideMessage(item);
    } else {
      progress++;
      const offset = circumference - (progress / 100) * circumference;
      timerCircle.style.strokeDashoffset = offset;
    }
  }, 50);
}

function hideMessage(item) {
  item.classList.add('opacity-0', 'translate-x-full');
  setTimeout(() => {
    item.remove();
  }, 300);
}
