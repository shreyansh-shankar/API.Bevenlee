# app/config/admins.py
# Hardcoded list of admin user_ids who can mark library items as admin picks
# and add items to the library without ownership checks being bypassed
# (ownership is still verified — admins just get the is_admin_pick flag)

ADMIN_USER_IDS: set[str] = {
    # Add your admin user_ids here
    # "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "45970419-918d-4968-a4d5-85e6e9af21f5",
}


def is_admin(user_id: str) -> bool:
    return user_id in ADMIN_USER_IDS