# from rest_framework import viewsets
# import json
# import base64
# from .serializers import ChallengeRecordSerializer, UploadedFileSerializer
# from rest_framework.decorators import renderer_classes
from rest_framework.renderers import JSONRenderer
from django.shortcuts import render, HttpResponse
from .models import Upload, ChallengeRecord, CandidateInfo
from .result_validate import result_validate
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import datetime
import subprocess
import after_response
import sys


def index(request):
    return render(request, "fileManage/index.html", {})


@api_view(["POST"])
def upload(request):
    if request.method == "POST":
        member_id = request.POST["member_id"]
        file_type = request.POST["file_type"]
        file_name = request.FILES["file"].name  # type: str
        file_location = request.FILES["file"]  # type: InMemoryUploadFile

        uploadedFile = Upload(
            member_id=member_id,
            file_type=file_type,
            file_name=file_name,
            file_location=file_location,
        )

        uploadedFile.save()
        makeFolder = subprocess.run(f"mkdir -p ./temp/{member_id}/data/".split())
        copy = subprocess.run(
            f"cp ./ptemplate/reports.py ./temp/{member_id}/data/reports.py".split()
        )

        return Response(data=None, status=status.HTTP_201_CREATED)

    elif request.method == "GET":
        return Response(data=None, status=status.HTTP_400_BAD_REQUEST)


@after_response.enable
def verify(upload_id, member_id, member_email):
    today = datetime.now()
    today_date = f"{today.year}_{today.month}_{today.day}"

    file_name = Upload.objects.get(
        upload_id=upload_id, member_id=member_id
    ).file_name  # type: str

    file_location = Upload.objects.get(
        upload_id=upload_id, member_id=member_id
    ).file_location  # type: FieldFile

    # 참가자가 업로드한 .ipynb 파일을 data 폴더로 복사하기
    copy = subprocess.run(
        f"cp ./temp/{file_location} ./temp/{member_id}/data/{file_name}".split()
    )

    # data 폴더로 복사해온 .ipynb 파일을 .py로 변환하기 (by 서브프로세스)
    process = subprocess.run(
        [
            "jupyter",
            "nbconvert",
            "--to",
            "python",
            f"./temp/{member_id}/data/{file_name}",
        ],
        capture_output=True,
        encoding="utf-8",
    )

    # 파일명과 확장자 분리하기
    FILE_NAME = file_name[:-6]

    # 변환된 .py를 실행하기 (by 서브프로세스)
    excute = subprocess.Popen(
        ["python", f"./temp/{member_id}/data/{FILE_NAME}.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )

    # 서브프로세스에서 출력되는 에러 메시지 받아오기
    # output_msg = excute.stdout.read()
    error_msg = excute.stderr.read()

    # 컴파일 에러가 발생했을 경우 로그 작성하기
    if error_msg != "":

        result_status = "컴파일에러"
        result_description = error_msg.replace(" ", "").replace("\n", "")

        with open(f"./logs/{today_date}_log.txt", "at") as file:
            file.write(
                f"<[{datetime.now()}] {member_email} {result_status} {result_description}>\n"
            )

    #
    try:
        # 최종 결과가 기록되어 있는 result.txt 파일을 열어서 분석 결과값을 읽어 온다. ex) 강남구 값, 홍길동
        with open(f"./temp/{member_id}/data/result.txt", "r") as file:
            result = file.read()

        precinct, candidate = result.split(", ")
    except Exception:
        # Exception : [Errno 2] No such file or directory: './temp/{member_id}/data/result.txt'
        # 복사해 온 .ipynb 파일과 변환된 .py 파일 삭제하기
        excute = subprocess.Popen(
            f"rm -r ./temp/{member_id}/data/{FILE_NAME}.ipynb ./temp/{member_id}/data/{FILE_NAME}.py".split()
        )
        print("컴파일 에러로 인해 검증을 종료합니다.")
        sys.exit(0)

    # 분석 결과값(지역구와 후보명) 검증하기
    valid_result, error_msg = result_validate(precinct, candidate)

    validation = True if error_msg == "" else False

    # 분석 결과값 검증을 통과 했다면 upload 테이블과 challenge_record 테이블에 값 반영하기
    if valid_result:
        result_status = "정상처리"

        uploadRow = Upload.objects.get(upload_id=upload_id)
        uploadRow.validation = True
        uploadRow.save()

        recordRow = ChallengeRecord(
            member_id=member_id, precinct=precinct, candidate=candidate
        )
        recordRow.save()
    else:
        result_status = "잘못된출력값"

    # 분석 결과값 검증에서 오류가 있는 경우 로그 작성하기
    result_description = error_msg.replace(" ", "").replace("\n", "")

    with open(f"./logs/{today_date}_log.txt", "at") as file:
        file.write(
            f"<[{datetime.now()}] {member_email} {result_status} {result_description}>\n"
        )

    # 복사해 온 .ipynb 파일과 변환된 .py 파일 삭제하기
    excute = subprocess.Popen(
        f"rm -r ./temp/{member_id}/data/result.txt ./temp/{member_id}/data/{FILE_NAME}.ipynb ./temp/{member_id}/data/{FILE_NAME}.py".split()
    )

    result = {
        "upload_id": upload_id,
        "member_id": member_id,
        "validation": validation,
        "precinct": precinct,
        "candidate": candidate,
        "error_msg": error_msg,
    }

    print(result)
    return Response(data=result, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def djangoServer(request):
    if request.method == "POST":

        upload_id = request.POST["upload_id"]
        member_id = request.POST["member_id"]
        member_email = request.POST["member_email"]

        msg = {"message": "정상적으로 접수됐습니다."}

        verify.after_response(upload_id, member_id, member_email)

        return Response(data=msg, status=status.HTTP_200_OK)

    elif request.method == "GET":
        msg = {"message": "잘못된 요청입니다."}
        return Response(data=msg, status=status.HTTP_400_BAD_REQUEST)
