from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.model import User
from ..schemas.schema import UserUpdateRequest
from ..repositories.user import UserRepository
from api.modules.auth.services.service import hash_password

async def update_user_profile(
    user_to_update: User, 
    update_data: UserUpdateRequest, 
    db: AsyncSession
) -> User:
    """사용자 프로필 정보 업데이트 서비스"""
    user_repo = UserRepository(db)
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if field == "password":
            hashed_password = hash_password(value)
            setattr(user_to_update, field, hashed_password)
        else:
            setattr(user_to_update, field, value)
    user_to_update.updated_at = datetime.now()
    
    return await user_repo.update(user_to_update)
