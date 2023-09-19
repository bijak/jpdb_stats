import base64
from datetime import datetime
import io
import json
from datetime import datetime
import pytz


def is_successful(string):
    if string in ["known", "pass", "hard", "easy", "okay"]:
        return 1
    return 0


def is_fail(string):
    if string in ["known", "pass", "hard", "easy", "okay", "abandoned"]:
        return 0
    return 1


def parse_data(contents, timezone):
    decoded = base64.b64decode(contents)
    new = []
    rep = []
    history = []
    struggles = []
    try:
        reviews_json = json.load(io.StringIO(decoded.decode("utf-8")))
        for entry in (
            reviews_json["cards_vocabulary_jp_en"]
            + reviews_json["cards_kanji_char_keyword"]
            + reviews_json["cards_kanji_keyword_char"]
        ):
            if len(entry["reviews"]) == 0:
                continue
            new.append(
                datetime.utcfromtimestamp(entry["reviews"][0]["timestamp"])
                .astimezone(pytz.timezone(timezone))
                .date()
            )
            for review in entry["reviews"]:
                if review["grade"] != "abandoned":
                    rep.append(
                        datetime.utcfromtimestamp(review["timestamp"]).astimezone(
                            pytz.timezone(timezone)
                        )
                    )
            entry_hist, word_totals = parse_entry(entry, timezone)
            history += entry_hist
            struggles += word_totals
    except Exception as e:
        print(e)
        return None, None, None, None

    return new, rep, history, struggles


def parse_entry(entry, timezone):
    history = []
    previous = None
    time_to_learn = 0
    relapses = 0
    abandoned = 0
    everKnown = False
    isKnown = False
    consecutive_success = 0
    first_review = True
    for review in entry["reviews"]:
        if first_review:
            first_reviewed = datetime.utcfromtimestamp(review["timestamp"]).astimezone(
                pytz.timezone(timezone)
            )
            first_review = False
        # The rows are date, fail, pass, new, abandoned, isKnown (state before the review)
        if previous is None:
            history.append(
                [
                    datetime.utcfromtimestamp(review["timestamp"]).date(),
                    0,
                    0,
                    1,
                    0,
                    isKnown,
                ]
            )
        elif (previous["grade"] == "abandoned") and review["grade"] != "abandoned":
            history.append(
                [
                    datetime.utcfromtimestamp(review["timestamp"]).date(),
                    0,
                    0,
                    1,
                    0,
                    False,
                ]
            )
        elif review["grade"] == "abandoned":
            history.append(
                [
                    datetime.utcfromtimestamp(review["timestamp"]).date(),
                    0,
                    0,
                    0,
                    1,
                    False,
                ]
            )
        elif (previous is not None) and (
            datetime.utcfromtimestamp(previous["timestamp"])
            .astimezone(pytz.timezone(timezone))
            .date()
            != datetime.utcfromtimestamp(review["timestamp"]).date()
        ):
            history.append(
                [
                    datetime.utcfromtimestamp(review["timestamp"])
                    .astimezone(pytz.timezone(timezone))
                    .date(),
                    is_fail(review["grade"]),
                    is_successful(review["grade"]),
                    0,
                    0,
                    isKnown,
                ]
            )
        previous = review

        # This is the logic handling the change in state between known, and tracking word level stats
        if is_successful(review["grade"]):
            if (not everKnown) and (time_to_learn < 1):
                everKnown = True
                isKnown = True
            elif (not everKnown) and (consecutive_success == 2):
                everKnown = True
                isKnown = True
                time_to_learn += 1
            elif not everKnown:
                consecutive_success += 1
                time_to_learn += 1
            elif (not isKnown) and (consecutive_success == 2):
                isKnown = True
            elif not isKnown:
                consecutive_success += 1
        elif review["grade"] == "abandoned":
            consecutive_success = 0
            isKnown = False
            abandoned += 1
            everKnown = False
        else:
            consecutive_success = 0
            if isKnown:
                isKnown = False
                relapses += 1
            if not everKnown:
                time_to_learn += 1
    return history, [
        [
            entry.get("spelling") or ("Kanji: " + entry["character"]),
            len(entry["reviews"]),
            time_to_learn,
            relapses,
            abandoned,
            first_reviewed,
        ]
    ]
