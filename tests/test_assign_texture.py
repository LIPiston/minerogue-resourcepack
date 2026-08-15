import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))

from assign_texture import find_entry, load_entries, run, target_paths
from build_pack import process_texture

CONTENT_FILES = {
    "content/weapons/crimson_oath.yml": "id: crimson_oath\nitem: minecraft:iron_sword\n",
    "content/armor/explosive_helmet.yml": "id: explosive_helmet\nmaterial: minecraft:copper_helmet\n",
    "content/items/burger.yml": "id: burger\nitem: minecraft:player_head\n",
}


def make_root(directory: str) -> Path:
    root = Path(directory)
    for relative, text in CONTENT_FILES.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def fake_fixer_run(command, **kwargs):
    fixed_path = Path(command[-1])
    fixed_path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (20, 40), "blue").save(fixed_path)


class LoadEntriesTest(unittest.TestCase):
    def test_collects_weapons_armor_and_items(self):
        with TemporaryDirectory() as directory:
            root = make_root(directory)
            entries = load_entries(root)
            by_id = {entry.id: entry for entry in entries}
            self.assertEqual(by_id["crimson_oath"].material, "iron_sword")
            self.assertEqual(by_id["crimson_oath"].category, "武器")
            self.assertEqual(by_id["explosive_helmet"].material, "copper_helmet")
            self.assertEqual(by_id["explosive_helmet"].category, "装备")
            self.assertEqual(by_id["burger"].material, "player_head")
            self.assertEqual(by_id["burger"].category, "物品")


class FindEntryTest(unittest.TestCase):
    def test_selects_by_number(self):
        with TemporaryDirectory() as directory:
            entries = load_entries(make_root(directory))
            selected = find_entry(entries, "2")
            self.assertEqual(selected.id, "explosive_helmet")

    def test_selects_by_dragged_yml_path(self):
        with TemporaryDirectory() as directory:
            root = make_root(directory)
            entries = load_entries(root)
            path = root / "content" / "items" / "burger.yml"
            selected = find_entry(entries, f'"{path}"')
            self.assertEqual(selected.id, "burger")

    def test_rejects_invalid_selection(self):
        with TemporaryDirectory() as directory:
            entries = load_entries(make_root(directory))
            with self.assertRaises(ValueError):
                find_entry(entries, "99")


class TargetPathsTest(unittest.TestCase):
    def test_maps_entry_to_pack_paths(self):
        with TemporaryDirectory() as directory:
            pack_dir = Path(directory) / "pack"
            entries = load_entries(make_root(directory))
            targets = target_paths(pack_dir, entries[0])
            self.assertEqual(
                targets.texture,
                pack_dir / "assets" / "minerogue" / "textures" / "item" / "crimson_oath.png",
            )
            self.assertEqual(
                targets.item_json,
                pack_dir / "assets" / "minerogue" / "items" / "crimson_oath.json",
            )
            self.assertEqual(
                targets.model_json,
                pack_dir / "assets" / "minerogue" / "models" / "item" / "crimson_oath.json",
            )


class ProcessTextureNameTest(unittest.TestCase):
    def test_writes_fixed_texture_under_given_name(self):
        with TemporaryDirectory() as directory:
            directory = Path(directory)
            source = directory / "drawn.png"
            output_dir = directory / "out"
            Image.new("RGB", (64, 48), "red").save(source)
            with patch("build_pack.subprocess.run", fake_fixer_run):
                output = process_texture(source, directory / "pixel-art-fixer", output_dir, name="crimson_oath")
            self.assertEqual(output, output_dir / "crimson_oath.png")
            with Image.open(output) as image:
                self.assertEqual(image.size, (32, 32))
                self.assertEqual(image.mode, "RGBA")


class RunWizardTest(unittest.TestCase):
    def _inputs(self, *values):
        iterator = iter(values)

        def read_input(prompt):
            return next(iterator)

        return read_input

    def test_writes_texture_and_json_for_selected_entry(self):
        with TemporaryDirectory() as directory:
            root = make_root(directory)
            pack_dir = root / "resourcepack" / "pack"
            source = root / "drawing.png"
            Image.new("RGB", (64, 48), "red").save(source)
            with patch("build_pack.subprocess.run", fake_fixer_run):
                result = run(root, pack_dir, self._inputs("1", str(source)), print_fn=lambda *_: None)
            self.assertEqual(result, 0)
            texture = pack_dir / "assets" / "minerogue" / "textures" / "item" / "crimson_oath.png"
            self.assertTrue(texture.is_file())
            with Image.open(texture) as image:
                self.assertEqual(image.size, (32, 32))
            item_json = pack_dir / "assets" / "minerogue" / "items" / "crimson_oath.json"
            model_json = pack_dir / "assets" / "minerogue" / "models" / "item" / "crimson_oath.json"
            self.assertEqual(json.loads(item_json.read_text(encoding="utf-8")), {
                "model": {"type": "minecraft:model", "model": "minerogue:item/crimson_oath"}
            })
            self.assertEqual(json.loads(model_json.read_text(encoding="utf-8")), {
                "parent": "minecraft:item/iron_sword",
                "textures": {"layer0": "minerogue:item/crimson_oath"},
            })

    def test_asks_before_overwriting_existing_texture(self):
        with TemporaryDirectory() as directory:
            root = make_root(directory)
            pack_dir = root / "resourcepack" / "pack"
            texture = pack_dir / "assets" / "minerogue" / "textures" / "item" / "crimson_oath.png"
            texture.parent.mkdir(parents=True, exist_ok=True)
            texture.write_bytes(b"old texture")
            source = root / "drawing.png"
            Image.new("RGB", (64, 48), "red").save(source)
            with patch("build_pack.subprocess.run", fake_fixer_run):
                result = run(root, pack_dir, self._inputs("1", str(source), "n"), print_fn=lambda *_: None)
            self.assertEqual(result, 1)
            self.assertEqual(texture.read_bytes(), b"old texture")
            self.assertFalse((pack_dir / "assets" / "minerogue" / "items" / "crimson_oath.json").exists())

    def test_rejects_invalid_image_path(self):
        with TemporaryDirectory() as directory:
            root = make_root(directory)
            pack_dir = root / "resourcepack" / "pack"
            missing = root / "missing.png"
            with patch("build_pack.subprocess.run", fake_fixer_run):
                result = run(root, pack_dir, self._inputs("1", str(missing), "2", "3"), print_fn=lambda *_: None)
            self.assertEqual(result, 1)
            self.assertFalse((pack_dir / "assets" / "minerogue" / "items" / "crimson_oath.json").exists())


if __name__ == "__main__":
    unittest.main()
