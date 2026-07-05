from dataclasses import dataclass


@dataclass
class ProjectQuality:
    tests_present: bool
    readme_present: bool
    changelog_present: bool
    security_present: bool
    docs_present: bool

    @property
    def score(self) -> int:
        checks = [self.tests_present, self.readme_present, self.changelog_present, self.security_present, self.docs_present]
        return round((sum(1 for check in checks if check) / len(checks)) * 100)

    @property
    def release_ready(self) -> bool:
        return self.score == 100
