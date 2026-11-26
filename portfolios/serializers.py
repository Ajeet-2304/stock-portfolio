from rest_framework import serializers
from .models import Portfolio, CashLedgerEntry

class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model=Portfolio
        fields=("id","name","base_currency","created_at")
        read_only_fields=("id","created_at")

class CashLedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model=CashLedgerEntry
        fields=("id","entry_type","amount","reference","description","created_at")
        read_only_fields=("id","created_at")
