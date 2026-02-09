# content/urls/punctuation_urls.py

from django.urls import path
from content.views.punctuation import teach, practice, test

app_name = "punctuation"



urlpatterns = [
    path("<int:focus_id>/teach/", teach.teach_punctuation_view, name="teach"),
    path("<int:focus_id>/practice/", practice.punctuation_practice, name="practice"),
    path("<int:focus_id>/test/", test.punctuation_test, name="test"),
    path("<int:focus_id>/test/result/", test.punctuation_test_result, name="test_result"),
]