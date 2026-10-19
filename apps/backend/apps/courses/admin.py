from django.contrib import admin
from django.apps import apps
# Register your models here.
# Register your models here.

app_models = apps.get_app_config('courses').get_models()


for model in app_models:
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        # This prevents errors if you manually registered a model earlier
        pass
