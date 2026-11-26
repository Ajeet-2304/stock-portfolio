from rest_framework import serializers
from .models import Exchange, Instrument, DailyPrice, CorporateAction, ExchangeHoliday

class ExchangeSerializer(serializers.ModelSerializer):
    class Meta: model=Exchange; fields="__all__"
class InstrumentSerializer(serializers.ModelSerializer):
    class Meta: model=Instrument; fields="__all__"
class DailyPriceSerializer(serializers.ModelSerializer):
    class Meta: model=DailyPrice; fields="__all__"
class CorporateActionSerializer(serializers.ModelSerializer):
    class Meta: model=CorporateAction; fields="__all__"
class ExchangeHolidaySerializer(serializers.ModelSerializer):
    class Meta: model=ExchangeHoliday; fields="__all__"
