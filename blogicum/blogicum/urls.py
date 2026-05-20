from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from blog import views

handler404 = "pages.views.page_not_found"
handler500 = "pages.views.server_error"

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "auth/registration/",
        views.RegisterCreateView.as_view(),
        name="registration",
    ),
    path("auth/", include("django.contrib.auth.urls")),
    path("", include("blog.urls")),
    path("pages/", include("pages.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
