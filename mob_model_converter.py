"""
╔══════════════════════════════════════════════════════════════╗
║         mob_model_converter.py                              ║
║         Tool chuyên biệt: Convert Model Quái               ║
║         Hỗ trợ: ModelEngine / EliteCreatures / Java Mobs   ║
║                                                              ║
║  ► HOÀN TOÀN ĐỘC LẬP với ia_to_geyser_converter.py        ║
║  ► Chỉ xử lý models/entity và textures/entity              ║
║  ► Dễ sửa lỗi, dễ mở rộng                                  ║
╚══════════════════════════════════════════════════════════════╝

Cách dùng CLI:
  python mob_model_converter.py <input.zip> [output_dir]
  python mob_model_converter.py pack.zip ./output_mobs
"""

import os
import json
import shutil
import zipfile
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime


# ══════════════════════════════════════════════════════════════
#  CẤU HÌNH - Sửa tại đây khi cần
# ══════════════════════════════════════════════════════════════

# Bedrock texture size mặc định
DEFAULT_TEX_WIDTH  = 64
DEFAULT_TEX_HEIGHT = 64

# Visible bounds mặc định cho mob
DEFAULT_BOUNDS = {
    "width":  2.0,
    "height": 2.0,
    "offset": [0, 1.0, 0]
}

# Thứ tự mặt UV Java
UV_FACE_ORDER = ["north", "south", "east", "west", "up", "down"]


# ══════════════════════════════════════════════════════════════
#  LỚP 1: JavaGeometryConverter
#  Chuyển đổi từng phần (part/bone) từ Java sang Bedrock
# ══════════════════════════════════════════════════════════════
class JavaGeometryConverter:
    """
    Xử lý chuyển đổi geometry:
      Java element (cuboid) → Bedrock cube
      Java part (nhiều elements) → Bedrock bone
      Tất cả parts của mob → Bedrock geometry file
    """

    @staticmethod
    def convert_mob_geometry(mob_name: str, parts: Dict[str, dict]) -> Optional[dict]:
        """
        Gộp tất cả part của một mob → một file geometry Bedrock.

        Args:
            mob_name: Tên mob, VD: "dwarf_cleric"
            parts: { tên_part: nội_dung_java_model }

        Returns:
            dict Bedrock geometry, None nếu không có gì để convert.
        """
        bones = []

        for part_name, java_model in parts.items():
            elements = java_model.get("elements", [])
            if not elements:
                continue  # Part rỗng, bỏ qua

            cubes = []
            for elem in elements:
                cube = JavaGeometryConverter._convert_element(elem)
                if cube:
                    cubes.append(cube)

            if cubes:
                bones.append({
                    "name":   part_name,
                    "parent": "root",
                    "pivot":  [0.0, 0.0, 0.0],
                    "cubes":  cubes
                })

        if not bones:
            return None  # Mob không có geometry hợp lệ

        # Thêm bone gốc
        bones.insert(0, {"name": "root", "pivot": [0, 0, 0]})

        return {
            "format_version": "1.12.0",
            "minecraft:geometry": [{
                "description": {
                    "identifier":             f"geometry.{mob_name}",
                    "texture_width":          DEFAULT_TEX_WIDTH,
                    "texture_height":         DEFAULT_TEX_HEIGHT,
                    "visible_bounds_width":   DEFAULT_BOUNDS["width"],
                    "visible_bounds_height":  DEFAULT_BOUNDS["height"],
                    "visible_bounds_offset":  DEFAULT_BOUNDS["offset"]
                },
                "bones": bones
            }]
        }

    @staticmethod
    def _convert_element(elem: dict) -> Optional[dict]:
        """
        Chuyển một element Java → Bedrock cube.

        Hệ tọa độ:
          Java:   X[0→16], Y[0→16], Z[0→16], tâm ở (8,8,8)
          Bedrock: X[-8→8], Y[0→16], Z[-8→8]
        """
        frm = elem.get("from", [0, 0, 0])
        to  = elem.get("to",   [16, 16, 16])

        size = [
            round(to[0] - frm[0], 4),
            round(to[1] - frm[1], 4),
            round(to[2] - frm[2], 4),
        ]
        # Bỏ qua cube rỗng
        if size[0] == 0 and size[1] == 0 and size[2] == 0:
            return None

        cube = {
            "origin": [
                round(frm[0] - 8.0, 4),
                round(frm[1],        4),
                round(frm[2] - 8.0, 4),
            ],
            "size": size,
            "uv":   JavaGeometryConverter._get_uv(elem),
        }

        # Xử lý rotation
        rot = elem.get("rotation")
        if rot:
            orig = rot.get("origin", [8, 8, 8])
            cube["pivot"] = [
                round(orig[0] - 8.0, 4),
                round(orig[1],        4),
                round(orig[2] - 8.0, 4),
            ]
            cube["rotation"] = JavaGeometryConverter._convert_rotation(
                rot.get("axis",  "y"),
                rot.get("angle", 0.0)
            )

        return cube

    @staticmethod
    def _get_uv(elem: dict) -> list:
        """Lấy UV [u, v] từ mặt đầu tiên có trong element."""
        faces = elem.get("faces", {})
        for face in UV_FACE_ORDER:
            if face in faces:
                uv = faces[face].get("uv", [0, 0, 16, 16])
                return [round(uv[0], 2), round(uv[1], 2)]
        return [0, 0]

    @staticmethod
    def _convert_rotation(axis: str, angle: float) -> list:
        """
        Java: xoay quanh 1 trục.
        Bedrock: [rx, ry, rz] Euler degrees.
        Bedrock đảo chiều quay nên nhân -1.
        """
        a = round(-float(angle), 4)
        if axis == "x": return [a,   0.0, 0.0]
        if axis == "y": return [0.0, a,   0.0]
        if axis == "z": return [0.0, 0.0, a  ]
        return [0.0, 0.0, 0.0]


