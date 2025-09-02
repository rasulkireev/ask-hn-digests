import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static values = { type: String } // "liked" or "bookmarked"
  static targets = ["container", "emptyMessage"]

  connect() {
    this.loadArticles()
  }

  loadArticles() {
    const articles = this.typeValue === "liked" ? this.getLikedArticles() : this.getBookmarkedArticles()
    
    if (articles.length === 0) {
      this.showEmptyMessage()
    } else {
      this.displayArticles(articles)
    }
  }

  displayArticles(articles) {
    this.hideEmptyMessage()
    
    // Sort articles by date (most recent first)
    const sortedArticles = articles.sort((a, b) => {
      const dateA = new Date(this.typeValue === "liked" ? a.likedAt : a.bookmarkedAt)
      const dateB = new Date(this.typeValue === "liked" ? b.likedAt : b.bookmarkedAt)
      return dateB - dateA
    })

    const articlesHTML = sortedArticles.map(article => this.createArticleHTML(article)).join('')
    this.containerTarget.innerHTML = articlesHTML
  }

  createArticleHTML(article) {
    const actionDate = this.typeValue === "liked" ? article.likedAt : article.bookmarkedAt
    const actionText = this.typeValue === "liked" ? "Liked" : "Bookmarked"
    const formattedDate = new Date(actionDate).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })

    // Create tags HTML if article has tags
    const tagsHTML = article.tags ? 
      article.tags.split(',').map(tag => {
        const trimmedTag = tag.trim()
        if (trimmedTag) {
          return `<span class="inline-block px-2 py-1 text-xs font-medium text-orange-700 bg-orange-100 rounded-full">${this.escapeHtml(trimmedTag)}</span>`
        }
        return ''
      }).filter(tag => tag).join('') : ''

    return `
      <div class="relative p-6 bg-white rounded-lg border border-orange-100 shadow-md"
           data-controller="likes"
           data-likes-article-id-value="${article.id}"
           data-likes-article-slug-value="${article.slug}"
           data-likes-article-title-value="${this.escapeHtml(article.title)}">

        <!-- Like and Bookmark buttons in top right -->
        <div class="flex absolute top-4 right-4 space-x-2">
          <!-- Like button -->
          <button data-action="click->likes#like"
                  data-likes-target="likeButton"
                  class="p-2 text-gray-400 rounded-full transition-colors hover:bg-gray-100 hover:text-red-500"
                  title="Like this article">
            <svg data-likes-target="likeIcon" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
            </svg>
          </button>

          <!-- Bookmark button -->
          <button data-action="click->likes#bookmark"
                  data-likes-target="bookmarkButton"
                  class="p-2 text-gray-400 rounded-full transition-colors hover:bg-gray-100 hover:text-blue-500"
                  title="Bookmark this article">
            <svg data-likes-target="bookmarkIcon" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path>
            </svg>
          </button>
        </div>

        <!-- Article content -->
        <div>
          <!-- Title and date area - needs right padding for buttons -->
          <div class="pr-20 mb-3">
            <div class="mb-2">
              <a href="/blog/${article.slug}" class="text-xl font-bold text-orange-700 hover:text-orange-800 hover:underline">
                ${this.escapeHtml(article.title)}
              </a>
            </div>
            <div class="text-xs text-gray-500">
              ${formattedDate}
            </div>
          </div>

          <!-- Description and tags - can use full width -->
          <p class="mb-4 text-gray-700">
            ${this.escapeHtml(article.description || '')}
          </p>
          ${tagsHTML ? `<div class="flex flex-wrap gap-2">${tagsHTML}</div>` : ''}
          
          <!-- Remove button at bottom -->
          <div class="mt-4 text-right">
            <button data-action="click->saved-articles#removeArticle" 
                    data-article-id="${article.id}"
                    class="text-sm text-red-500 hover:text-red-700 underline">
              Remove from ${this.typeValue}
            </button>
          </div>
        </div>
      </div>
    `
  }

  removeArticle(event) {
    const articleId = event.target.dataset.articleId
    if (this.typeValue === "liked") {
      const likes = this.getLikedArticles()
      const filteredLikes = likes.filter(article => article.id !== articleId)
      localStorage.setItem('likedArticles', JSON.stringify(filteredLikes))
    } else {
      const bookmarks = this.getBookmarkedArticles()
      const filteredBookmarks = bookmarks.filter(article => article.id !== articleId)
      localStorage.setItem('bookmarkedArticles', JSON.stringify(filteredBookmarks))
    }
    
    this.loadArticles() // Reload the display
  }

  showEmptyMessage() {
    this.containerTarget.innerHTML = ''
    if (this.hasEmptyMessageTarget) {
      this.emptyMessageTarget.classList.remove('hidden')
    }
  }

  hideEmptyMessage() {
    if (this.hasEmptyMessageTarget) {
      this.emptyMessageTarget.classList.add('hidden')
    }
  }

  getLikedArticles() {
    const stored = localStorage.getItem('likedArticles')
    return stored ? JSON.parse(stored) : []
  }

  getBookmarkedArticles() {
    const stored = localStorage.getItem('bookmarkedArticles')
    return stored ? JSON.parse(stored) : []
  }

  escapeHtml(text) {
    const div = document.createElement('div')
    div.textContent = text
    return div.innerHTML
  }
}

