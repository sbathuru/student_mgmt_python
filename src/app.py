"""Flask application entrypoint for the Student Management API."""

import os

from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint

from .student_service import StudentService, ValidationError
from .auth import register_user, authenticate_user, verify_token, USER_STORE


class LazyService:
    """Lazily creates the real service once the Oracle repository is available."""

    def __init__(self, repository_factory):
        self._repository_factory = repository_factory
        self._service = None

    def _get_service(self):
        if self._service is None:
            self._service = StudentService(self._repository_factory())
        return self._service

    def __getattr__(self, name):
        return getattr(self._get_service(), name)


def create_repository():
    """Create the Oracle repository implementation."""
    if not os.getenv("ORACLE_USER") or not os.getenv("ORACLE_PASSWORD") or not os.getenv("ORACLE_DSN"):
        raise ValueError(
            "Oracle configuration is required. Set ORACLE_USER, ORACLE_PASSWORD, and ORACLE_DSN."
        )

    from .oracle_db import OracleStudentDB

    return OracleStudentDB()


def create_app(service=None):
    app = Flask(__name__, static_folder="static")
    # Use config SECRET_KEY for JWT signing. This should be overridden in prod.
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    swagger_url = "/swagger"
    api_url = "/static/swagger.json"
    swaggerui_blueprint = get_swaggerui_blueprint(
        swagger_url,
        api_url,
        config={"app_name": "Student Management API"},
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=swagger_url)

    if service is None:
        service = LazyService(create_repository)

    def _get_token_from_header():
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth.split(" ", 1)[1].strip()
        return None

    def require_auth():
        token = _get_token_from_header()
        if not token:
            return None
        payload = verify_token(token)
        return payload

    @app.route("/api/students", methods=["GET"])
    def api_list_students():
        students = service.list_students()
        return jsonify([student.to_dict() for student in students]), 200

    @app.route("/api/students/<int:student_id>", methods=["GET"])
    def api_get_student(student_id):
        student = service.get_student(student_id)
        if student is None:
            return jsonify({"error": f"No student found with ID {student_id}."}), 404
        return jsonify(student.to_dict()), 200

    @app.route("/api/students", methods=["POST"])
    def api_add_student():
        # require authentication for write operations
        if not require_auth():
            return jsonify({"error": "Authentication required."}), 401

        payload = request.get_json(silent=True) or {}
        if not isinstance(payload, dict):
            return jsonify({"error": "Request body must be a JSON object."}), 400

        try:
            student = service.add_student(
                name=payload.get("name", ""),
                age=payload.get("age", ""),
                email=payload.get("email", ""),
                course=payload.get("course", ""),
            )
            return jsonify(student.to_dict()), 201
        except ValidationError as e:
            return jsonify({"error": str(e)}), 400

    @app.route("/api/students/<int:student_id>", methods=["PUT"])
    def api_update_student(student_id):
        if not require_auth():
            return jsonify({"error": "Authentication required."}), 401

        payload = request.get_json(silent=True) or {}
        if not isinstance(payload, dict):
            return jsonify({"error": "Request body must be a JSON object."}), 400

        try:
            student = service.update_student(
                student_id,
                name=payload.get("name"),
                age=payload.get("age"),
                email=payload.get("email"),
                course=payload.get("course"),
            )
            return jsonify(student.to_dict()), 200
        except ValidationError as e:
            return jsonify({"error": str(e)}), 400

    @app.route("/api/students/<int:student_id>", methods=["DELETE"])
    def api_delete_student(student_id):
        if not require_auth():
            return jsonify({"error": "Authentication required."}), 401

        deleted = service.delete_student(student_id)
        if deleted:
            return jsonify({"message": "Student deleted"}), 200
        return jsonify({"error": f"No student found with ID {student_id}."}), 404


    # Authentication endpoints
    @app.route("/api/auth/register", methods=["POST"])
    def api_register():
        body = request.get_json(silent=True) or {}
        email = body.get("email")
        password = body.get("password")
        try:
            user = register_user(email, password)
            return jsonify({"message": "User registered", "user": user}), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400


    @app.route("/api/auth/login", methods=["POST"])
    def api_login():
        body = request.get_json(silent=True) or {}
        email = body.get("email")
        password = body.get("password")
        auth = authenticate_user(email, password)
        if auth is None:
            return jsonify({"error": "Invalid credentials"}), 401
        return jsonify(auth), 200


    # User management endpoints
    @app.route("/api/users", methods=["GET"])
    def api_list_users():
        if not require_auth():
            return jsonify({"error": "Authentication required."}), 401
        users = []
        try:
            raw = USER_STORE.list_users()
            for u in raw:
                users.append({"id": u.id, "email": u.email})
        except Exception:
            return jsonify({"error": "User store not available."}), 500
        return jsonify(users), 200

    @app.route("/api/users/<int:user_id>", methods=["GET"])
    def api_get_user(user_id):
        payload = require_auth()
        if not payload:
            return jsonify({"error": "Authentication required."}), 401
        # allow users to fetch their own profile
        if payload.get("sub") != user_id:
            return jsonify({"error": "Forbidden."}), 403
        user = USER_STORE.get_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found."}), 404
        return jsonify({"id": user.id, "email": user.email}), 200

    @app.route("/api/users/<int:user_id>", methods=["PUT"])
    def api_update_user(user_id):
        payload = require_auth()
        if not payload:
            return jsonify({"error": "Authentication required."}), 401
        if payload.get("sub") != user_id:
            return jsonify({"error": "Forbidden."}), 403
        body = request.get_json(silent=True) or {}
        new_password = body.get("password")
        if not new_password:
            return jsonify({"error": "Password is required to update."}), 400
        from passlib.hash import bcrypt

        pw_hash = bcrypt.hash(new_password)
        try:
            updated = USER_STORE.update_password(user_id, pw_hash)
        except Exception:
            return jsonify({"error": "Unable to update password."}), 500
        if not updated:
            return jsonify({"error": "User not found."}), 404
        return jsonify({"id": updated.id, "email": updated.email}), 200

    @app.route("/api/users/<int:user_id>", methods=["DELETE"])
    def api_delete_user(user_id):
        payload = require_auth()
        if not payload:
            return jsonify({"error": "Authentication required."}), 401
        if payload.get("sub") != user_id:
            return jsonify({"error": "Forbidden."}), 403
        try:
            deleted = USER_STORE.delete_user(user_id)
        except Exception:
            return jsonify({"error": "Unable to delete user."}), 500
        if deleted:
            return jsonify({"message": "User deleted."}), 200
        return jsonify({"error": "User not found."}), 404

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
