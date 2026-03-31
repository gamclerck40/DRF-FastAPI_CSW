from rest_framework import serializers


class SentimentRequestSerializer(serializers.Serializer):
    text = serializers.CharField()


class SentimentResponseSerializer(serializers.Serializer):
    sentiment = serializers.CharField()
    confidence = serializers.FloatField()
    keywords = serializers.ListField(child=serializers.CharField(), required=False)
