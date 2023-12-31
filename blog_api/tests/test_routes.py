import pytest
from app import app, db
from app.models import User, BlogPost, Comment


class TestRoutes:
    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        client = app.test_client()
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

    @pytest.fixture
    def test_user(self, client):
        data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "testpassword"
        }
        response = client.post('/register', json=data)
        assert response.status_code == 201
        access_token = self.get_access_token(client, data['username'], data['password'])
        return access_token

    @staticmethod
    def get_access_token(client, username, password):
        response = client.post('/login', json={"username": username, "password": password})
        assert response.status_code == 200
        return response.json['access_token']

    @pytest.fixture
    def post_data(self, client, test_user):
        data = {
            "title": "New Post",
            "content": "This is the content of the new post"
        }
        response = client.post('/posts', json=data, headers={"Authorization": f"Bearer {test_user}"})
        assert response.status_code == 201
        return response.json

    def test_register(self, client):
        data = {
            "username": "newuser1",
            "email": "newuser1@example.com",
            "password": "password"
        }
        response = client.post('/register', json=data)
        assert response.status_code == 201
        assert User.query.filter_by(username=data['username']).first() is not None

    def test_login(self, client, test_user):
        response = client.post('/login', json={"username": "testuser", "password": "testpassword"})
        assert response.status_code == 200
        assert 'access_token' in response.json

    def test_get_user(self, client, test_user):
        response = client.get('/user', headers={"Authorization": f"Bearer {test_user}"})
        assert response.status_code == 200
        assert response.json['username'] == "testuser"
        assert response.json['email'] == "testuser@example.com"

    def test_create_post(self, client, test_user, post_data):
        assert BlogPost.query.filter_by(title=post_data['data']['title']).first() is not None
        assert post_data['data']['title'] == "New Post"
        assert post_data['data']['content'] == "This is the content of the new post"

    def test_get_all_posts(self, client, test_user, post_data):
        response = client.get('/posts')
        assert response.status_code == 200
        assert len(response.json['posts']) == 1
        assert response.json['posts'][0]['title'] == post_data['data']['title']

    def test_get_post(self, client, test_user, post_data):
        response = client.get(f"/posts/{post_data['data']['id']}")
        assert response.status_code == 200
        assert response.json['title'] == post_data['data']['title']

    def test_update_post(self, client, test_user, post_data):
        new_data = {
            "title": "Updated Title",
            "content": "This is the updated content."
        }
        response = client.put(
            f"/posts/{post_data['data']['id']}",
            json=new_data,
            headers={"Authorization": f"Bearer {test_user}"}
        )
        assert response.status_code == 200
        assert response.json['message'] == "Blog post updated successfully!"

    def test_delete_post(self, client, test_user, post_data):
        response = client.delete(
            f"/posts/{post_data['data']['id']}",
            headers={"Authorization": f"Bearer {test_user}"}
        )
        assert response.status_code == 200
        assert response.json['message'] == "Blog post deleted successfully!"

    def test_add_comment(self, client, test_user, post_data):
        comment_data = {
            "content": "This is a new comment."
        }
        response = client.post(
            f"/posts/{post_data['data']['id']}/comments",
            json=comment_data,
            headers={"Authorization": f"Bearer {test_user}"}
        )
        assert response.status_code == 201
        assert response.json['message'] == "Comment added successfully!"

    def test_get_comments(self, client, test_user, post_data):
        response = client.get(f"/posts/{post_data['data']['id']}/comments")
        assert response.status_code == 200
        assert len(response.json['comments']) == 0  # No comments initially

        comment_data = {
            "content": "This is a new comment."
        }
        response = client.post(
            f"/posts/{post_data['data']['id']}/comments",
            json=comment_data,
            headers={"Authorization": f"Bearer {test_user}"}
        )
        assert response.status_code == 201

        response = client.get(f"/posts/{post_data['data']['id']}/comments")
        assert response.status_code == 200
        assert len(response.json['comments']) == 1
        assert response.json['comments'][0]['content'] == comment_data['content']

    def test_update_comment(self, client, test_user, post_data):
        comment_data = {
            "content": "This is a new comment."
        }
        response = client.post(
            f"/posts/{post_data['data']['id']}/comments",
            json=comment_data,
            headers={"Authorization": f"Bearer {test_user}"}
        )
        assert response.status_code == 201
        assert response.json['message'] == "Comment added successfully!"

        updated_comment_data = {
            "content": "Updated comment content."
        }
        response_put = client.put(
            f"/posts/{post_data['data']['id']}/comments/{response.json['data']['id']}",
            json=updated_comment_data,
            headers={"Authorization": f"Bearer {test_user}"}
        )
        assert response_put.status_code == 200
        assert response_put.json['message'] == "Comment updated successfully!"

    def test_delete_comment(self, client, test_user, post_data):
        comment_data = {
            "content": "This is a new comment."
        }
        response = client.post(
            f"/posts/{post_data['data']['id']}/comments",
            json=comment_data,
            headers={"Authorization": f"Bearer {test_user}"}
        )
        assert response.status_code == 201

        response = client.delete(
            f"/posts/{post_data['data']['id']}/comments/{response.json['data']['id']}",
            headers={"Authorization": f"Bearer {test_user}"}
        )
        assert response.status_code == 200
        assert response.json['message'] == "Comment deleted successfully!"
