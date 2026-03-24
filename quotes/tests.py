from django.contrib.auth.models import User
from django.template import Context, Template
from django.test import TestCase
from django.urls import reverse

from .models import Quote


class QuoteModelTest(TestCase):
    def test_default_status_is_pending(self):
        quote = Quote.objects.create(content="<user1> hello\n<user2> world")
        self.assertEqual(quote.status, Quote.Status.PENDING)
        self.assertEqual(quote.votes_up, 0)
        self.assertEqual(quote.votes_down, 0)

    def test_str_returns_content(self):
        quote = Quote.objects.create(content="test content")
        self.assertEqual(str(quote), "test content")

    def test_default_acceptant_is_none(self):
        quote = Quote.objects.create(content="test")
        self.assertIsNone(quote.acceptant)

    def test_created_date_auto_set(self):
        quote = Quote.objects.create(content="test")
        self.assertIsNotNone(quote.created_date)

    def test_default_ordering_is_newest_first(self):
        q1 = Quote.objects.create(content="first")
        q2 = Quote.objects.create(content="second")
        quotes = list(Quote.objects.all())
        self.assertEqual(quotes[0], q2)
        self.assertEqual(quotes[1], q1)

    def test_acceptant_set_null_on_user_delete(self):
        user = User.objects.create_user(username="mod", password="pass")
        quote = Quote.objects.create(content="test", acceptant=user, status=Quote.Status.APPROVED)
        user.delete()
        quote.refresh_from_db()
        self.assertIsNone(quote.acceptant)

    def test_status_choices_values(self):
        self.assertEqual(Quote.Status.PENDING, 1)
        self.assertEqual(Quote.Status.REJECTED, 2)
        self.assertEqual(Quote.Status.APPROVED, 3)


