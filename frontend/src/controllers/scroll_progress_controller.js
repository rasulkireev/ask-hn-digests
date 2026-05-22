import { Controller } from "@hotwired/stimulus";

export default class extends Controller {
  static targets = ["bar"];

  connect() {
    this.ticking = false;
    this.update = this.update.bind(this);
    this.queueUpdate = this.queueUpdate.bind(this);
    window.addEventListener("scroll", this.queueUpdate, { passive: true });
    window.addEventListener("resize", this.queueUpdate);
    this.update();
  }

  disconnect() {
    window.removeEventListener("scroll", this.queueUpdate);
    window.removeEventListener("resize", this.queueUpdate);
  }

  queueUpdate() {
    if (this.ticking) return;
    this.ticking = true;
    window.requestAnimationFrame(this.update);
  }

  update() {
    const scrollable = document.documentElement.scrollHeight - window.innerHeight;
    const progress = scrollable > 0 ? window.scrollY / scrollable : 0;
    this.barTarget.style.transform = `scaleX(${Math.min(Math.max(progress, 0), 1)})`;
    this.ticking = false;
  }
}
