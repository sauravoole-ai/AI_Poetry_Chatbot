import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class GenerationRegressionTests(unittest.TestCase):
    def test_gpt_oss_uses_a_reasoning_appropriate_completion_budget(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")

        self.assertIn('max_completion_tokens=1024', source)
        self.assertNotIn('max_tokens=500', source)

    @unittest.skipUnless(shutil.which("node"), "Node.js is required for the browser-flow mock")
    def test_failed_generation_restores_the_button_and_shows_an_error(self):
        html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
        script = re.findall(r"<script>([\s\S]*?)</script>", html)[0]
        harness = f"""
const topic = {{ value: 'Krishna', addEventListener() {{}} }};
const button = {{ innerText: '✨ Generate Poem', disabled: false }};
const poem = {{ innerHTML: '', appendChild() {{}} }};
global.document = {{
  getElementById(id) {{ return {{ topic, generateBtn: button, poem }}[id]; }},
  createElement() {{ return {{ className: '', innerText: '' }}; }}
}};
global.fetch = async () => ({{
  ok: false,
  status: 500,
  json: async () => ({{ error: 'Upstream unavailable' }})
}});
{script}
generatePoem().then(() => {{
  if (button.disabled || button.innerText !== '✨ Generate Poem') process.exit(1);
  if (!poem.innerHTML.includes('Unable to generate a poem')) process.exit(2);
}}).catch(() => process.exit(3));
"""

        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as test_file:
            test_file.write(harness)
            test_path = Path(test_file.name)
        try:
            completed = subprocess.run(["node", str(test_path)], capture_output=True, text=True)
        finally:
            test_path.unlink(missing_ok=True)

        self.assertEqual(completed.returncode, 0, completed.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node.js is required for the browser-flow mock")
    def test_successful_generation_restores_the_button(self):
        html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
        script = re.findall(r"<script>([\s\S]*?)</script>", html)[0]
        harness = f"""
const topic = {{ value: 'Krishna', addEventListener() {{}} }};
const button = {{ innerText: 'âœ¨ Generate Poem', disabled: false }};
const poem = {{ innerHTML: '', appendChild() {{}} }};
global.document = {{
  getElementById(id) {{ return {{ topic, generateBtn: button, poem }}[id]; }},
  createElement() {{ return {{ className: '', innerText: '' }}; }}
}};
global.fetch = async () => ({{
  ok: true,
  status: 200,
  json: async () => ({{ poem: 'Line one\\nLine two' }})
}});
{script}
generatePoem().then(() => {{
  if (button.disabled || !button.innerText.includes('Generate Poem')) process.exit(1);
}}).catch(() => process.exit(2));
"""

        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as test_file:
            test_file.write(harness)
            test_path = Path(test_file.name)
        try:
            completed = subprocess.run(["node", str(test_path)], capture_output=True, text=True)
        finally:
            test_path.unlink(missing_ok=True)

        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