# ══════════════════════════════════════════════════════════════
#  LỚP 2: BedrockMobBuilder
#  Tạo entity definition + render controller cho Bedrock
# ══════════════════════════════════════════════════════════════
class BedrockMobBuilder:
    """
    Tạo các file JSON Bedrock cần thiết cho một mob:
      - entity/<mob>.entity.json
      - render_controllers/<mob>.render_controllers.json
    """

    @staticmethod
    def build_entity(mob_name: str) -> dict:
        """
        Tạo client entity definition.
        File này nói với Bedrock: "mob này dùng geometry, texture, render controller nào".
        """
        return {
            "format_version": "1.10.0",
            "minecraft:client_entity": {
                "description": {
                    "identifier":          f"modelengine:{mob_name}",
                    "materials":           {"default": "entity_alphatest"},
                    "textures":            {"default": f"textures/entity/{mob_name}"},
                    "geometry":            {"default": f"geometry.{mob_name}"},
                    "render_controllers":  [f"controller.render.{mob_name}"],
                    "spawn_egg": {
                        "base_color":    "#3A5F3A",
                        "overlay_color": "#A8D5A2"
                    }
                }
            }
        }

    @staticmethod
    def build_render_controller(mob_name: str) -> dict:
        """Tạo render controller cho mob."""
        return {
            "format_version": "1.8.0",
            "render_controllers": {
                f"controller.render.{mob_name}": {
                    "geometry":  "Geometry.default",
                    "materials": [{"*": "Material.default"}],
                    "textures":  ["Texture.default"]
                }
            }
        }


