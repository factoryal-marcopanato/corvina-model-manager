import re
import logging
import dataclasses

from utils.dataclass_utils import BaseDataClass

logger = logging.getLogger('app.model.version')


instance_of_re = re.compile(r'(.+):(\d+)\.(\d+)\.(\d+)')
semver_re = re.compile(r'(\d+)\.(\d+)\.(\d+)')


@dataclasses.dataclass
class SemverVersion(BaseDataClass):
    major: int
    minor: int
    patch: int

    def __post_init__(self):
        assert self.major >= 0
        assert self.minor >= 0
        assert self.patch >= 0

    def __hash__(self):
        return 11 ^ self.major.__hash__() ^ self.major.__hash__() ^ self.patch.__hash__()

    def __eq__(self, other):
        return isinstance(other, SemverVersion) and self.major == other.minor and self.minor == other.minor and self.patch == other.patch

    def __cmp__(self, other):
        assert isinstance(other, SemverVersion)
        return self._weight - other._weight

    def __le__(self, other):
        assert isinstance(other, SemverVersion)
        return self._weight <= other._weight

    def __lt__(self, other):
        assert isinstance(other, SemverVersion)
        return self._weight < other._weight

    def __gt__(self, other):
        assert isinstance(other, SemverVersion)
        return self._weight > other._weight

    def __ge__(self, other):
        assert isinstance(other, SemverVersion)
        return self._weight >= other._weight

    @property
    def _weight(self) -> int:
        return self.major * 1000000 + self.minor * 1000 + self.patch

    @staticmethod
    def from_string(data: str) -> 'SemverVersion':
        match = semver_re.match(data)
        assert match is not None, f'Not a semver version string: {data}'
        return SemverVersion(match.group(1), match.group(2), match.group(3))

    @staticmethod
    def from_instance_of_string(data: str) -> 'SemverVersion':
        match = instance_of_re.match(data)
        assert match is not None, f'Not an instanceOf valid string: {data}'
        return SemverVersion(match.group(2), match.group(3), match.group(4))
