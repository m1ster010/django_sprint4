from django.contrib import admin
from .models import Category, Location, Post


class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "pub_date", "author", "category", "is_published")
    list_editable = ("is_published", "category")
    search_fields = ("title", "text")
    list_filter = ("category", "is_published", "pub_date")


admin.site.register(Post, PostAdmin)
admin.site.register(Category)
admin.site.register(Location)