# ══════════════════════════════════════════════════════════════
#  LỚP CHÍNH: MobModelConverter
#  Điều phối toàn bộ quá trình
# ══════════════════════════════════════════════════════════════
class MobModelConverter:
    """
    Convert tất cả model quái từ một pack ZIP sang định dạng Bedrock.

    Nhận diện được:
      - ModelEngine pack (assets/modelengine/models/<mob>/<part>.json)
      - EliteCreatures pack (assets/elitecreatures/models/<mob>/<part>.json)
      - Bedrock entity pack (models/entity/<mob>/<part>.json)
      - Bất kỳ namespace nào có models/<mob>/<part>.json

    Cách dùng:
        converter = MobModelConverter("pack.zip", "output/")
        result = converter.convert()
    """

    def __init__(self, input_zip: str, output_dir: str):
        self.input_zip  = input_zip
        self.output_dir = output_dir
        self.temp_dir   = os.path.join(output_dir, "_temp")

        # Dữ liệu quét được
        # { mob_name: { part_name: java_model_dict } }
        self.mobs: Dict[str, Dict[str, dict]] = {}
        # { mob_name: đường_dẫn_texture.png }
        self.mob_textures: Dict[str, str] = {}

        # Thống kê
        self.stats = {
            "converted": 0,
            "skipped":   0,
            "errors":    [],   # [(mob_name, error_message)]
        }

        os.makedirs(self.temp_dir,   exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    # ──────────────────────────────────────────────────────────
    #  BƯỚC 1: GIẢI NÉN
    # ──────────────────────────────────────────────────────────
    def _extract(self):
        print(f"📦 Giải nén {os.path.basename(self.input_zip)}...")
        ok = skip = 0
        with zipfile.ZipFile(self.input_zip, "r") as z:
            for member in z.infolist():
                try:
                    # Làm sạch path, bỏ ../ và ký tự nguy hiểm
                    clean = member.filename.replace("\\", "/").lstrip("/")
                    if ".." in clean:
                        skip += 1
                        continue
                    dest = os.path.join(self.temp_dir, clean)
                    if member.is_dir():
                        os.makedirs(dest, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        with z.open(member) as src, open(dest, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                    ok += 1
                except Exception:
                    skip += 1
        print(f"   ✅ {ok} files  (bỏ qua {skip} files lỗi)")

    # ──────────────────────────────────────────────────────────
    #  BƯỚC 2: QUÉT TÌM MODEL QUÁI
    # ──────────────────────────────────────────────────────────
    def _scan(self):
        print("\n🔍 Quét tìm model quái...")

        base = self.temp_dir

        # ── Dạng 1: ItemsAdder/ModelEngine pack ──
        #   assets/<namespace>/models/<mob_name>/<part>.json
        assets_dir = os.path.join(base, "assets")
        if os.path.exists(assets_dir):
            for ns_entry in os.scandir(assets_dir):
                if not ns_entry.is_dir():
                    continue
                models_dir = os.path.join(ns_entry.path, "models")
                if os.path.exists(models_dir):
                    self._scan_models_dir(models_dir)

                # Textures entity
                tex_entity = os.path.join(ns_entry.path, "textures", "entity")
                if os.path.exists(tex_entity):
                    self._scan_textures_dir(tex_entity)

        # ── Dạng 2: Bedrock pack ──
        #   models/entity/<mob_name>/<part>.json
        models_entity = os.path.join(base, "models", "entity")
        if os.path.exists(models_entity):
            self._scan_models_dir(models_entity)

        # Textures entity Bedrock
        tex_bedrock = os.path.join(base, "textures", "entity")
        if os.path.exists(tex_bedrock):
            self._scan_textures_dir(tex_bedrock)

        # ── Tóm tắt ──
        print(f"\n   📊 Tìm thấy: {len(self.mobs)} mobs")
        for mob_name, parts in self.mobs.items():
            has_tex = "✅" if mob_name in self.mob_textures else "⚠️ "
            print(f"   {has_tex} {mob_name}  ({len(parts)} parts)")

    def _scan_models_dir(self, models_dir: str):
        """
        Quét thư mục models/ để tìm mob subdirs.
        Mỗi subdir = một mob, mỗi .json trong đó = một part.
        """
        for mob_entry in os.scandir(models_dir):
            if not mob_entry.is_dir():
                continue
            mob_name = mob_entry.name
            parts = self._load_parts(mob_entry.path)
            if parts:
                # Gộp nếu mob đã tồn tại (nhiều namespace)
                if mob_name not in self.mobs:
                    self.mobs[mob_name] = {}
                self.mobs[mob_name].update(parts)

    def _load_parts(self, mob_dir: str) -> Dict[str, dict]:
        """Đọc tất cả .json trong thư mục mob, trả về { part_name: model_dict }."""
        parts = {}
        for f in os.scandir(mob_dir):
            if not f.name.endswith(".json"):
                continue
            data = self._read_json_safe(f.path)
            if data is None:
                continue
            # Chỉ nhận Java model có "elements"
            if "elements" in data:
                parts[f.name.replace(".json", "")] = data
        return parts

    @staticmethod
    def _read_json_safe(path: str) -> Optional[dict]:
        """Đọc JSON an toàn, thử nhiều encoding, bỏ qua file binary."""
        raw = open(path, "rb").read()
        stripped = raw.lstrip()
        if not stripped or stripped[0] not in (ord("{"), ord("[")):
            return None
        for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                return json.loads(raw.decode(enc))
            except Exception:
                pass
        return None

    def _scan_textures_dir(self, tex_dir: str):
        """Quét thư mục textures/entity/ để map mob_name → texture path."""
        for f in os.scandir(tex_dir):
            if f.name.endswith(".png"):
                mob_name = f.name.replace(".png", "")
                # Không ghi đè nếu đã có
                if mob_name not in self.mob_textures:
                    self.mob_textures[mob_name] = f.path

    # ──────────────────────────────────────────────────────────
    #  BƯỚC 3: BUILD OUTPUT BEDROCK PACK
    # ──────────────────────────────────────────────────────────
    def _build_bedrock_pack(self) -> str:
        """Tạo cấu trúc thư mục Bedrock và trả về đường dẫn."""
        pack_dir = os.path.join(self.output_dir, "mob_models_bedrock")
        os.makedirs(pack_dir, exist_ok=True)

        # Manifest
        manifest = {
            "format_version": 2,
            "header": {
                "description": "Mob Models - Converted by MobModelConverter",
                "name":        "Mob Models Pack",
                "uuid":        str(uuid.uuid4()),
                "version":     [1, 0, 0],
                "min_engine_version": [1, 16, 0]
            },
            "modules": [{
                "description": "Resource Pack",
                "type":        "resources",
                "uuid":        str(uuid.uuid4()),
                "version":     [1, 0, 0]
            }]
        }
        self._write_json(os.path.join(pack_dir, "manifest.json"), manifest)

        return pack_dir

    def _convert_all_mobs(self, pack_dir: str):
        """Convert từng mob và ghi file output."""
        print(f"\n🔄 Đang convert {len(self.mobs)} mobs...\n")

        geo_dir    = os.path.join(pack_dir, "models", "entity")
        entity_dir = os.path.join(pack_dir, "entity")
        rc_dir     = os.path.join(pack_dir, "render_controllers")
        tex_dir    = os.path.join(pack_dir, "textures", "entity")

        for d in [geo_dir, entity_dir, rc_dir, tex_dir]:
            os.makedirs(d, exist_ok=True)

        for mob_name, parts in self.mobs.items():
            try:
                result = self._convert_one_mob(
                    mob_name, parts,
                    geo_dir, entity_dir, rc_dir, tex_dir
                )
                if result:
                    self.stats["converted"] += 1
                    has_tex = "🖼️" if mob_name in self.mob_textures else "  "
                    print(f"   ✅ {has_tex} {mob_name}  ({len(parts)} parts)")
                else:
                    self.stats["skipped"] += 1
                    print(f"   ⚠️  {mob_name}  – bỏ qua (không có geometry hợp lệ)")
            except Exception as e:
                self.stats["skipped"] += 1
                self.stats["errors"].append((mob_name, str(e)))
                print(f"   ❌  {mob_name}  – lỗi: {e}")

    def _convert_one_mob(
        self,
        mob_name:   str,
        parts:      Dict[str, dict],
        geo_dir:    str,
        entity_dir: str,
        rc_dir:     str,
        tex_dir:    str
    ) -> bool:
        """
        Convert một mob:
          1. Tạo geometry  →  models/entity/<mob>.geo.json
          2. Tạo entity    →  entity/<mob>.entity.json
          3. Tạo render controller  →  render_controllers/<mob>.rc.json
          4. Copy texture (nếu có)  →  textures/entity/<mob>.png
        """
        # 1. Geometry
        geo = JavaGeometryConverter.convert_mob_geometry(mob_name, parts)
        if geo is None:
            return False

        self._write_json(
            os.path.join(geo_dir, f"{mob_name}.geo.json"),
            geo
        )

        # 2. Entity definition
        self._write_json(
            os.path.join(entity_dir, f"{mob_name}.entity.json"),
            BedrockMobBuilder.build_entity(mob_name)
        )

        # 3. Render controller
        self._write_json(
            os.path.join(rc_dir, f"{mob_name}.render_controllers.json"),
            BedrockMobBuilder.build_render_controller(mob_name)
        )

        # 4. Texture
        src_tex = self.mob_textures.get(mob_name)
        if src_tex and os.path.exists(src_tex):
            shutil.copy2(src_tex, os.path.join(tex_dir, f"{mob_name}.png"))

        return True

    # ──────────────────────────────────────────────────────────
    #  BƯỚC 4: ĐÓNG GÓI
    # ──────────────────────────────────────────────────────────
    def _package(self, pack_dir: str):
        """Tạo .mcpack và .zip từ thư mục output."""
        print("\n📦 Đóng gói files...")

        mcpack_path = os.path.join(self.output_dir, "MobModels_Bedrock.mcpack")
        zip_path    = os.path.join(self.output_dir, "mob_models_geyser.zip")

        with zipfile.ZipFile(mcpack_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(pack_dir):
                for f in files:
                    fp = os.path.join(root, f)
                    zf.write(fp, os.path.relpath(fp, pack_dir))

        shutil.copy2(mcpack_path, zip_path)

        size_kb = os.path.getsize(mcpack_path) // 1024
        print(f"   ✅ MobModels_Bedrock.mcpack  ({size_kb} KB)")
        print(f"   ✅ mob_models_geyser.zip  ({size_kb} KB)")

    # ──────────────────────────────────────────────────────────
    #  BƯỚC 5: BÁO CÁO
    # ──────────────────────────────────────────────────────────
    def _write_report(self):
        """Ghi file báo cáo README.md."""
        lines = [
            f"# Mob Models Conversion Report",
            f"**Ngày:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Tool:** MobModelConverter",
            f"",
            f"## Kết Quả",
            f"| | |",
            f"|---|---|",
            f"| ✅ Thành công | {self.stats['converted']} mobs |",
            f"| ⚠️  Bỏ qua | {self.stats['skipped']} mobs |",
            f"| ❌ Lỗi | {len(self.stats['errors'])} mobs |",
            f"",
            f"## Files Tạo Ra",
            f"- `MobModels_Bedrock.mcpack` – Cài trực tiếp vào Minecraft Bedrock",
            f"- `mob_models_geyser.zip` – Upload vào `Geyser/packs/`",
            f"",
            f"## Cách Dùng",
            f"**Bedrock Player:**",
            f"1. Tải `MobModels_Bedrock.mcpack`",
            f"2. Mở file → Minecraft tự động import",
            f"3. Bật pack trong Global Resources",
            f"",
            f"**Geyser Server:**",
            f"1. Upload `mob_models_geyser.zip` → `plugins/Geyser-Spigot/packs/`",
            f"2. Chạy `/geyser reload`",
        ]

        if self.stats["errors"]:
            lines += ["", "## Danh Sách Lỗi"]
            for mob_name, err in self.stats["errors"]:
                lines.append(f"- `{mob_name}`: {err}")

        if self.mobs:
            lines += ["", f"## Danh Sách Mobs ({len(self.mobs)})"]
            for mob_name, parts in sorted(self.mobs.items()):
                has_tex = "✅" if mob_name in self.mob_textures else "⚠️ "
                lines.append(f"- {has_tex} `{mob_name}` – {len(parts)} parts")

        with open(os.path.join(self.output_dir, "MOB_REPORT.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    # ──────────────────────────────────────────────────────────
    #  HELPER
    # ──────────────────────────────────────────────────────────
    @staticmethod
    def _write_json(path: str, data: dict):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _cleanup(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _print_summary(self):
        print("\n" + "=" * 60)
        print("  ✨  MOB MODELS CONVERSION COMPLETE!")
        print("=" * 60)
        print(f"  📁  Output  : {os.path.abspath(self.output_dir)}")
        print(f"  🐾  Mobs    : {len(self.mobs)}")
        print(f"  ✅  Thành công : {self.stats['converted']}")
        print(f"  ⚠️   Bỏ qua    : {self.stats['skipped']}")
        print(f"  ❌  Lỗi        : {len(self.stats['errors'])}")
        print()
        print("  📦  Files:")
        print("       MobModels_Bedrock.mcpack")
        print("       mob_models_geyser.zip")
        print("       MOB_REPORT.md")
        print()

    # ──────────────────────────────────────────────────────────
    #  ENTRY POINT CHÍNH
    # ──────────────────────────────────────────────────────────
    def convert(self) -> dict:
        """
        Chạy toàn bộ quá trình convert.
        Returns: dict stats { converted, skipped, errors }
        """
        print("\n" + "=" * 60)
        print("  🐾  MOB MODEL CONVERTER")
        print("  Convert model quái → Bedrock Edition")
        print("=" * 60 + "\n")

        try:
            # 1. Giải nén
            self._extract()

            # 2. Quét tìm mobs
            self._scan()

            if not self.mobs:
                print("\n⚠️  Không tìm thấy model quái nào trong pack này!")
                print("   Pack cần có thư mục: models/<mob_name>/<part>.json")
                return self.stats

            # 3. Tạo cấu trúc Bedrock
            pack_dir = self._build_bedrock_pack()

            # 4. Convert từng mob
            self._convert_all_mobs(pack_dir)

            # 5. Đóng gói
            self._package(pack_dir)

            # 6. Báo cáo
            self._write_report()

            # 7. Dọn dẹp
            self._cleanup()

            # 8. Tóm tắt
            self._print_summary()

        except Exception as e:
            import traceback
            print(f"\n❌ Lỗi nghiêm trọng: {e}")
            traceback.print_exc()
            raise

        return self.stats


# ══════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("╔══════════════════════════════════════════════╗")
        print("║  Mob Model Converter – Cách dùng:           ║")
        print("╠══════════════════════════════════════════════╣")
        print("║  python mob_model_converter.py <file.zip>   ║")
        print("║  python mob_model_converter.py pack.zip     ║")
        print("║  python mob_model_converter.py pack.zip out ║")
        print("╚══════════════════════════════════════════════╝")
        sys.exit(0)

    input_zip  = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "mob_output"

    if not os.path.exists(input_zip):
        print(f"❌ Không tìm thấy file: {input_zip}")
        sys.exit(1)

    converter = MobModelConverter(input_zip, output_dir)
    converter.convert()
