from django.db import models

STATUS_CHOICES = (
    (1, 'Is pending'),
    (2, 'Is rejected'),
    (3, 'is approved'),
)


# Create your models here.
class Quote(models.Model):
    acceptant = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.SET_NULL)
    content = models.TextField(null=False)
    created_date = models.DateTimeField(auto_now_add=True)
    votes_up = models.PositiveIntegerField(default=0)
    votes_down = models.PositiveIntegerField(default=0)
    status = models.PositiveIntegerField(default=1, choices=STATUS_CHOICES)

    def __str__(self):
        return self.content
