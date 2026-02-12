# content/urls/__init__.py

import importlib
import pkgutil

app_name = "content"

urlpatterns = []

package = __name__  # "content.urls"

for _, module_name, is_pkg in pkgutil.iter_modules(__path__):
    # Skip private files and __init__
    if module_name.startswith("_"):
        continue

    module = importlib.import_module(f"{package}.{module_name}")

    if hasattr(module, "urlpatterns"):
        urlpatterns.extend(module.urlpatterns)
