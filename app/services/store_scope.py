import uuid

from fastapi import HTTPException, status

from app.services.store import StoreService


class StoreScopedService:
    def _resolve_store_id(self, *, current_user=None, store_id: uuid.UUID | None = None) -> uuid.UUID:
        if store_id:
            return store_id
        return self._get_store_or_404(current_user).id

    def _get_store_or_404(self, current_user):
        if not current_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Store scope is required")

        return StoreService(self.db).get_by_current_user_or_404(current_user)

    def _assert_store_scope(self, entity, scope_store_id: uuid.UUID, not_found_detail: str) -> None:
        if entity.store_id != scope_store_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_detail)
