from django.conf import settings
from django.db import models


class Quote(models.Model):
    class Status(models.IntegerChoices):
        PENDING = 1, "Is pending"
        REJECTED = 2, "Is rejected"
        APPROVED = 3, "Is approved"

    acceptant = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    content = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    votes_up = models.PositiveIntegerField(default=0)
    votes_down = models.PositiveIntegerField(default=0)
    status = models.IntegerField(default=Status.PENDING, choices=Status.choices)

    class Meta:
        ordering = ["-created_date"]

    def __str__(self):
        return self.content
