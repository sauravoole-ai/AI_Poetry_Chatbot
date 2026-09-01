import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


class _FakeApp:
    def __init__(self, _name):
        self.logger = types.SimpleNamespace(error=lambda *_args, **_kwargs: None)

    def before_request(self, function):
        return function

    def route(self, *_args, **_kwargs):
        return lambda function: function


def _fake_modules():
    flask = types.ModuleType("flask")
    flask.Flask = _FakeApp
    flask.jsonify = lambda payload: payload
    flask.request = types.SimpleNamespace(get_json=lambda **_kwargs: {"topic": "Krishna"})
    flask.session = {}
    flask.render_template = lambda *_args, **_kwargs: None
    flask.send_file = lambda *_args, **_kwargs: None

    groq = types.ModuleType("groq")
    groq.Groq = lambda **_kwargs: types.SimpleNamespace(
        chat=types.SimpleNamespace(
            completions=types.SimpleNamespace(
                create=lambda **_create_kwargs: (_ for _ in ()).throw(
                    RuntimeError("internal provider detail")
                )
            )
        )
    )

    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda: None

    reportlab = types.ModuleType("reportlab")
    platypus = types.ModuleType("reportlab.platypus")
    platypus.SimpleDocTemplate = object
    platypus.Paragraph = object
    lib = types.ModuleType("reportlab.lib")
    styles = types.ModuleType("reportlab.lib.styles")
    styles.getSampleStyleSheet = lambda: {}

    return {
        "flask": flask,
        "groq": groq,
        "dotenv": dotenv,
        "reportlab": reportlab,
        "reportlab.platypus": platypus,
        "reportlab.lib": lib,
        "reportlab.lib.styles": styles,
    }


def _load_app(getenv):
    spec = importlib.util.spec_from_file_location("app_under_test", ROOT / "app.py")
    module = importlib.util.module_from_spec(spec)
    try:
        with patch.dict(sys.modules, _fake_modules()), patch.object(os, "getenv", side_effect=getenv):
            spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.pop("app_under_test", None)


class ProductionSecurityHygieneTests(unittest.TestCase):
    def test_startup_requires_a_configured_flask_secret(self):
        with self.assertRaisesRegex(RuntimeError, "FLASK_SECRET not set in environment variables"):
            _load_app(lambda name, default=None: None)

    def test_generation_failure_hides_internal_error_text(self):
        app_module = _load_app(
            lambda name, default=None: "configured" if name in {"FLASK_SECRET", "GROQ_API_KEY"} else default
        )

        payload, status = app_module.generate()

        self.assertEqual(status, 500)
        self.assertEqual(payload, {"error": "Unable to generate a poem right now. Please try again."})
        self.assertNotIn("internal provider detail", payload["error"])


if __name__ == "__main__":
    unittest.main()
