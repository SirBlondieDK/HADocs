from datetime import datetime, timezone

class ManagePoliciesApplication:
    def __init__(self, repository) -> None:
        self.repository = repository

    def list(self, include_disabled: bool = True):
        return self.repository.list(include_disabled)

    def save(self, policy):
        policy.updated_at = datetime.now(timezone.utc)
        return self.repository.save(policy)

    def delete(self, policy_id: str) -> bool:
        return self.repository.delete(policy_id)
