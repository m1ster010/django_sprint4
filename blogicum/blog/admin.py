from django.contrib import admin
from .models import Category, Location, Post, Comment
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

# Django автоматические регистрирует модель User, поэтому
# нужно зарегестировать её заново со специальным классом UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "pub_date", "author", "category", "is_published")
    list_editable = ("is_published", "category")
    search_fields = ("title", "text")
    list_filter = ("category", "is_published", "pub_date")


class CommentAdmin(admin.ModelAdmin):
    list_display = ("text", "post", "author", "created_at")
    search_fields = ("text",)


admin.site.register(Post, PostAdmin)
admin.site.register(Category)
admin.site.register(Location)
admin.site.register(Comment, CommentAdmin)
