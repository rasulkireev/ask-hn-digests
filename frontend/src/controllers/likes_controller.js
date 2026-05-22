import { Controller } from "@hotwired/stimulus";

const INACTIVE_BUTTON_CLASSES = ["border-line", "bg-paper", "text-muted"];
const LIKE_ACTIVE_CLASSES = ["border-danger/25", "bg-danger-soft", "text-danger"];
const BOOKMARK_ACTIVE_CLASSES = ["border-cobalt/25", "bg-cobalt-soft", "text-cobalt"];

export default class extends Controller {
  static values = {
    articleId: String,
    articleSlug: String,
    articleTitle: String
  };
  static targets = ["likeButton", "bookmarkButton", "likeIcon", "bookmarkIcon"];

  connect() {
    this.updateButtonStates();
  }

  like() {
    const likes = this.getLikedArticles();
    const articleData = {
      id: this.articleIdValue,
      slug: this.articleSlugValue,
      title: this.articleTitleValue,
      likedAt: new Date().toISOString()
    };

    if (this.isLiked()) {
      // Remove from likes
      const filteredLikes = likes.filter(article => article.id !== this.articleIdValue);
      localStorage.setItem('likedArticles', JSON.stringify(filteredLikes));
    } else {
      // Add to likes
      likes.push(articleData);
      localStorage.setItem('likedArticles', JSON.stringify(likes));
    }

    this.updateButtonStates();
  }

  bookmark() {
    const bookmarks = this.getBookmarkedArticles();
    const articleData = {
      id: this.articleIdValue,
      slug: this.articleSlugValue,
      title: this.articleTitleValue,
      bookmarkedAt: new Date().toISOString()
    };

    if (this.isBookmarked()) {
      // Remove from bookmarks
      const filteredBookmarks = bookmarks.filter(article => article.id !== this.articleIdValue);
      localStorage.setItem('bookmarkedArticles', JSON.stringify(filteredBookmarks));
    } else {
      // Add to bookmarks
      bookmarks.push(articleData);
      localStorage.setItem('bookmarkedArticles', JSON.stringify(bookmarks));
    }

    this.updateButtonStates();
  }

  updateButtonStates() {
    const isLiked = this.isLiked();
    const isBookmarked = this.isBookmarked();

    // Update like button
    if (this.hasLikeButtonTarget) {
      this.toggleButtonClasses(this.likeButtonTarget, LIKE_ACTIVE_CLASSES, isLiked);
    }

    if (this.hasLikeIconTarget) {
      this.likeIconTarget.classList.toggle('fill-current', isLiked);
    }

    // Update bookmark button
    if (this.hasBookmarkButtonTarget) {
      this.toggleButtonClasses(this.bookmarkButtonTarget, BOOKMARK_ACTIVE_CLASSES, isBookmarked);
    }

    if (this.hasBookmarkIconTarget) {
      this.bookmarkIconTarget.classList.toggle('fill-current', isBookmarked);
    }
  }

  toggleButtonClasses(button, activeClasses, isActive) {
    INACTIVE_BUTTON_CLASSES.forEach(className => {
      button.classList.toggle(className, !isActive);
    });

    activeClasses.forEach(className => {
      button.classList.toggle(className, isActive);
    });
  }

  isLiked() {
    const likes = this.getLikedArticles();
    return likes.some(article => article.id === this.articleIdValue);
  }

  isBookmarked() {
    const bookmarks = this.getBookmarkedArticles();
    return bookmarks.some(article => article.id === this.articleIdValue);
  }

  getLikedArticles() {
    const stored = localStorage.getItem('likedArticles');
    return stored ? JSON.parse(stored) : [];
  }

  getBookmarkedArticles() {
    const stored = localStorage.getItem('bookmarkedArticles');
    return stored ? JSON.parse(stored) : [];
  }

  // Static methods for use in other controllers or pages
  static getAllLikedArticles() {
    const stored = localStorage.getItem('likedArticles');
    return stored ? JSON.parse(stored) : [];
  }

  static getAllBookmarkedArticles() {
    const stored = localStorage.getItem('bookmarkedArticles');
    return stored ? JSON.parse(stored) : [];
  }
}
