"""
Activity mode factory.

Creates activity mode objects based on activity type.
"""

from fastapi import HTTPException, status
from core.modes.story import StoryPractice
from core.modes.unlimited import UnlimitedPractice
from core.modes.choice_story import ChoiceStoryPractice
from models.session import Session as UserSession


def get_activity_object(session: UserSession):
    """
    Build the activity object based on the session's activity type.

    Args:
        session: User session containing activity information.

    Returns:
        BaseMode instance corresponding to the activity type.

    Raises:
        HTTPException: If session/activity not found or unsupported mode.
    """
    if session is None or session.activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session or activity not found",
        )

    activity_type = session.activity.activity_type

    if activity_type == "unlimited":
        return UnlimitedPractice()
    elif activity_type == "choice-story":
        return ChoiceStoryPractice()
    elif activity_type == "story":
        story_name = session.activity.activity_settings.get("story_name", "")
        return StoryPractice(story_name)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported mode: {activity_type}",
        )
