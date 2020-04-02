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
            error_msg = "잘못된후보명"
            return (False, error_msg)
    else:
        error_msg = "잘못된지역구"
        return (False, error_msg)
