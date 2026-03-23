from django.contrib.auth.models import User
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


class QuoteDetailViewTest(TestCase):
    def test_view_single_quote(self):
        quote = Quote.objects.create(content="<a> test quote", status=Quote.Status.APPROVED)
        response = self.client.get(reverse("quote_view", args=[quote.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["quote"], quote)

    def test_view_nonexistent_quote_returns_404(self):
        response = self.client.get(reverse("quote_view", args=[9999]))
        self.assertEqual(response.status_code, 404)
