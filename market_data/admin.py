from django.contrib import admin

from market_data.models import Exchange, Instrument, DailyPrice, CorporateAction, ExchangeHoliday

# Register your models here.

admin.site.register(Exchange)
admin.site.register(Instrument)
admin.site.register(DailyPrice)
admin.site.register(CorporateAction)
admin.site.register(ExchangeHoliday)




