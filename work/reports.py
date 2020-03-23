import hashlib
import json


def md5(needHash):
    return hashlib.md5(needHash.encode("utf-8")).hexdigest()


def checkResult(vote):

    # init = vote['init']
    # fini = json.dumps(vote)
    prec = vote['precinct']
    cand = vote['candidate']

    with open("./work/result.txt", 'w') as f:
        f.write(f'{prec}, {cand}')

    # f.write("init: %s \n" % md5(init))
    # f.write("fini: %s \n" % md5(fini))
    # f.write("prec: %s \n" % prec)
    # f.write("cand: %s \n" % cand)
    # f.close()
