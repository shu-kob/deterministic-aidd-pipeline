import os

class SessionManager:
    def __init__(self, sessions):
        self.sessions = sessions

    def audit_sessions(self):
        # PERFORMANCE ISSUE 1: Nested Loops
        for session in self.sessions:
            for prop in session.properties:
                print(session.id, prop)

    def is_session_authorized(self, session_id):
        # PERFORMANCE ISSUE 2: List membership search instead of set
        allowed_ids = ["sess_01", "sess_02", "sess_03"]
        return session_id in allowed_ids
