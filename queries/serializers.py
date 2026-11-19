from rest_framework import serializers

from .models import CustomerQuery


class CustomerQuerySerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.username')

    class Meta:
        model = CustomerQuery
        fields = [
            'id', 'customer_name', 'email', 'subject', 'description',
            'category', 'priority', 'status', 'suggested_response',
            'analysed_by', 'analysed_at', 'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['suggested_response', 'analysed_by', 'analysed_at', 'created_at', 'updated_at']

    def validate_customer_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError('Customer name must be at least 2 characters.')
        if any(char.isdigit() for char in value):
            raise serializers.ValidationError('Customer name should not contain numbers.')
        return value

    def validate_subject(self, value):
        value = value.strip()
        if len(value) < 5:
            raise serializers.ValidationError('Subject must be at least 5 characters.')
        return value

    def validate_description(self, value):
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError('Description must be at least 10 characters.')
        return value


class StatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=CustomerQuery.STATUS_CHOICES)
