from aiogram.fsm.state import State,StatesGroup


class NewPost(StatesGroup):
    company_name = State()
    place = State()
    data_time = State()
    job_title = State()
    work_schedule = State()
    task = State()
    payment = State()
    contacts = State()
    awaiting_finished_post = State()
    pending_confirmation = State()

class AdminState(StatesGroup):
    waiting_for_broadcast_ms = State()
    waiting_action = State()
    waiting_for_reason = State()


class DeletePostState(StatesGroup):
    waiting_post_id = State()

