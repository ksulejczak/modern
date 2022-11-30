import re

import pytest

from modern.codecs.validators.regex import RegexMatch

RE_REGEX_MATCH = RegexMatch(re.compile(r"[A-Z][a-z]+ [a-z]+[A-Z]"))
STR_REGEX_MATCH = RegexMatch(r"[A-Z][a-z]+ [a-z]+[A-Z]")

MATCHES = [
    "Frodo bagginS",
]
NOT_MATCHES = [
    "SauroN",
    " Frodo bagginS",
    "F bagginS",
    "frodo bagginS",
]


@pytest.mark.parametrize("regex_match", [RE_REGEX_MATCH, STR_REGEX_MATCH])
@pytest.mark.parametrize("value", MATCHES)
def test_matches(regex_match: RegexMatch, value: str) -> None:
    assert regex_match(value) is True


@pytest.mark.parametrize("regex_match", [RE_REGEX_MATCH, STR_REGEX_MATCH])
@pytest.mark.parametrize("value", NOT_MATCHES)
def test_not_matches(regex_match: RegexMatch, value: str) -> None:
    assert regex_match(value) is False
