from app.core.supabase import supabase
from app.config.admin import is_admin

class NotOwnerError(Exception):
    pass


class SourceNotFoundError(Exception):
    pass


def add_library_item(
    user_id: str,
    item_type: str,          # "course" | "roadmap"
    source_id: str,
    whiteboards: bool = False,
) -> dict:
    """
    Add a course or roadmap to the library.
    - Verifies the source exists and belongs to the user.
    - Marks is_admin_pick=True if user_id is in ADMIN_USER_IDS.
    - Denormalises title + description for fast list queries.
    """

    admin_pick = is_admin(user_id)

    if item_type == "course":
        source = (
            supabase.table("courses")
            .select("course_id, title, purpose")
            .eq("course_id", source_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        ).data

        if not source:
            raise SourceNotFoundError("Course not found or not owned by you")

        title = source["title"]
        description = source.get("purpose")  # courses use `purpose` as description

    elif item_type == "roadmap":
        source = (
            supabase.table("roadmaps")
            .select("roadmap_id, title, description")
            .eq("roadmap_id", source_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        ).data

        if not source:
            raise SourceNotFoundError("Roadmap not found or not owned by you")

        title = source["title"]
        description = source.get("description")

    else:
        raise ValueError("item_type must be 'course' or 'roadmap'")

    result = (
        supabase.table("library_items")
        .insert({
            "item_type": item_type,
            "source_id": source_id,
            "added_by": user_id,
            "is_admin_pick": admin_pick,
            "whiteboards": whiteboards,
            "title": title,
            "description": description,
        })
        .execute()
    )

    return result.data[0]