import { Controller } from "@hotwired/stimulus";

export default class extends Controller {
  static values = { type: String }; // "liked" or "bookmarked"
  static targets = ["container", "emptyMessage"];

  connect() {
    this.loadArticles();
  }

  loadArticles() {
    const articles = this.typeValue === "liked" ? this.getLikedArticles() : this.getBookmarkedArticles();

    if (articles.length === 0) {
      this.showEmptyMessage();
    } else {
      this.displayArticles(articles);
    }
  }

  displayArticles(articles) {
    this.hideEmptyMessage();

    // Sort articles by date (most recent first)
    const sortedArticles = articles.sort((a, b) => {
      const dateA = new Date(this.typeValue === "liked" ? a.likedAt : a.bookmarkedAt);
      const dateB = new Date(this.typeValue === "liked" ? b.likedAt : b.bookmarkedAt);
      return dateB - dateA;
    });

    const articlesHTML = sortedArticles.map(article => this.createArticleHTML(article)).join('');
    this.containerTarget.innerHTML = articlesHTML;
  }

  createArticleHTML(article) {
    const actionDate = this.typeValue === "liked" ? article.likedAt : article.bookmarkedAt;
    const actionText = this.typeValue === "liked" ? "Liked" : "Bookmarked";
    const formattedDate = new Date(actionDate).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });

    return `
      <article class="group grid gap-3 border-t border-line py-5 transition hover:bg-paper/70 sm:grid-cols-[7.5rem_minmax(0,1fr)_auto] sm:items-start">
        <div class="text-[0.68rem] font-black uppercase leading-relaxed tracking-[0.16em] text-muted">
          <span class="block text-ink">${actionText}</span>
          <span class="block">${formattedDate}</span>
        </div>
        <div>
          <h2 class="max-w-4xl break-words text-[1.12rem] font-black leading-tight sm:text-[1.34rem]">
            <a href="/blog/${article.slug}" class="no-underline transition hover:text-accent-dark">
              ${this.escapeHtml(article.title)}
            </a>
          </h2>
          <div class="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[0.68rem] font-black uppercase tracking-[0.16em] text-muted">
            <span>${actionText} on ${formattedDate}</span>
            <span>Article ID: ${article.id}</span>
          </div>
        </div>
        <button data-action="click->saved-articles#removeArticle"
                data-article-id="${article.id}"
                class="inline-flex min-h-[2.7rem] items-center justify-center gap-2 rounded-[2px] border border-line bg-paper px-4 text-[0.82rem] font-black uppercase tracking-[0.12em] leading-none text-ink-soft no-underline transition hover:border-line-strong hover:bg-paper-strong focus:outline-none focus:ring-2 focus:ring-accent/20">
          Remove from ${this.typeValue}
        </button>
      </article>
    `;
  }

  removeArticle(event) {
    const articleId = event.target.dataset.articleId;
    if (this.typeValue === "liked") {
      const likes = this.getLikedArticles();
      const filteredLikes = likes.filter(article => article.id !== articleId);
      localStorage.setItem('likedArticles', JSON.stringify(filteredLikes));
    } else {
      const bookmarks = this.getBookmarkedArticles();
      const filteredBookmarks = bookmarks.filter(article => article.id !== articleId);
      localStorage.setItem('bookmarkedArticles', JSON.stringify(filteredBookmarks));
    }

    this.loadArticles(); // Reload the display
  }

  showEmptyMessage() {
    this.containerTarget.innerHTML = '';
    if (this.hasEmptyMessageTarget) {
      this.emptyMessageTarget.classList.remove('hidden');
    }
  }

  hideEmptyMessage() {
    if (this.hasEmptyMessageTarget) {
      this.emptyMessageTarget.classList.add('hidden');
    }
  }

  getLikedArticles() {
    const stored = localStorage.getItem('likedArticles');
    return stored ? JSON.parse(stored) : [];
  }

  getBookmarkedArticles() {
    const stored = localStorage.getItem('bookmarkedArticles');
    return stored ? JSON.parse(stored) : [];
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}
