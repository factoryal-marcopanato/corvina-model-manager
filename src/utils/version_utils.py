import re


def _check_changelog_file() -> list[str] | None:
    try:
        with open('CHANGELOG.txt', 'r') as fd:
            data = fd.readlines()
            return data
    except Exception:
        pass
    try:
        with open('../CHANGELOG.txt', 'r') as fd:
            data = fd.readlines()
            return data
    except Exception:
        return None


def _parse_changelog_rows(rows: list[str]) -> str:
    version_re = re.compile(r'v(\d\.\d\.\d(?:-dev)?) - (\d\d\d\d/\d\d/\d\d)')
    for row in rows:
        if row.startswith('-'):
            return '??/??/?? v?.?.? (cannot read CHANGELOG.txt)'
        match = version_re.match(row)
        if match:
            return f'{match.groups()[1]} v{match.groups()[0]}'
    return '??/??/?? v?.?.? (invalid CHANGELOG.txt format)'


def get_version_and_date() -> str:
    changelog_data = _check_changelog_file()
    if changelog_data is None:
        return '??/??/?? v?.?.? (CHANGELOG.txt not found)'
    return _parse_changelog_rows(changelog_data)
