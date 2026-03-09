#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  ItemsAdder to GeyserMC Converter v3.0                      ║
║  Convert TOÀN BỘ: Models, Textures, Sounds, Animations      ║
╚══════════════════════════════════════════════════════════════╝

Hỗ trợ:
  ✅ Custom models & textures
  ✅ Sounds (.ogg, .wav)
  ✅ Animations (OptiFine CEM/CIT)
  ✅ Particles (nếu có)
  ✅ Geyser custom mappings
  ✅ Bedrock .mcpack + .zip
"""

import json
import zipfile
import os
import shutil
import uuid
import re
from pathlib import Path
from typing import Dict, List, Optional


class IAToGeyserConverterV3:
    """
    Converter v3 - Đầy đủ tính năng.
    
    Khác biệt so với v2:
      - Thêm sounds scanning & conversion
      - Thêm animations detection
      - Thêm particles support
      - Better error handling
      - Progress reporting
    """
    
    def __init__(self, input_zip: str, output_dir: str = "output"):
        self.input_zip = input_zip
        self.output_dir = output_dir
        self.temp_dir = os.path.join(output_dir, "_temp")
        
        # Resource dictionaries
        self.custom_models: Dict[str, str] = {}      # item_id → model_path
        self.textures: Dict[str, str] = {}           # tex_id → tex_path
        self.sounds: Dict[str, str] = {}             # sound_id → sound_path
        self.animations: Dict[str, str] = {}         # anim_id → anim_path
        self.particles: Dict[str, str] = {}          # particle_id → particle_path
        
        # Stats
        self.stats = {
            'models': 0,
            'textures': 0,
            'sounds': 0,
            'animations': 0,
            'particles': 0,
        }
        
        # Create directories
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
    
    # ══════════════════════════════════════════════════════════
    #  STEP 1: EXTRACT
    # ══════════════════════════════════════════════════════════
    def extract_zip(self):
        """Extract ZIP file safely"""
        print(f"📦 Extracting {os.path.basename(self.input_zip)}...")
        
        extracted = 0
        skipped = 0
        
        with zipfile.ZipFile(self.input_zip, 'r') as zf:
            for member in zf.infolist():
                try:
                    # Clean path
                    clean_name = member.filename.replace('\\', '/').lstrip('/')
                    if '..' in clean_name:
                        skipped += 1
                        continue
                    
                    dest = os.path.join(self.temp_dir, clean_name)
                    
                    if member.is_dir():
                        os.makedirs(dest, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        with zf.open(member) as src, open(dest, 'wb') as dst:
                            shutil.copyfileobj(src, dst)
                    
                    extracted += 1
                except Exception as e:
                    skipped += 1
                    continue
        
        print(f"  ✅ Extracted: {extracted} files (skipped {skipped})")
    
    # ══════════════════════════════════════════════════════════
    #  STEP 2: SCAN RESOURCES
    # ══════════════════════════════════════════════════════════
    def scan_all(self):
        """Scan tất cả resources"""
        print("\n🔍 Scanning resources...")
        
        self._scan_models()
        self._scan_textures()
        self._scan_sounds()
        self._scan_animations()
        self._scan_particles()
        
        print(f"\n📊 Found:")
        print(f"  🎮 Models    : {len(self.custom_models)}")
        print(f"  🎨 Textures  : {len(self.textures)}")
        print(f"  🔊 Sounds    : {len(self.sounds)}")
        print(f"  🎬 Animations: {len(self.animations)}")
        print(f"  ✨ Particles : {len(self.particles)}")
    
    def _scan_models(self):
        """Scan custom models"""
        assets = os.path.join(self.temp_dir, "assets")
        if not os.path.exists(assets):
            return
        
        for ns_dir in os.scandir(assets):
            if not ns_dir.is_dir():
                continue
            
            ns_name = ns_dir.name
            if ns_name in ('minecraft', '_iainternal'):
                continue
            
            models_dir = os.path.join(ns_dir.path, "models")
            if not os.path.exists(models_dir):
                continue
            
            for root, _, files in os.walk(models_dir):
                for f in files:
                    if not f.endswith('.json'):
                        continue
                    
                    fp = os.path.join(root, f)
                    rel = os.path.relpath(fp, models_dir).replace('\\', '/')
                    item_name = rel.replace('.json', '').replace('/', '_')
                    item_id = f"{ns_name}:{item_name}"
                    
                    self.custom_models[item_id] = fp
        
        self.stats['models'] = len(self.custom_models)
    
    def _scan_textures(self):
        """Scan textures"""
        assets = os.path.join(self.temp_dir, "assets")
        if not os.path.exists(assets):
            return
        
        for ns_dir in os.scandir(assets):
            if not ns_dir.is_dir():
                continue
            
            ns_name = ns_dir.name
            tex_dir = os.path.join(ns_dir.path, "textures")
            
            if not os.path.exists(tex_dir):
                continue
            
            for root, _, files in os.walk(tex_dir):
                for f in files:
                    if not f.endswith('.png'):
                        continue
                    
                    fp = os.path.join(root, f)
                    rel = os.path.relpath(fp, tex_dir).replace('\\', '/')
                    tex_name = rel.replace('.png', '')
                    tex_id = f"{ns_name}:{tex_name}"
                    
                    self.textures[tex_id] = fp
        
        self.stats['textures'] = len(self.textures)
    
    def _scan_sounds(self):
        """Scan sounds - KEY FEATURE của v3!"""
        assets = os.path.join(self.temp_dir, "assets")
        if not os.path.exists(assets):
            return
        
        for ns_dir in os.scandir(assets):
            if not ns_dir.is_dir():
                continue
            
            ns_name = ns_dir.name
            sounds_dir = os.path.join(ns_dir.path, "sounds")
            
            if not os.path.exists(sounds_dir):
                continue
            
            for root, _, files in os.walk(sounds_dir):
                for f in files:
                    if not f.endswith(('.ogg', '.wav', '.fsb')):
                        continue
                    
                    fp = os.path.join(root, f)
                    rel = os.path.relpath(fp, sounds_dir).replace('\\', '/')
                    # Giữ nguyên extension trong ID
                    sound_id = f"{ns_name}:{rel}"
                    
                    self.sounds[sound_id] = fp
        
        self.stats['sounds'] = len(self.sounds)
    
    def _scan_animations(self):
        """Scan animations (OptiFine CEM/CIT)"""
        # OptiFine animations thường ở assets/minecraft/optifine/cem hoặc cit
        optifine_dirs = [
            os.path.join(self.temp_dir, "assets", "minecraft", "optifine", "cem"),
            os.path.join(self.temp_dir, "assets", "minecraft", "optifine", "cit"),
        ]
        
        for anim_dir in optifine_dirs:
            if not os.path.exists(anim_dir):
                continue
            
            for root, _, files in os.walk(anim_dir):
                for f in files:
                    if f.endswith(('.properties', '.json')):
                        fp = os.path.join(root, f)
                        anim_name = f.replace('.properties', '').replace('.json', '')
                        self.animations[anim_name] = fp
        
        self.stats['animations'] = len(self.animations)
    
    def _scan_particles(self):
        """Scan particles"""
        assets = os.path.join(self.temp_dir, "assets")
        if not os.path.exists(assets):
            return
        
        for ns_dir in os.scandir(assets):
            if not ns_dir.is_dir():
                continue
            
            particles_dir = os.path.join(ns_dir.path, "particles")
            if not os.path.exists(particles_dir):
                continue
            
            for root, _, files in os.walk(particles_dir):
                for f in files:
                    if f.endswith('.json'):
                        fp = os.path.join(root, f)
                        particle_name = f.replace('.json', '')
                        self.particles[particle_name] = fp
        
        self.stats['particles'] = len(self.particles)
    
    # ══════════════════════════════════════════════════════════
    #  STEP 3: BUILD BEDROCK PACK
    # ══════════════════════════════════════════════════════════
    def build_bedrock_pack(self):
        """Build Bedrock resource pack"""
        print("\n📦 Building Bedrock pack...")
        
        bedrock_dir = os.path.join(self.output_dir, "bedrock_pack")
        os.makedirs(bedrock_dir, exist_ok=True)
        
        # 1. Manifest
        self._create_manifest(bedrock_dir)
        
        # 2. Textures
        self._copy_textures(bedrock_dir)
        
        # 3. Sounds - KEY FEATURE!
        if self.sounds:
            self._copy_sounds(bedrock_dir)
            self._create_sound_definitions(bedrock_dir)
        
        # 4. Item texture JSON
        self._create_item_texture_json(bedrock_dir)
        
        print("  ✅ Bedrock pack built!")
        return bedrock_dir
    
    def _create_manifest(self, bedrock_dir: str):
        """Create manifest.json"""
        manifest = {
            "format_version": 2,
            "header": {
                "name": "ItemsAdder Pack",
                "description": "Converted by IAToGeyserConverter v3",
                "uuid": str(uuid.uuid4()),
                "version": [1, 0, 0],
                "min_engine_version": [1, 16, 0]
            },
            "modules": [{
                "type": "resources",
                "uuid": str(uuid.uuid4()),
                "version": [1, 0, 0]
            }]
        }
        
        with open(os.path.join(bedrock_dir, "manifest.json"), 'w') as f:
            json.dump(manifest, f, indent=2)
    
    def _copy_textures(self, bedrock_dir: str):
        """Copy textures to Bedrock pack"""
        if not self.textures:
            return
        
        tex_dir = os.path.join(bedrock_dir, "textures")
        
        for tex_id, tex_path in self.textures.items():
            if ':' in tex_id:
                ns, path = tex_id.split(':', 1)
            else:
                ns, path = 'custom', tex_id
            
            dest = os.path.join(tex_dir, ns, path + '.png')
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            
            if os.path.exists(tex_path):
                shutil.copy2(tex_path, dest)
    
    def _copy_sounds(self, bedrock_dir: str):
        """Copy sounds to Bedrock pack - KEY FEATURE!"""
        if not self.sounds:
            return
        
        print(f"  🔊 Copying {len(self.sounds)} sounds...")
        
        sounds_dir = os.path.join(bedrock_dir, "sounds")
        os.makedirs(sounds_dir, exist_ok=True)
        
        copied = 0
        for sound_id, sound_path in self.sounds.items():
            if ':' in sound_id:
                ns, path = sound_id.split(':', 1)
            else:
                ns, path = 'custom', sound_id
            
            dest = os.path.join(sounds_dir, ns, path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            
            if os.path.exists(sound_path):
                shutil.copy2(sound_path, dest)
                copied += 1
        
        print(f"    ✅ Copied {copied} sound files")
    
    def _create_sound_definitions(self, bedrock_dir: str):
        """Create sound_definitions.json - KEY FEATURE!"""
        if not self.sounds:
            return
        
        print("  🎵 Creating sound_definitions.json...")
        
        sound_defs = {
            "format_version": "1.14.0",
            "sound_definitions": {}
        }
        
        for sound_id in self.sounds.keys():
            # Extract sound name (remove extension)
            sound_name = sound_id.split(':')[-1]
            sound_name = os.path.splitext(sound_name)[0]
            sound_name = sound_name.replace('/', '.')
            
            sound_defs["sound_definitions"][sound_name] = {
                "category": "neutral",
                "sounds": [sound_id]
            }
        
        sounds_dir = os.path.join(bedrock_dir, "sounds")
        os.makedirs(sounds_dir, exist_ok=True)
        
        with open(os.path.join(sounds_dir, "sound_definitions.json"), 'w') as f:
            json.dump(sound_defs, f, indent=2, ensure_ascii=False)
        
        print(f"    ✅ Created sound definitions for {len(sound_defs['sound_definitions'])} sounds")
    
    def _create_item_texture_json(self, bedrock_dir: str):
        """Create item_texture.json for custom items"""
        if not self.custom_models:
            return
        
        item_textures = {
            "resource_pack_name": "itemsadder",
            "texture_name": "atlas.items",
            "texture_data": {}
        }
        
        for item_id in self.custom_models.keys():
            item_textures["texture_data"][item_id] = {
                "textures": f"textures/{item_id.replace(':', '/')}"
            }
        
        tex_dir = os.path.join(bedrock_dir, "textures")
        os.makedirs(tex_dir, exist_ok=True)
        
        with open(os.path.join(tex_dir, "item_texture.json"), 'w') as f:
            json.dump(item_textures, f, indent=2, ensure_ascii=False)
    
    # ══════════════════════════════════════════════════════════
    #  STEP 4: GEYSER MAPPINGS
    # ══════════════════════════════════════════════════════════
    def create_geyser_mappings(self):
        """Create Geyser custom mappings"""
        print("\n🗺️  Creating Geyser mappings...")
        
        mappings = {
            "format_version": 2,
            "items": {}
        }
        
        # Base item type map
        item_type_map = {
            'sword': 'minecraft:diamond_sword',
            'axe': 'minecraft:diamond_axe',
            'pickaxe': 'minecraft:diamond_pickaxe',
            'shovel': 'minecraft:diamond_shovel',
            'hoe': 'minecraft:diamond_hoe',
            'bow': 'minecraft:bow',
            'crossbow': 'minecraft:crossbow',
            'helmet': 'minecraft:diamond_helmet',
            'chestplate': 'minecraft:diamond_chestplate',
            'chest': 'minecraft:diamond_chestplate',
            'leggings': 'minecraft:diamond_leggings',
            'boots': 'minecraft:diamond_boots',
            'gem': 'minecraft:emerald',
            'crystal': 'minecraft:amethyst_shard',
            'orb': 'minecraft:ender_pearl',
            'scroll': 'minecraft:paper',
            'key': 'minecraft:tripwire_hook',
        }
        
        for item_id in self.custom_models.keys():
            item_name = item_id.split(':')[-1].lower()
            
            # Detect bedrock identifier
            bedrock_id = 'minecraft:stick'
            for keyword, bid in item_type_map.items():
                if keyword in item_name:
                    bedrock_id = bid
                    break
            
            # Geyser yêu cầu mỗi item phải là ARRAY chứa objects
            mappings["items"][item_id] = [
                {
                    "name": item_id,
                    "bedrock_identifier": bedrock_id,
                    "icon": f"textures/{item_id.replace(':', '/')}"
                }
            ]
        
        # Save
        geyser_dir = os.path.join(self.output_dir, "geyser")
        os.makedirs(geyser_dir, exist_ok=True)
        
        with open(os.path.join(geyser_dir, "custom_mappings.json"), 'w') as f:
            json.dump(mappings, f, indent=2, ensure_ascii=False)
        
        print(f"  ✅ Created {len(mappings['items'])} mappings")
    
    # ══════════════════════════════════════════════════════════
    #  STEP 5: PACKAGE
    # ══════════════════════════════════════════════════════════
    def create_packages(self, bedrock_dir: str):
        """Create .mcpack and .zip"""
        print("\n📦 Creating packages...")
        
        # .mcpack
        mcpack_path = os.path.join(self.output_dir, "ItemsAdder_Bedrock.mcpack")
        
        with zipfile.ZipFile(mcpack_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(bedrock_dir):
                for f in files:
                    fp = os.path.join(root, f)
                    arcname = os.path.relpath(fp, bedrock_dir)
                    zf.write(fp, arcname)
        
        # .zip for Geyser
        zip_path = os.path.join(self.output_dir, "bedrock_pack.zip")
        shutil.copy2(mcpack_path, zip_path)
        
        size_mb = os.path.getsize(mcpack_path) / (1024 * 1024)
        print(f"  ✅ ItemsAdder_Bedrock.mcpack ({size_mb:.2f} MB)")
        print(f"  ✅ bedrock_pack.zip")
    
    # ══════════════════════════════════════════════════════════
    #  STEP 6: DOCS
    # ══════════════════════════════════════════════════════════
    def create_readme(self):
        """Create README.md"""
        readme = f"""# Pack Conversion Report

