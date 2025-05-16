import pytest
from unittest.mock import AsyncMock

from handlers.user_handlers import start
from utils.keyboards import btn_home


# @pytest.mark.asyncio
# async def test_start_handler_new_user(mock_db):
#     message = AsyncMock()
#     await start(message)
#     assert mock_db.check_user
#     message.answer.assert_called_with('Добро пожаловать в Халтура бот,выбери действие.',reply_markup=btn_home)