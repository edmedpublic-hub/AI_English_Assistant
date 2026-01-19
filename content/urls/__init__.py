from .core_urls import urlpatterns as core_urls
from .chunk_urls import urlpatterns as chunk_urls
from .tests_urls import urlpatterns as test_urls
from .vocabulary_urls import urlpatterns as vocabulary_urls

urlpatterns = core_urls + chunk_urls + test_urls + vocabulary_urls
