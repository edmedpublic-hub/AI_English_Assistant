# content/urls/punctuation_urls.py

from django.urls import path
from content.views.punctuation import teach, practice, test

app_name = "punctuation"

urlpatterns = [
    # chunk_id is already captured by the include in chunk_urls.py
    path("<int:focus_id>/teach/", teach.teach_punctuation_view, name="teach"),
    path("<int:focus_id>/practice/", practice.punctuation_practice, name="practice"),
    path("<int:focus_id>/test/", test.punctuation_test, name="test"),
   
]