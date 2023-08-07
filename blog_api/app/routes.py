from flask import Blueprint, jsonify, request, Response
from datetime import timedelta
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import app, db, bcrypt
from .models import User, BlogPost, Comment

# Create a Blueprint
bp = Blueprint('routes', __name__)


# -------------------------------------------------------------------- #
# User Management:
# -------------------------------------------------------------------- #
@bp.route('/register', methods=['POST'])
def register() -> tuple[Response, int]:
    """User Registration.
        curl -X POST -H "Content-Type: application/json" -d '{
        "username":"newuser",
        "email":"newuser@example.com",
        "password":"password"
        }' http://0.0.0.0:5002/register

    :return:
        {"message": "User registered successfully!"}
    """
    data = request.get_json()
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], email=data['email'], password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully!'}), 201


@bp.route('/login', methods=['POST'])
def login() -> tuple[Response, int]:
    """User Authentication.
        curl -X POST -H "Content-Type: application/json" -d '{
        "username":"newuser",
        "password":"password"
        }' http://0.0.0.0:5002/login

    :return:
        {"access_token": "<your_access_token>"}
    """
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and bcrypt.check_password_hash(user.password_hash, data['password']):
        access_token = create_access_token(identity=user.id, expires_delta=timedelta(days=1))
        return jsonify({'access_token': access_token}), 200
    return jsonify({'message': 'Invalid username or password'}), 401


