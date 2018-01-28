from django.contrib.admin import AdminSite, site


class LS2AdminSite(AdminSite):
    site_header = 'Curiosity Health LS2 Admin'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._registry.update(site._registry)  # PART 2

admin_site = LS2AdminSite(name='ls2_admin')
