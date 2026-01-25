# content/urls/__init__.py
import importlib
import pkgutil
from django.urls import path

# Namespace for reverse lookups in templates
app_name = "content"

urlpatterns = []

# Dynamically import all *_urls.py modules inside this package
package = __name__  # "content.urls"
for _, module_name, is_pkg in pkgutil.iter_modules(__path__):
    if module_name.endswith("_urls"):
        module = importlib.import_module(f"{package}.{module_name}")
        if hasattr(module, "urlpatterns"):
            urlpatterns.extend(module.urlpatterns)