from django.contrib import admin
from .models import Quote

# TODO: Add a ModelAdmin with list_display, list_filter, search_fields, and readonly_fields
admin.site.register(Quote)
