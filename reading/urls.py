# reading/urls.py

from django.urls import path
from .views import (
    reading_home,
    reading_detail,
)

app_name = "reading"  # important for namespaced URL reverses

urlpatterns = [
    # --------------------
    # Template Pages
    # --------------------
    path("", reading_home, name="home"),              # /reading/
    path("<int:pk>/", reading_detail, name="detail"), # /reading/5/
]