from pathlib import Path
import sys
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))

from build_pack import process_texture


class ProcessTextureTest(unittest.TestCase):
    def test_writes_fixed_32px_rgba_png(self):
        with TemporaryDirectory() as temporary_directory:
            temporary_directory = Path(temporary_directory)
            source = temporary_directory / "crimson_oath.png"
            output_dir = temporary_directory / "art" / "fixed"
            Image.new("RGB", (64, 48), "red").save(source)

            def fake_run(command, **kwargs):
                fixed_path = Path(command[-1])
                fixed_path.parent.mkdir(parents=True, exist_ok=True)
                Image.new("RGB", (20, 40), "blue").save(fixed_path)

            with patch("build_pack.subprocess.run", fake_run):
                output = process_texture(source, temporary_directory / "pixel-art-fixer", output_dir)

            self.assertEqual(output, output_dir / "crimson_oath.png")
            with Image.open(output) as image:
                self.assertEqual(image.mode, "RGBA")
                self.assertEqual(image.size, (32, 32))


if __name__ == "__main__":
    unittest.main()
