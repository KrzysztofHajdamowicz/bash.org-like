from django.db import models
from django.utils import timezone

# Create your models here.
class Quote(models.Model):
	acceptant = models.ForeignKey('auth.User', null=True)
	content = models.TextField(null=False)
	created_date = models.DateTimeField(default=timezone.now)
	votes_up = models.PositiveIntegerField(default=0)
	votes_down = models.PositiveIntegerField(default=0)
	# status
	# 1 - is pending
	# 2 - is rejected
	# 3 - is approved
	status = models.PositiveIntegerField(default=1)

	def publish(self):
		self.published_date = timezone.now()
		self.save()
	def __str__(self):
		return self.content