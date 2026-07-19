from dataclasses import dataclass
from src.hadocs.application.manage_policies import ManagePoliciesApplication
from src.hadocs.application.preview_policy import PreviewPolicyApplication
from src.hadocs.persistence.database import Database
from src.hadocs.persistence.policy_repository import PolicyRepository

@dataclass(slots=True)
class ApiServices:
    database: Database
    policies: ManagePoliciesApplication
    policy_preview: PreviewPolicyApplication


def build_api_services(database=None) -> ApiServices:
    db = database or Database()
    db.migrate()
    repository = PolicyRepository(db)
    return ApiServices(
        db,
        ManagePoliciesApplication(repository),
        PreviewPolicyApplication(),
    )
