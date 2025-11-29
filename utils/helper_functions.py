from flask import session

from utils.constants import SessionInfo


def update_session_if_self(entity_obj, entity_type):
    if session.get(SessionInfo.USER_ID) == entity_obj.id and session.get(SessionInfo.USER_TYPE) == entity_type:
        session[SessionInfo.USER_NAME] = entity_obj.name
        session[SessionInfo.USER_EMAIL] = entity_obj.email
