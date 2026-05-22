from django.urls import path

from core import views
from core.api.views import api
from core.views import AdminPanelView, BookmarkedArticlesView, LikedArticlesView

urlpatterns = [
    # pages
    path("", views.HomeView.as_view(), name="home"),
    path("search/", views.SearchView.as_view(), name="search"),
    path("liked/", LikedArticlesView.as_view(), name="liked_articles"),
    path("bookmarked/", BookmarkedArticlesView.as_view(), name="bookmarked_articles"),
    # blog
    path("blog/", views.BlogView.as_view(), name="blog_posts"),
    path("blog/<str:slug>", views.BlogPostView.as_view(), name="blog_post"),
    # tags
    path("tags/", views.TagListView.as_view(), name="tag_list"),
    path("tag/<slug:tag_slug>/", views.TagDetailView.as_view(), name="tag_detail"),
    # app
    path("api/", api.urls),
    # utils
    path("admin-panel", AdminPanelView.as_view(), name="admin_panel"),
]
