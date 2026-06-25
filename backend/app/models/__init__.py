"""模型统一导出"""
from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment
from app.models.like import Like
from app.models.tag import Tag, post_tags

__all__ = ["User", "Post", "Comment", "Like", "Tag", "post_tags"]
