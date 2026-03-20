from app.main import app


def test_app_exists() -> None:
    assert app.title == "MindFriend Agent"

