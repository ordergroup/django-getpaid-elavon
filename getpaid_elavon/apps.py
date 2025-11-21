from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class GetpaidElavonAppConfig(AppConfig):
    name = "getpaid_elavon"
    verbose_name = _("Elavon")

    def ready(self):
        from getpaid.registry import registry

        registry.register(self.module)
