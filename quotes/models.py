from django.db import models


class Quote(models.Model):
    STATUS_PENDING = 1
    STATUS_REJECTED = 2
    STATUS_APPROVED = 3

    STATUS_CHOICES = (
        (STATUS_PENDING, "Is pending"),
        (STATUS_REJECTED, "Is rejected"),
        (STATUS_APPROVED, "Is approved"),
    )

    acceptant = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.SET_NULL)
    content = models.TextField(null=False)
    created_date = models.DateTimeField(auto_now_add=True)
    votes_up = models.PositiveIntegerField(default=0)
    votes_down = models.PositiveIntegerField(default=0)
    status = models.PositiveIntegerField(default=STATUS_PENDING, choices=STATUS_CHOICES)

    class Meta:
        ordering = ["-created_date"]

    def __str__(self):
        return self.content
