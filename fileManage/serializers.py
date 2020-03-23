from rest_framework import serializers
from .models import ChallengeRecord, UploadedFile

"""
Serializer란 qureyset과 모델 인스턴스와 같은 복잡한 데이터를 json, xml 또는 다른 콘텐츠 유형으로 쉽게 변환할 수 있다.
받은 데이터의 유효성을 검사한 다음, 복잡한 타입으로 형 변환할 수 있도도록 serialization을 제공한다.

"""


class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = '__all__'


class ChallengeRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeRecord
        fields = '__all__'
