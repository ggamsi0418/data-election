from django.shortcuts import render, HttpResponse
from .models import Upload, ChallengeRecord
import io
import base64
import subprocess
import json
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
# from .serializers import ChallengeRecordSerializer, UploadedFileSerializer
from datetime import datetime


def index(request):
    return render(request, 'fileManage/index.html', {})


@api_view(['POST'])
def upload(request):
    if request.method == 'POST':
        member_id = request.POST['member_id']
        file_type = request.POST['file_type']
        file_name = request.FILES['file'].name  # type: str
        file_location = request.FILES['file']  # type: InMemoryUploadFile
        # print(type(request.FILES['file'].name))
        # print(file_location)

        # return HttpResponse(f"{member_id}/{file_name}")

        uploadedFile = Upload(member_id=member_id, file_type=file_type,
                              file_name=file_name, file_location=file_location, )
        uploadedFile.save()

        return Response(data=None, status=status.HTTP_201_CREATED)

    elif request.method == 'GET':
        return Response(data=None, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def validation(request):
    if request.method == 'POST':
        upload_id = request.POST['upload_id']
        member_id = request.POST['member_id']
        file_name = Upload.objects.get(
            upload_id=upload_id, member_id=member_id).file_name  # type: str
        file_location = Upload.objects.get(
            upload_id=upload_id, member_id=member_id).file_location  # type: FieldFile

        copy = subprocess.run(
            f"cp ./upload/{file_location} ./work/{file_name}".split())

        # 저장된 .ipynb 파일을 .py로 변환
        process = subprocess.run(['jupyter', 'nbconvert', '--to',
                                  'python', f'./work/{file_name}'], capture_output=True, encoding='utf-8')

        # 변환된 .py를 서브프로세스에서 실행
        # excute = subprocess.Popen(['python', f'./work/{pk}.py'],
        #                           stdout=subprocess.PIPE, encoding='utf-8').stdout
        FILE_NAME = file_name[:-6]
        excute = subprocess.Popen(
            ['python', f'./work/{FILE_NAME}.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')

        # log.txt 작성
        today = datetime.now()
        today_date = f"{today.year}_{today.month}_{today.day}"

        output_msg = excute.stdout.read()
        error_msg = excute.stderr.read()

        with open(f'./work/logs/{today_date}_log.txt', 'at') as file:
            file.write(f"\n\
---------------------------------- log of upload_id({upload_id}) & memeber_id({member_id}) : {datetime.now()} ----------------------------------\n\
출력 메시지:\n{output_msg}\n\
에러 메시지:\n{error_msg}\
------------------------------------------------------------------------------------------------------------------------------------------\n\
")

        # 최종 결과가 기록되어 있는 result.txt 파일을 열어서 값을 읽어 온다. ex) 강남구 값, 홍길동
        with open('./work/result.txt', 'r') as file:
            result = file.read()

        precinct, candidate = result.split(', ')

        validation = True if error_msg == "" else False

        uploadRow = Upload.objects.get(upload_id=upload_id)
        uploadRow.validation = validation
        uploadRow.save()

        try:
            recordRow = ChallengeRecord.objects.get(
                member_id=member_id, precinct=precinct)
            recordRow.candidate = candidate
            recordRow.admin_check = None
            recordRow.save()
        except:
            recordRow = ChallengeRecord(
                member_id=member_id, precinct=precinct, candidate=candidate)
            recordRow.save()

        excute = subprocess.Popen(
            f'rm -r ./work/{FILE_NAME}.ipynb ./work/{FILE_NAME}.py'.split())

        result = {
            'upload_id': upload_id,
            'member_id': member_id,
            'validation': validation,
            'precinct': precinct,
            'candidate': candidate,
            'error_msg': error_msg
        }

        return Response(data=result, status=status.HTTP_201_CREATED)

    elif request.method == 'GET':
        return Response(data=None, status=status.HTTP_400_BAD_REQUEST)
