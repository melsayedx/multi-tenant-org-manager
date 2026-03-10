
from app.core.utils import uuid7
from app.models.item import Item
from app.models.membership import Role
from app.services.item import ItemService


def _service(mock_item_repo, mock_audit_repo) -> ItemService:
    return ItemService(mock_item_repo, mock_audit_repo)


async def test_create_item_returns_item(mock_item_repo, mock_audit_repo):
    org_id = uuid7()
    user_id = uuid7()
    details = {"name": "Widget", "price": 9.99}
    item = Item(id=uuid7(), org_id=org_id, created_by=user_id, item_details=details)
    mock_item_repo.create.return_value = item

    result = await _service(mock_item_repo, mock_audit_repo).create_item(
        org_id, user_id, details
    )

    assert result.item_details == details
    mock_item_repo.create.assert_called_once()
    mock_audit_repo.create.assert_called_once()


async def test_create_item_audit_action(mock_item_repo, mock_audit_repo):
    org_id = uuid7()
    user_id = uuid7()
    item = Item(id=uuid7(), org_id=org_id, created_by=user_id, item_details={})
    mock_item_repo.create.return_value = item

    await _service(mock_item_repo, mock_audit_repo).create_item(org_id, user_id, {})

    audit_call = mock_audit_repo.create.call_args[0][0]
    assert audit_call.action == "item_created"
    assert audit_call.entity_type == "item"


async def test_list_items_admin_sees_all(mock_item_repo, mock_audit_repo):
    org_id = uuid7()
    user_id = uuid7()
    items = [Item(id=uuid7(), org_id=org_id, created_by=user_id, item_details={})]
    mock_item_repo.get_by_org.return_value = (items, 1)

    result, total = await _service(mock_item_repo, mock_audit_repo).list_items(
        org_id, user_id, Role.ADMIN, 20, 0
    )

    assert total == 1
    mock_item_repo.get_by_org.assert_called_once_with(org_id, 20, 0, None)


async def test_list_items_member_sees_own_only(mock_item_repo, mock_audit_repo):
    org_id = uuid7()
    user_id = uuid7()
    mock_item_repo.get_by_org.return_value = ([], 0)

    await _service(mock_item_repo, mock_audit_repo).list_items(
        org_id, user_id, Role.MEMBER, 20, 0
    )

    mock_item_repo.get_by_org.assert_called_once_with(org_id, 20, 0, user_id)