@bp.route('/user', methods=['GET'])
@jwt_required()
def get_user() -> tuple[Response, int]:
    """Protected route to retrieve user details.
        curl -X GET -H "Authorization: Bearer <your_access_token>" http://0.0.0.0:5002/user

    :return:
        {
            "created_at":"Mon, 07 Aug 2023 07:30:02 GMT",
            "email":"newuser@example.com",
            "id":1,
            "username":"newuser"
        }
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'created_at': user.created_at
    }), 200


# -------------------------------------------------------------------- #
# Blog Post Management:
# -------------------------------------------------------------------- #
@bp.route('/posts', methods=['POST'])
@jwt_required()
def create_post() -> tuple[Response, int]:
    """Create a new blog post.
        curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer <your_access_token>" -d '{
        "title":"New Post",
        "content":"This is the content of the new post"
        }' http://0.0.0.0:5002/posts

    :return:
        {"message": "Blog post created successfully!"}
    """
    data = request.get_json()
    new_post = BlogPost(title=data['title'], content=data['content'], author_id=get_jwt_identity())
    db.session.add(new_post)
    db.session.commit()
    return jsonify({'message': 'Blog post created successfully!'}), 201


@bp.route('/posts', methods=['GET'])
def get_all_posts() -> tuple[Response, int]:
    """Retrieve a list of all blog posts.
        curl -X GET http://0.0.0.0:5002/posts

    :return:
        {
            "posts":
                [
                    {
                        "author_id":1,
                        "content":"This is the content of the new post",
                        "created_at":"Mon, 07 Aug 2023 07:32:13 GMT",
                        "id":1,
                        "title":"New Post"
                    },
                ]
            }
    """
    posts = BlogPost.query.all()
    posts_list = []
    for post in posts:
        posts_list.append({
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'author_id': post.author_id,
            'created_at': post.created_at
        })
    return jsonify({'posts': posts_list}), 200


@bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id: int) -> tuple[Response, int]:
    """Retrieve details of a specific blog post.
    curl -X GET http://0.0.0.0:5002/posts/<post_id>

    :param post_id:
    :return:
        {
            "author_id":1,
            "content":"This is the content of the new post",
            "created_at":"Mon, 07 Aug 2023 07:32:13 GMT",
            "id":1,"title":"New Post"
        }
    """
    post = BlogPost.query.get_or_404(post_id)
    return jsonify({
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'author_id': post.author_id,
        'created_at': post.created_at
    }), 200


@bp.route('/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id: int) -> tuple[Response, int]:
    """Update a blog post.
        curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer <your_access_token>" -d '{
        "title":"Updated Title",
        "content":"This is the updated content."
        }' http://0.0.0.0:5002/posts/<post_id>

    :param post_id:
    :return:
        {"message": "Blog post updated successfully!"}
    """
    post = BlogPost.query.get_or_404(post_id)
    data = request.get_json()
    post.title = data['title']
    post.content = data['content']
    db.session.commit()
    return jsonify({'message': 'Blog post updated successfully!'}), 200


@bp.route('/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id: int) -> tuple[Response, int]:
    """Delete a blog post.
        curl -X DELETE -H "Authorization: Bearer <your_access_token>" http://0.0.0.0:5002/posts/<post_id>

    :param post_id:
    :return:
        {"message": "Blog post deleted successfully!"}
    """
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return jsonify({'message': 'Blog post deleted successfully!'}), 200


# -------------------------------------------------------------------- #
# Comment Management:
# -------------------------------------------------------------------- #
@bp.route('/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(post_id: int) -> tuple[Response, int]:
    """Add a comment to a blog post.
        curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer <your_access_token>" -d '{
        "content":"This is a new comment."
        }' http://0.0.0.0:5002/posts/<post_id>/comments

    :param post_id:
    :return:
        {"message": "Comment added successfully!"}
    """
    data = request.get_json()
    new_comment = Comment(content=data['content'], author_id=get_jwt_identity(), post_id=post_id)
    db.session.add(new_comment)
    db.session.commit()
    return jsonify({'message': 'Comment added successfully!'}), 201


@bp.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id: int) -> tuple[Response, int]:
    """Retrieve all comments for a specific blog post.
        curl -X GET http://0.0.0.0:5002/posts/<post_id>/comments

    :param post_id:
    :return:
        {"comments":
            [
                {
                    "author_id":1,
                    "content":"This is a new comment.",
                    "created_at":"Mon, 07 Aug 2023 07:37:01 GMT",
                    "id":1
                },
            ]
        }
    """
    comments = Comment.query.filter_by(post_id=post_id).all()
    comments_list = []
    for comment in comments:
        comments_list.append({
            'id': comment.id,
            'content': comment.content,
            'author_id': comment.author_id,
            'created_at': comment.created_at
        })
    return jsonify({'comments': comments_list}), 200


@bp.route('/posts/<int:post_id>/comments/<int:comment_id>', methods=['PUT'])
@jwt_required()
def update_comment(post_id: int, comment_id: int) -> tuple[Response, int]:
    """Update a comment.
        curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer <your_access_token>" -d '{
        "content":"Updated comment content."
        }' http://0.0.0.0:5002/posts/<post_id>/comments/<comment_id>

    :param post_id:
    :param comment_id:
    :return:
        {"message": "Comment updated successfully!"}
    """
    comment = Comment.query.get_or_404(comment_id)
    if comment.post_id != post_id:
        return jsonify({'message': 'Comment does not belong to the specified post'}), 400
    data = request.get_json()
    comment.content = data['content']
    db.session.commit()
    return jsonify({'message': 'Comment updated successfully!'}), 200


@bp.route('/posts/<int:post_id>/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(post_id: int, comment_id: int) -> tuple[Response, int]:
    """Delete a comment.
        curl -X DELETE -H "Authorization: Bearer <your_access_token>"
        http://0.0.0.0:5002/posts/<post_id>/comments/<comment_id>

    :param post_id:
    :param comment_id:
    :return:
        {"message": "Comment deleted successfully!"}
    """
    comment = Comment.query.get_or_404(comment_id)
    if comment.post_id != post_id:
        return jsonify({'message': 'Comment does not belong to the specified post'}), 400
    db.session.delete(comment)
    db.session.commit()
    return jsonify({'message': 'Comment deleted successfully!'}), 200


# Register the Blueprint
app.register_blueprint(bp)
