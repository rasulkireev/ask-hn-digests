import { Controller } from "@hotwired/stimulus";
import { showMessage } from "../utils/messages";

export default class extends Controller {
  static targets = ["toggleButton", "overlay", "formContainer", "feedbackInput"];

  connect() {
    // Initialize the controller
    this.isOpen = false;

    // Bind keyboard event handlers
    this.handleKeydownBound = this.handleKeydown.bind(this);
    document.addEventListener("keydown", this.handleKeydownBound);
  }

  disconnect() {
    // Clean up event listeners when controller disconnects
    document.removeEventListener("keydown", this.handleKeydownBound);
  }

  toggleFeedback() {
    if (this.isOpen) {
      this.closeFeedback();
    } else {
      this.openFeedback();
    }
  }

  openFeedback() {
    this.overlayTarget.classList.remove("pointer-events-none", "opacity-0");
    this.overlayTarget.classList.add("pointer-events-auto", "opacity-100");
    this.formContainerTarget.classList.remove("translate-y-2", "scale-[0.98]");
    this.formContainerTarget.classList.add("translate-y-0", "scale-100");

    // Focus the input field
    setTimeout(() => {
      this.feedbackInputTarget.focus();
    }, 300);

    this.isOpen = true;
  }

  closeFeedback() {
    this.formContainerTarget.classList.remove("translate-y-0", "scale-100");
    this.formContainerTarget.classList.add("translate-y-2", "scale-[0.98]");
    setTimeout(() => {
      this.overlayTarget.classList.remove("pointer-events-auto", "opacity-100");
      this.overlayTarget.classList.add("pointer-events-none", "opacity-0");
    }, 100);

    this.isOpen = false;
  }

  closeIfClickedOutside(event) {
    // Close if clicked outside the form
    if (event.target === this.overlayTarget) {
      this.closeFeedback();
    }
  }

  handleKeydown(event) {
    // Close with Escape key
    if (event.key === "Escape" && this.isOpen) {
      event.preventDefault();
      this.closeFeedback();
    }

    // Submit with Enter key when focused on the textarea (unless Shift is pressed for multiline)
    if (event.key === "Enter" && !event.shiftKey && this.isOpen &&
        document.activeElement === this.feedbackInputTarget) {
      event.preventDefault();
      this.submitFeedback(event);
    }
  }

  submitFeedback(event) {
    event.preventDefault();

    const feedback = this.feedbackInputTarget.value.trim();

    if (!feedback) {
      return;
    }

    // Add loading state
    const submitButton = event.target.tagName === 'BUTTON' ? event.target : this.element.querySelector('button[type="submit"]');
    const originalButtonText = submitButton?.textContent || 'Submit';
    if (submitButton) {
      submitButton.disabled = true;
      submitButton.textContent = 'Submitting...';
    }

    const csrfTokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
    const csrfToken = csrfTokenInput ? csrfTokenInput.value : '';

    fetch('/api/submit-feedback', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify({ feedback, page: window.location.pathname }),
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
      }
      return response.json();
    })
    .then(data => {
      this.resetForm();
      this.closeFeedback();
      showMessage(data.message || "Feedback submitted successfully", 'success');
    })
    .catch((error) => {
      console.error('Error:', error);
      showMessage(error.message || "Failed to submit feedback. Please try again later.", 'error');
      // Reset loading state on error
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.textContent = originalButtonText;
      }
    });
  }

  resetForm() {
    this.feedbackInputTarget.value = "";
  }
}
