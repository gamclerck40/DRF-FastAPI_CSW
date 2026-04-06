from rest_framework import serializers


class EmbeddingRequestSerializer(serializers.Serializer):
    """
    여러 문장을 받아 FastAPI /embed로 전달할 때 사용
    """

    texts = serializers.ListField(child=serializers.CharField(), allow_empty=False)


class SimilarityRequestSerializer(serializers.Serializer):
    """
    두 문장을 받아 FastAPI /similarity 로 전달할 때 사용
    """

    text1 = serializers.CharField()
    text2 = serializers.CharField()
