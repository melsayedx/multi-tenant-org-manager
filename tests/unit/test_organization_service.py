import pytest

from app.core.exceptions import ConflictException, NotFoundException
from app.core.utils import uuid7
from app.models.membership import Membership, Role
from app.models.organization import Organization
from app.models.user import User
from app.services.organization import OrgService


def _service(mock_org_repo, mock_membership_repo, mock_user_repo, mock_audit_repo) -> OrgService:
    return OrgService(mock_org_repo, mock_membership_repo, mock_user_repo, mock_audit_repo)


async def test_create_organization_returns_org(
    mock_org_repo, mock_membership_repo, mock_user_repo, mock_audit_repo
):
    creator_id = uuid7()
    org = Organization(id=uuid7(), name="Test Org")
    mock_org_repo.create.return_value = org
    mock_membership_repo.create.return_value = Membership(
        user_id=creator_id, org_id=org.id, role=Role.ADMIN
    )

    result = await _service(
        mock_org_repo, mock_membership_repo, mock_user_repo, mock_audit_repo
    ).create_organization("Test Org", creator_id)

    assert result.name == "Test Org"
    mock_org_repo.create.assert_called_once()
    mock_membership_repo.create.assert_called_once()
    mock_audit_repo.create.assert_called_once()


async def test_create_organization_assigns_admin_role(
    mock_org_repo, mock_membership_repo, mock_user_repo, mock_audit_repo
):
    creator_id = uuid7()
    org = Organization(id=uuid7(), name="Test Org")
    mock_org_repo.create.return_value = org

    await _service(
        mock_org_repo, mock_membership_repo, mock_user_repo, mock_audit_repo
    ).create_organization("Test Org", creator_id)

    created: Membership = mock_membership_repo.create.call_args[0][0]
    assert created.role == Role.ADMIN
    assert created.user_id == creator_id


async def test_invite_user_success(
    mock_org_repo, mock_membership_repo, mock_user_repo, mock_audit_repo
):
    org_id = uuid7()
    inviter_id = uuid7()
    user = User(id=uuid7(), email="new@test.com", full_name="New User", password="hashed")
    membership = Membership(user_id=user.id, org_id=org_id, role=Role.MEMBER)

    mock_membership_repo.get_user_and_membership.return_value = (user, None)
    mock_membership_repo.create.return_value = membership

    result = await _service(
        mock_org_repo, mock_membership_repo, mock_user_repo, mock_audit_repo
    ).invite_user(org_id, "new@test.com", "member", inviter_id)

    assert result.role == Role.MEMBER
    mock_audit_repo.create.assert_called_once()


async def test_invite_user_not_found_raises(
    mock_org_repo, mock_membership_repo, mock_user_repo, mock_audit_repo
):
    mock_membership_repo.get_user_and_membership.return_value = (None, None)

    with pytest.raises(NotFoundException):
        await _service(
            mock_org_repo, mock_membership_repo, mock_user_repo, mock_audit_repo
        ).invite_user(uuid7(), "nobody@test.com", "member", uuid7())


async def test_invite_already_member_raises(
    mock_org_repo, mock_membership_repo, mock_user_repo, mock_audit_repo
):
    """Test that a user cannot be invited to an org they are already in. 
    Because of the composite primary key (user_id, org_id), this single rule 
    intrinsically prevents both duplicate MEMBER roles and ADMIN->MEMBER downgrades."""
    user = User(id=uuid7(), email="existing@test.com", full_name="Existing", password="hashed")
    existing = Membership(user_id=user.id, org_id=uuid7(), role=Role.MEMBER)
    mock_membership_repo.get_user_and_membership.return_value = (user, existing)

    with pytest.raises(ConflictException):
        await _service(
            mock_org_repo, mock_membership_repo, mock_user_repo, mock_audit_repo
        ).invite_user(uuid7(), "existing@test.com", "member", uuid7())


async def test_invite_user_to_multiple_orgs_success(
    mock_org_repo, mock_membership_repo, mock_user_repo, mock_audit_repo
):
    """Test that a user can be successfully inserted/invited into multiple different organizations."""
    user = User(id=uuid7(), email="multi@test.com", full_name="Multi", password="hashed")
    org_id_1 = uuid7()
    org_id_2 = uuid7()
    
    # User is already logically in org 1 (not that the mock needs to know, but to illustrate)
    _ = Membership(user_id=user.id, org_id=org_id_1, role=Role.MEMBER)
    
    # Inviting to org 2: The repo returns the user, but NO existing membership for org 2
    mock_membership_repo.get_user_and_membership.return_value = (user, None)
    
    # The mock will echo back what gets created
    mock_membership_repo.create.return_value = Membership(
        user_id=user.id, org_id=org_id_2, role=Role.MEMBER
    )
    
    result = await _service(
        mock_org_repo, mock_membership_repo, mock_user_repo, mock_audit_repo
    ).invite_user(org_id_2, "multi@test.com", "member", uuid7())
    
    assert result.role == Role.MEMBER
    assert result.org_id == org_id_2
    mock_membership_repo.create.assert_called_once()

