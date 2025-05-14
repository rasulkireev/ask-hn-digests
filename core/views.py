from django.http import HttpResponse

from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.conf import settings
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView, UpdateView, ListView, DetailView
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django_q.tasks import async_task

from core.forms import ProfileUpdateForm, SummarizeHNDiscussionForm, SendNewsletterForm
from core.models import Profile, BlogPost, HNDiscussionSummary

from ask_hn_digest.utils import get_ask_hn_digest_logger


logger = get_ask_hn_digest_logger(__name__)

class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["latest_summaries"] = HNDiscussionSummary.objects.order_by("-date_analyzed")[:3]
        return context


class UserSettingsView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    login_url = "account_login"
    model = Profile
    form_class = ProfileUpdateForm
    success_message = "User Profile Updated"
    success_url = reverse_lazy("settings")
    template_name = "pages/user-settings.html"

    def get_object(self):
        return self.request.user.profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        email_address = EmailAddress.objects.get_for_user(user, user.email)
        context["email_verified"] = email_address.verified
        context["resend_confirmation_url"] = reverse("resend_confirmation")

        return context


@login_required
def resend_confirmation_email(request):
    user = request.user
    send_email_confirmation(request, user, EmailAddress.objects.get_for_user(user, user.email))

    return redirect("settings")


class BlogView(ListView):
    model = HNDiscussionSummary
    template_name = "blog/blog_posts.html"
    context_object_name = "blog_posts"


class BlogPostView(DetailView):
    model = HNDiscussionSummary
    template_name = "blog/blog_post.html"
    context_object_name = "blog_post"


def test_mjml(request):
    html_content = render_to_string("emails/test_mjml.html", {})
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        "Subject",
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        ["test@test.com"],
    )
    email.attach_alternative(html_content, "text/html")
    email.send()

    return HttpResponse("Email sent")


class AdminPanelView(UserPassesTestMixin, TemplateView):
    template_name = "pages/admin_panel.html"
    login_url = "account_login"

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to access the admin panel.")
        return redirect("home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["summarize_form"] = kwargs.get("summarize_form") or SummarizeHNDiscussionForm()
        if "send_newsletter_form" in kwargs:
            context["send_newsletter_form"] = kwargs["send_newsletter_form"]
        else:
            latest_ids = HNDiscussionSummary.get_latest_summaries_ids()
            initial = {"summary_ids": ",".join(str(i) for i in latest_ids)}
            context["send_newsletter_form"] = SendNewsletterForm(initial=initial)
        return context

    def post(self, request, *args, **kwargs):
        if "send_newsletter" in request.POST:
            form = SendNewsletterForm(request.POST)
            if form.is_valid():
                summary_ids_str = form.cleaned_data["summary_ids"]
                summary_ids = [int(sid.strip()) for sid in summary_ids_str.split(',') if sid.strip()]
                from core.tasks import send_buttondown_newsletter
                response = send_buttondown_newsletter(summary_ids)
                if response.get("id") or response.get("success"):
                    messages.success(request, f"Newsletter sent for summaries: {summary_ids_str}")
                else:
                    messages.error(request, f"Failed to send newsletter: {response}")
                return redirect("admin_panel")
            else:
                return self.render_to_response(self.get_context_data(send_newsletter_form=form))
        else:
            form = SummarizeHNDiscussionForm(request.POST)
            if form.is_valid():
                discussion_ids_str = form.cleaned_data["discussion_ids"]
                discussion_ids = [int(d.strip()) for d in discussion_ids_str.split(',') if d.strip()]

                for discussion_id in discussion_ids:
                    async_task('core.tasks.summarize_hn_discussion', discussion_id, group="Analyze Discussion")

                messages.success(request, f"Summarization tasks for discussions {discussion_ids_str} started!")
                return redirect("admin_panel")
            else:
                return self.render_to_response(self.get_context_data(summarize_form=form))
