from django.urls import path

from core import views
from core.api.views import api
from core.views import AdminPanelView

urlpatterns = [
    # pages
    path("", views.HomeView.as_view(), name="home"),
    path("settings", views.UserSettingsView.as_view(), name="settings"),
    # blog
    path("blog/", views.BlogView.as_view(), name="blog_posts"),
    path("blog/<slug:slug>", views.BlogPostView.as_view(), name="blog_post"),

    # app
    path("api/", api.urls),
    # utils
    path("resend-confirmation/", views.resend_confirmation_email, name="resend_confirmation"),
    path("admin-panel", AdminPanelView.as_view(), name="admin_panel"),
]
