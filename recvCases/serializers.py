from rest_framework import serializers
class TestCaseSerializer(serializers.Serializer):
    problem_id=serializers.IntegerField(required=True)
    file=serializers.FileField(required=True)