import { Controller } from "@hotwired/stimulus";

const MESSAGE_BASE_CLASSES = 'mt-3 min-h-[1.35rem] text-sm font-semibold';

export default class extends Controller {
  static targets = ["message"];

  submit(event) {
    event.preventDefault();
    const form = event.target;
    const email = form.email.value.trim();
    if (!email) {
      this.showMessage("Please enter a valid email address.", "error");
      return;
    }
    const submitButton = form.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.textContent;
    submitButton.disabled = true;
    submitButton.textContent = 'Adding...';
    fetch("/api/newsletter/subscribe/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
      },
      body: JSON.stringify({ email }),
    })
      .then(async (response) => {
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(data.message || "Subscription failed. Please try again.");
        }
        this.showMessage(
          data.message,
          data.status
        );
        form.reset();
      })
      .catch((error) => {
        this.showMessage(error.message || "Subscription failed. Please try again later.", "error");
      })
      .finally(() => {
        submitButton.disabled = false;
        submitButton.textContent = originalButtonText;
      });
  }

  showMessage(message, type) {
    if (!this.hasMessageTarget) return;
    this.messageTarget.textContent = message;
    if (message) {
      const statusClasses = type === 'success' ? 'text-success' : 'text-danger';
      this.messageTarget.className = `${MESSAGE_BASE_CLASSES} ${statusClasses}`;
    }
  }
}
