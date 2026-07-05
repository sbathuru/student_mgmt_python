"""Flask application entrypoint for the Student Management API."""

import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint

from .student_service import StudentService, ValidationError


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
    app.secret_key = "dev-secret-key-change-in-production"
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
        deleted = service.delete_student(student_id)
        if deleted:
            return jsonify({"message": "Student deleted"}), 200
        return jsonify({"error": f"No student found with ID {student_id}."}), 404

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
