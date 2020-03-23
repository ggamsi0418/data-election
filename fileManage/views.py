from django.shortcuts import render, HttpResponse
from .models import UploadedFile, ChallengeRecord
import io
import base64
import subprocess
import json
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from .serializers import ChallengeRecordSerializer, UploadedFileSerializer
from datetime import datetime


def index(request):
    return render(request, 'fileManage/index.html', {})


@api_view(['POST'])
def upload(request):
    if request.method == 'POST':
        file = request.FILES['file'].file
        # print("업로드 받은 파일: ", type(file))
        byte_file = file.read()
        # print(type(byte_file))
        byte_file = byte_file.decode('UTF-8')
        # print(type(byte_file))
        # print(byte_file)
        uploadedFile = UploadedFile(file=byte_file)
        uploadedFile.save()
        return Response(data=None, status=status.HTTP_201_CREATED)
    elif request.method == 'GET':
        return Response(data=None, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def validation(request):
    if request.method == 'POST':
        # 검증 요청 파일의 pk로 제목 지정
        # 실제로는 pk를 통해서 참가자의 id(?)도 가져와야 한다.
        pk = request.POST.get('file_id')
        title = f'{pk}.ipynb'

        # 해당 pk를 통해서 DB로부터 파일을 꺼내오고 로컬에 저장 (.ipynb)
        file = UploadedFile.objects.filter(
            file_id=pk).values('file')[0]['file']
        with open(f'work/{title}', 'wb') as f:
            f.write(file)

        # 저장된 .ipynb 파일을 .py로 변환
        process = subprocess.run(['jupyter', 'nbconvert', '--to',
                                  'python', f'./work/{title}'], capture_output=True, encoding='utf-8')

        # 변환된 .py를 서브프로세스에서 실행
        # excute = subprocess.Popen(['python', f'./work/{pk}.py'],
        #                           stdout=subprocess.PIPE, encoding='utf-8').stdout
        excute = subprocess.Popen(
            ['python', f'./work/{pk}.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')

        # log.txt 작성
        today = datetime.now()
        today_date = f"{today.year}_{today.month}_{today.day}"

        output_msg = excute.stdout.read()
        error_msg = excute.stderr.read()

        with open(f'./work/logs/{today_date}_log.txt', 'at') as file:
            file.write(f"\n\
---------------------------------- log of pk {pk} : {datetime.now()} ----------------------------------\n\
출력 메시지:\n{output_msg}\n\
에러 메시지:\n{error_msg}\
----------------------------------------------------------------------------------------------------------------\n\
")

        # 최종 결과가 기록되어 있는 result.txt 파일을 열어서 값을 읽어 온다. ex) 강남구 값, 홍길동
        with open('./work/result.txt', 'r') as file:
            result = file.read()

        # 가져온 결과값을 지역구와 후보자로 나눈 뒤, ChallengeRecord 테이블에 반영.
        # 실제로는 업로드 테이블에서의 pk값이 아닌 참가자의 id를 통해서 저장해야 한다.
        # ChallengeRecord 테이블이 업데이트 되는 테이블이므로 추가적인 쿼리를 생각해야 한다.
        # 예를 들면, 강남구 갑, 홍길동에서 강남구 갑, 이순신으로 바뀌는 경우.
        precinct, candidate = result.split(', ')
        reflection = ChallengeRecord(
            file_id=pk, precinct=precinct, candidate=candidate)
        reflection.save()

        excute = subprocess.Popen(
            f'rm -r ./work/{pk}.ipynb ./work/{pk}.py'.split())

        is_valid = True if error_msg == "" else False

        result = {
            'file_id': pk,
            'is_valid': is_valid,
            'precinct': precinct,
            'candidate': candidate,
            'error_msg': error_msg
        }
        return Response(data=result, status=status.HTTP_201_CREATED)
    elif request.method == 'GET':
        return Response(data=None, status=status.HTTP_400_BAD_REQUEST)