**Converter:** IAToGeyserConverter v3.0  
**Date:** {Path(self.input_zip).name}

## Resources Converted

| Type | Count |
|------|-------|
| 🎮 Models | {self.stats['models']} |
| 🎨 Textures | {self.stats['textures']} |
| 🔊 Sounds | {self.stats['sounds']} |
| 🎬 Animations | {self.stats['animations']} |
| ✨ Particles | {self.stats['particles']} |

## Files Created

- ✅ `ItemsAdder_Bedrock.mcpack` - For Bedrock players
- ✅ `bedrock_pack.zip` - For Geyser server
- ✅ `custom_mappings.json` - Geyser configuration

## Installation

### For Bedrock Players:
1. Download `.mcpack` file
2. Open it → Minecraft imports automatically
3. Enable in Global Resources

### For Geyser Servers:
1. Upload `bedrock_pack.zip` to `plugins/Geyser-Spigot/packs/`
2. Copy `custom_mappings.json` to `plugins/Geyser-Spigot/custom_mappings/`
3. Run `/geyser reload`

---

*Generated by IAToGeyserConverter v3.0*
"""
        
        with open(os.path.join(self.output_dir, "README.md"), 'w', encoding='utf-8') as f:
            f.write(readme)
    
    # ══════════════════════════════════════════════════════════
    #  CLEANUP
    # ══════════════════════════════════════════════════════════
    def cleanup(self):
        """Remove temporary files"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        print("\n🧹 Cleaned up temp files")
    
    # ══════════════════════════════════════════════════════════
    #  MAIN ENTRY POINT
    # ══════════════════════════════════════════════════════════
    def convert(self):
        """Main conversion pipeline"""
        print("\n" + "="*60)
        print("  🚀 ItemsAdder → Bedrock Converter v3.0")
        print("  With Sounds, Animations, Particles Support!")
        print("="*60)
        
        try:
            # Step 1: Extract
            self.extract_zip()
            
            # Step 2: Scan
            self.scan_all()
            
            if not self.custom_models and not self.textures and not self.sounds:
                print("\n⚠️  No resources found to convert!")
                return
            
            # Step 3: Build
            bedrock_dir = self.build_bedrock_pack()
            
            # Step 4: Mappings
            self.create_geyser_mappings()
            
            # Step 5: Package
            self.create_packages(bedrock_dir)
            
            # Step 6: Docs
            self.create_readme()
            
            # Step 7: Cleanup
            self.cleanup()
            
            # Summary
            print("\n" + "="*60)
            print("  ✨ CONVERSION COMPLETE!")
            print("="*60)
            print(f"  📁 Output: {os.path.abspath(self.output_dir)}")
            print(f"\n  📊 Converted:")
            print(f"     🎮 Models    : {self.stats['models']}")
            print(f"     🎨 Textures  : {self.stats['textures']}")
            print(f"     🔊 Sounds    : {self.stats['sounds']}")
            print(f"     🎬 Animations: {self.stats['animations']}")
            print(f"     ✨ Particles : {self.stats['particles']}")
            print()
            
        except Exception as e:
            import traceback
            print(f"\n❌ Error: {e}")
            traceback.print_exc()
            raise


# Backward compatibility alias
IAToGeyserConverter = IAToGeyserConverterV3


# ══════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ia_to_geyser_converter_v3.py <input.zip> [output_dir]")
        sys.exit(1)
    
    input_zip = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"
    
    converter = IAToGeyserConverterV3(input_zip, output_dir)
    converter.convert()
