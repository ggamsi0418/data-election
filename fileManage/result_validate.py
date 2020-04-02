from .models import Upload, ChallengeRecord, CandidateInfo


def result_validate(precinct, candidate):
    cond = CandidateInfo.objects.filter(precinct=precinct).exists()

    if cond:
        candidate_list = CandidateInfo.objects.filter(precinct=precinct).values_list(
            "candidate", flat=True
        )
        if candidate in candidate_list:
            return (True, "")
        else:
            error_msg = "지역구와후보자명이잘못매칭됐습니다."
            return (False, error_msg)
    else:
        error_msg = "지역구가잘못입력됐습니다."
        return (False, error_msg)
