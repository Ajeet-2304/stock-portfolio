from django.contrib import admin
from orders.models import *
# Register your models here.
admin.site.register(Order)
admin.site.register(Execution)
admin.site.register(TaxLot)
admin.site.register(LotConsumption)