from tools.social_tools import (
    get_platform_guidelines,
    save_post,
    list_posts,
    generate_content_calendar,
    get_hashtag_suggestions,
)


def test_get_platform_guidelines_twitter():
    result = get_platform_guidelines.invoke({"platform": "twitter"})
    assert "TWITTER" in result
    assert "280" in result


def test_get_platform_guidelines_unknown():
    result = get_platform_guidelines.invoke({"platform": "tiktok"})
    assert "Unknown platform" in result


def test_save_and_list_posts():
    save_post.invoke(
        {
            "platform": "linkedin",
            "content": "Summer sale starts today!",
            "hashtags": "sale,marketing",
            "scheduled_date": "2026-07-10",
        }
    )

    listed = list_posts.invoke({"platform": "linkedin", "status": "scheduled"})
    assert "Summer sale starts today!" in listed
    assert "#sale" in listed


def test_generate_content_calendar():
    result = generate_content_calendar.invoke(
        {
            "topics": "launch, tips",
            "platforms": "twitter, linkedin",
            "weeks": 1,
        }
    )
    assert "Content Calendar" in result
    assert "Week 1" in result
    assert "TWITTER" in result or "LINKEDIN" in result


def test_get_hashtag_suggestions():
    result = get_hashtag_suggestions.invoke(
        {"topic": "product launch", "platform": "twitter"}
    )
    assert "#productlaunch" in result or "#marketing" in result
