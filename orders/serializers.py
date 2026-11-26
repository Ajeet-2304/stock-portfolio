from rest_framework import serializers
from .models import Order, Execution
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model=Order
        fields=("id","portfolio","instrument","side","order_type","quantity","limit_price","status","created_at")
        read_only_fields=("id","status","created_at","portfolio")
class ExecutionSerializer(serializers.Serializer):
    external_execution_id=serializers.CharField(max_length=120,required=False,allow_blank=True)
    quantity=serializers.DecimalField(max_digits=20,decimal_places=4)
    price=serializers.DecimalField(max_digits=20,decimal_places=6)
    executed_at=serializers.DateTimeField(required=False)