class QuoteWorkflowTest(TestCase):
    """Full lifecycle: add quotes, approve/reject, upvote/downvote."""

    def setUp(self):
        self.admin = User.objects.create_user(username="admin", password="testpass123")
        self.quotes = []
        for i in range(5):
            q = Quote.objects.create(content=f"<user> quote number {i}")
            self.quotes.append(q)

    def test_approve_quote(self):
        self.client.login(username="admin", password="testpass123")
        quote = self.quotes[0]

        response = self.client.post(reverse("quote_accept", args=[quote.id]), HTTP_REFERER="/manage/")
        self.assertEqual(response.status_code, 302)

        quote.refresh_from_db()
        self.assertEqual(quote.status, Quote.Status.APPROVED)
        self.assertEqual(quote.acceptant, self.admin)

    def test_reject_quote(self):
        self.client.login(username="admin", password="testpass123")
        quote = self.quotes[1]

        response = self.client.post(reverse("quote_reject", args=[quote.id]), HTTP_REFERER="/manage/")
        self.assertEqual(response.status_code, 302)

        quote.refresh_from_db()
        self.assertEqual(quote.status, Quote.Status.REJECTED)
        self.assertEqual(quote.acceptant, self.admin)

    def test_upvote_approved_quote(self):
        quote = self.quotes[0]
        quote.status = Quote.Status.APPROVED
        quote.save()

        for _ in range(3):
            self.client.post(reverse("quote_vote_up", args=[quote.id]), HTTP_REFERER="/")

        quote.refresh_from_db()
        self.assertEqual(quote.votes_up, 3)
        self.assertEqual(quote.votes_down, 0)

    def test_downvote_approved_quote(self):
        quote = self.quotes[0]
        quote.status = Quote.Status.APPROVED
        quote.save()

        for _ in range(2):
            self.client.post(reverse("quote_vote_down", args=[quote.id]), HTTP_REFERER="/")

        quote.refresh_from_db()
        self.assertEqual(quote.votes_down, 2)
        self.assertEqual(quote.votes_up, 0)

    def test_approved_quotes_appear_in_list(self):
        for q in self.quotes[:3]:
            q.status = Quote.Status.APPROVED
            q.save()

        response = self.client.get(reverse("accepted_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["quotes"]), 3)

    def test_rejected_quotes_appear_in_trash(self):
        for q in self.quotes[3:]:
            q.status = Quote.Status.REJECTED
            q.save()

        response = self.client.get(reverse("trash_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["quotes"]), 2)

    def test_pending_quotes_not_in_accepted_list(self):
        response = self.client.get(reverse("accepted_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["quotes"]), 0)

    def test_best_list_ordered_by_karma(self):
        for i, q in enumerate(self.quotes[:3]):
            q.status = Quote.Status.APPROVED
            q.votes_up = (i + 1) * 10
            q.votes_down = 0
            q.save()

        response = self.client.get(reverse("best_list"))
        quotes = list(response.context["quotes"])
        karmas = [q.votes_up - q.votes_down for q in quotes]
        self.assertEqual(karmas, sorted(karmas, reverse=True))

    def test_delete_quote(self):
        self.client.login(username="admin", password="testpass123")
        quote = self.quotes[4]
        quote_id = quote.id

        self.client.post(reverse("quote_delete", args=[quote_id]), HTTP_REFERER="/manage/")
        self.assertFalse(Quote.objects.filter(id=quote_id).exists())

    def test_manage_requires_login(self):
        response = self.client.get(reverse("quote_manage"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_accept_requires_login(self):
        response = self.client.post(reverse("quote_accept", args=[self.quotes[0].id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_reject_requires_login(self):
        response = self.client.post(reverse("quote_reject", args=[self.quotes[0].id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_delete_requires_login(self):
        response = self.client.post(reverse("quote_delete", args=[self.quotes[0].id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_accept_nonexistent_quote_returns_404(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.post(reverse("quote_accept", args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_reject_nonexistent_quote_returns_404(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.post(reverse("quote_reject", args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_delete_nonexistent_quote_returns_404(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.post(reverse("quote_delete", args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_vote_up_nonexistent_quote_returns_404(self):
        response = self.client.post(reverse("quote_vote_up", args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_vote_down_nonexistent_quote_returns_404(self):
        response = self.client.post(reverse("quote_vote_down", args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_pending_quotes_not_in_trash(self):
        response = self.client.get(reverse("trash_list"))
        self.assertEqual(len(response.context["quotes"]), 0)

    def test_pending_quotes_not_in_best(self):
        for q in self.quotes:
            q.votes_up = 100
            q.save()
        response = self.client.get(reverse("best_list"))
        self.assertEqual(len(response.context["quotes"]), 0)

    def test_rejected_quotes_not_in_accepted_list(self):
        for q in self.quotes:
            q.status = Quote.Status.REJECTED
            q.save()
        response = self.client.get(reverse("accepted_list"))
        self.assertEqual(len(response.context["quotes"]), 0)

    def test_manage_shows_only_pending_quotes(self):
        self.client.login(username="admin", password="testpass123")
        self.quotes[0].status = Quote.Status.APPROVED
        self.quotes[0].save()
        self.quotes[1].status = Quote.Status.REJECTED
        self.quotes[1].save()
        response = self.client.get(reverse("quote_manage"))
        self.assertEqual(response.status_code, 200)
        # 5 total minus 1 approved minus 1 rejected = 3 pending
        self.assertEqual(len(response.context["quotes"]), 3)

    def test_best_list_karma_with_downvotes(self):
        """Best list accounts for downvotes in karma calculation."""
        q1 = self.quotes[0]
        q1.status = Quote.Status.APPROVED
        q1.votes_up = 20
        q1.votes_down = 15  # karma = 5
        q1.save()

        q2 = self.quotes[1]
        q2.status = Quote.Status.APPROVED
        q2.votes_up = 10
        q2.votes_down = 0  # karma = 10
        q2.save()

        response = self.client.get(reverse("best_list"))
        quotes = list(response.context["quotes"])
        self.assertEqual(quotes[0].id, q2.id)
        self.assertEqual(quotes[1].id, q1.id)


class QuoteAddViewTest(TestCase):
    def test_add_quote_via_form(self):
        response = self.client.post(reverse("quote_add"), {"content": "<me> new quote"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Quote.objects.filter(content="<me> new quote").exists())
        quote = Quote.objects.get(content="<me> new quote")
        self.assertEqual(quote.status, Quote.Status.PENDING)

    def test_add_quote_get_shows_form(self):
        response = self.client.get(reverse("quote_add"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_add_empty_quote_fails_validation(self):
        response = self.client.post(reverse("quote_add"), {"content": ""})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Quote.objects.exists())
        self.assertTrue(response.context["form"].errors)

    def test_add_quote_renders_success_template(self):
        response = self.client.post(reverse("quote_add"), {"content": "<me> test"})
        self.assertTemplateUsed(response, "quotes/quote_added.html")

    def test_add_quote_renders_form_template(self):
        response = self.client.get(reverse("quote_add"))
        self.assertTemplateUsed(response, "quotes/quote_add.html")


class SafeRedirectTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin", password="testpass123")
        self.quote = Quote.objects.create(content="<user> test", status=Quote.Status.APPROVED)

    def test_malicious_referer_redirects_to_fallback(self):
        response = self.client.post(
            reverse("quote_vote_up", args=[self.quote.id]),
            HTTP_REFERER="https://evil.com/steal-cookies",
        )
        self.assertRedirects(response, "/", fetch_redirect_response=False)

    def test_safe_referer_is_preserved(self):
        response = self.client.post(
            reverse("quote_vote_up", args=[self.quote.id]),
            HTTP_REFERER="http://testserver/quote/show",
        )
        self.assertRedirects(response, "http://testserver/quote/show", fetch_redirect_response=False)

    def test_missing_referer_redirects_to_fallback(self):
        response = self.client.post(reverse("quote_vote_up", args=[self.quote.id]))
        self.assertRedirects(response, "/", fetch_redirect_response=False)

    def test_malicious_referer_on_protected_view(self):
        self.client.login(username="admin", password="testpass123")
        quote = Quote.objects.create(content="<user> pending")
        response = self.client.post(
            reverse("quote_accept", args=[quote.id]),
            HTTP_REFERER="https://evil.com/",
        )
        self.assertRedirects(response, "/", fetch_redirect_response=False)


class QuoteDetailViewTest(TestCase):
    def test_view_single_quote(self):
        quote = Quote.objects.create(content="<a> test quote", status=Quote.Status.APPROVED)
        response = self.client.get(reverse("quote_view", args=[quote.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["quote"], quote)

    def test_view_nonexistent_quote_returns_404(self):
        response = self.client.get(reverse("quote_view", args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_view_pending_quote_is_accessible(self):
        quote = Quote.objects.create(content="<a> pending quote")
        response = self.client.get(reverse("quote_view", args=[quote.id]))
        self.assertEqual(response.status_code, 200)

    def test_view_rejected_quote_is_accessible(self):
        quote = Quote.objects.create(content="<a> rejected", status=Quote.Status.REJECTED)
        response = self.client.get(reverse("quote_view", args=[quote.id]))
        self.assertEqual(response.status_code, 200)


class RequirePostTest(TestCase):
    """Verify all state-changing views reject GET requests with 405."""

    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="testpass123")
        self.quote = Quote.objects.create(content="<user> test", status=Quote.Status.APPROVED)

    def test_vote_up_get_returns_405(self):
        response = self.client.get(reverse("quote_vote_up", args=[self.quote.id]))
        self.assertEqual(response.status_code, 405)

    def test_vote_down_get_returns_405(self):
        response = self.client.get(reverse("quote_vote_down", args=[self.quote.id]))
        self.assertEqual(response.status_code, 405)

    def test_accept_get_returns_405(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.get(reverse("quote_accept", args=[self.quote.id]))
        self.assertEqual(response.status_code, 405)

    def test_reject_get_returns_405(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.get(reverse("quote_reject", args=[self.quote.id]))
        self.assertEqual(response.status_code, 405)

    def test_delete_get_returns_405(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.get(reverse("quote_delete", args=[self.quote.id]))
        self.assertEqual(response.status_code, 405)

    def test_ajax_get_returns_405(self):
        response = self.client.get(reverse("quote_ajax"))
        self.assertEqual(response.status_code, 405)


class IndexViewTest(TestCase):
    def test_index_returns_200(self):
        response = self.client.get(reverse("index_view"))
        self.assertEqual(response.status_code, 200)

    def test_index_uses_welcome_template(self):
        response = self.client.get(reverse("index_view"))
        self.assertTemplateUsed(response, "quotes/welcome.html")

    def test_index_contains_site_name(self):
        response = self.client.get(reverse("index_view"))
        self.assertIn("site_name", response.context)


class LoginViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="testpass123")

    def test_login_get_shows_form(self):
        response = self.client.get(reverse("login_user"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "quotes/login_form.html")

    def test_login_valid_credentials_redirects_to_manage(self):
        response = self.client.post(reverse("login_user"), {"username": "admin", "password": "testpass123"})
        self.assertRedirects(response, reverse("quote_manage"))

    def test_login_invalid_credentials_shows_form(self):
        response = self.client.post(reverse("login_user"), {"username": "admin", "password": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "quotes/login_form.html")

    def test_login_empty_credentials_shows_form(self):
        response = self.client.post(reverse("login_user"), {"username": "", "password": ""})
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_redirects_to_manage(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.get(reverse("login_user"))
        self.assertRedirects(response, reverse("quote_manage"))

    def test_login_nonexistent_user(self):
        response = self.client.post(reverse("login_user"), {"username": "nobody", "password": "pass"})
        self.assertEqual(response.status_code, 200)


class QuoteAjaxTest(TestCase):
    def setUp(self):
        self.quote = Quote.objects.create(content="<user> ajax test", status=Quote.Status.APPROVED)

    def test_ajax_vote_up_returns_json(self):
        response = self.client.post(reverse("quote_ajax"), {"quote_id": self.quote.id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("current_votes", data)
        self.assertEqual(data["current_votes"], 1)

    def test_ajax_increments_votes_up(self):
        self.client.post(reverse("quote_ajax"), {"quote_id": self.quote.id})
        self.client.post(reverse("quote_ajax"), {"quote_id": self.quote.id})
        self.quote.refresh_from_db()
        self.assertEqual(self.quote.votes_up, 2)

    def test_ajax_missing_quote_id_returns_400(self):
        response = self.client.post(reverse("quote_ajax"), {})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Missing quote_id")

    def test_ajax_nonexistent_quote_returns_404(self):
        response = self.client.post(reverse("quote_ajax"), {"quote_id": 9999})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "Quote not found")

    def test_ajax_returns_karma_not_just_upvotes(self):
        self.quote.votes_down = 3
        self.quote.save()
        response = self.client.post(reverse("quote_ajax"), {"quote_id": self.quote.id})
        data = response.json()
        # votes_up becomes 1, votes_down stays 3, karma = -2
        self.assertEqual(data["current_votes"], -2)


class PaginationTest(TestCase):
    def setUp(self):
        for i in range(25):
            Quote.objects.create(content=f"<user> quote {i}", status=Quote.Status.APPROVED)

    def test_accepted_list_first_page_has_10_quotes(self):
        response = self.client.get(reverse("accepted_list"))
        self.assertEqual(len(response.context["quotes"]), 10)

    def test_accepted_list_second_page(self):
        response = self.client.get(reverse("accepted_list"), {"page": 2})
        self.assertEqual(len(response.context["quotes"]), 10)

    def test_accepted_list_last_page(self):
        response = self.client.get(reverse("accepted_list"), {"page": 3})
        self.assertEqual(len(response.context["quotes"]), 5)

    def test_accepted_list_invalid_page_shows_first(self):
        response = self.client.get(reverse("accepted_list"), {"page": "abc"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["quotes"]), 10)

    def test_accepted_list_out_of_range_page_shows_last(self):
        response = self.client.get(reverse("accepted_list"), {"page": 999})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["quotes"]), 5)

    def test_best_list_paginates(self):
        response = self.client.get(reverse("best_list"))
        self.assertEqual(len(response.context["quotes"]), 10)

    def test_best_list_page_2(self):
        response = self.client.get(reverse("best_list"), {"page": 2})
        self.assertEqual(len(response.context["quotes"]), 10)

    def test_trash_list_limited_to_10(self):
        Quote.objects.update(status=Quote.Status.REJECTED)
        response = self.client.get(reverse("trash_list"))
        self.assertEqual(len(response.context["quotes"]), 10)


class TemplateFilterTest(TestCase):
    def _render(self, template_string, context_dict):
        t = Template(template_string)
        return t.render(Context(context_dict))

    def test_sub_filter_basic(self):
        result = self._render("{% load quote_extras %}{{ a|sub:b }}", {"a": 10, "b": 3})
        self.assertEqual(result.strip(), "7")

    def test_sub_filter_negative_result(self):
        result = self._render("{% load quote_extras %}{{ a|sub:b }}", {"a": 3, "b": 10})
        self.assertEqual(result.strip(), "-7")

    def test_sub_filter_zero(self):
        result = self._render("{% load quote_extras %}{{ a|sub:b }}", {"a": 5, "b": 5})
        self.assertEqual(result.strip(), "0")

    def test_sub_filter_invalid_value_returns_empty(self):
        result = self._render("{% load quote_extras %}{{ a|sub:b }}", {"a": "not_a_number", "b": 5})
        self.assertEqual(result.strip(), "")

    def test_sub_filter_none_returns_empty(self):
        result = self._render("{% load quote_extras %}{{ a|sub:b }}", {"a": None, "b": 5})
        self.assertEqual(result.strip(), "")


class URLResolutionTest(TestCase):
    def test_all_named_urls_resolve(self):
        """Verify all URL names can be reversed (catches routing regressions)."""
        quote = Quote.objects.create(content="test")
        url_names_no_args = [
            "index_view",
            "login_user",
            "quote_manage",
            "accepted_list",
            "best_list",
            "trash_list",
            "quote_add",
            "quote_ajax",
        ]
        url_names_with_id = [
            "quote_view",
            "quote_accept",
            "quote_reject",
            "quote_delete",
            "quote_vote_up",
            "quote_vote_down",
        ]
        for name in url_names_no_args:
            url = reverse(name)
            self.assertTrue(url, f"Failed to reverse {name}")
        for name in url_names_with_id:
            url = reverse(name, args=[quote.id])
            self.assertTrue(url, f"Failed to reverse {name}")


class FormTest(TestCase):
    def test_form_only_exposes_content_field(self):
        from .forms import AddQuoteForm

        form = AddQuoteForm()
        self.assertEqual(list(form.fields.keys()), ["content"])

    def test_form_rejects_missing_content(self):
        from .forms import AddQuoteForm

        form = AddQuoteForm(data={})
        self.assertFalse(form.is_valid())

    def test_form_does_not_allow_status_override(self):
        from .forms import AddQuoteForm

        form = AddQuoteForm(data={"content": "test", "status": Quote.Status.APPROVED})
        self.assertTrue(form.is_valid())
        quote = form.save()
        self.assertEqual(quote.status, Quote.Status.PENDING)
