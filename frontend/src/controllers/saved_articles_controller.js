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
      <div class="relative p-6 bg-white rounded-lg border border-orange-100 shadow-md">
        <div class="pr-20">
          <div class="mb-2">
            <a href="/blog/${article.slug}" class="text-xl font-bold text-orange-700 hover:text-orange-800 hover:underline">
              ${this.escapeHtml(article.title)}
            </a>
          </div>
          <div class="mb-3 text-xs text-gray-500">
            ${actionText} on ${formattedDate}
          </div>
          <div class="flex justify-between items-center">
            <span class="text-sm text-gray-500">Article ID: ${article.id}</span>
            <button data-action="click->saved-articles#removeArticle"
                    data-article-id="${article.id}"
                    class="text-sm text-red-500 underline hover:text-red-700">
              Remove from ${this.typeValue}
            </button>
          </div>
        </div>
      </div>
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
