#!/usr/bin/env python3
"""Phase 28: generate a complete missing-asset kit.

The kit is intentionally add-only and native-dimensioned. It creates draft
spritesheets, portraits, icons, map previews, manifests and review queues for
all currently planned LOG4 content. These are production-ready *templates* and
low-color draft placeholders, not final hand-cleaned pixel art.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import zipfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "additive_content" / "final_asset_kit"
DOC = ROOT / "docs" / "PHASE28_MISSING_ASSET_KIT.md"
PHASE_DOC = ROOT / "docs" / "PROJECT_PHASES_REMAINING.md"
ZIP_OUT = ROOT / "patch_output" / "LOG4_phase28_missing_asset_kit.zip"

CELL = 40
BOSS_CELL = 72
PORTRAIT = 40
ICON_SMALL = 16
ICON_BIG = 32
SCREEN = (240, 160)
TILE = 8
STD_FRAMES = [2, 4, 4, 3, 4, 4, 4, 1, 4, 3, 11, 2, 2, 3, 4, 4, 4, 3, 3, 11]
DIRECTIONS = ["down", "up", "side_right", "side_left"]

PLAYABLES = [
    ("GOKU_SUPER", "Goku Super", (244, 128, 38), ["SSJ", "SSJ2", "SSG", "SSB", "UI_SIGN", "UI_MASTERED"]),
    ("GOKU_GT", "Goku GT", (44, 92, 198), ["SSJ4"]),
    ("VEGETA_SUPER", "Vegeta Super", (46, 92, 178), ["SSJ", "SSJ2", "SSG", "SSB", "SSBE", "ULTRA_EGO"]),
    ("VEGETA_GT", "Vegeta GT", (222, 184, 56), ["SSJ4"]),
    ("GOHAN_SUPER", "Gohan Super", (116, 70, 178), ["SSJ", "SSJ2", "ULTIMATE", "BEAST"]),
    ("FUTURE_TRUNKS_DBS", "Future Trunks DBS", (70, 142, 220), ["SSJ", "SSJ2", "RAGE"]),
    ("GOTEN", "Goten", (238, 208, 54), ["SSJ"]),
    ("TRUNKS_KID", "Trunks Kid", (184, 72, 72), ["SSJ"]),
    ("GOTENKS", "Gotenks", (230, 176, 54), ["SSJ", "SSJ3"]),
    ("VEGITO", "Vegito", (42, 94, 204), ["SUPER_VEGITO", "VEGITO_BLUE"]),
    ("GOGETA", "Gogeta", (236, 164, 42), ["SUPER_GOGETA", "GOGETA_BLUE"]),
    ("PAN_GT", "Pan GT", (220, 54, 48), ["SSJ"]),
    ("UUB_GT", "Uub", (220, 220, 220), ["MAJUUB", "SUPER_MAJUUB"]),
    ("PICCOLO", "Piccolo", (72, 178, 74), ["ORANGE_PICCOLO", "SUPER_NAMEKIAN_AF"]),
    ("KRILLIN", "Krillin", (238, 156, 58), []),
    ("YAMCHA", "Yamcha", (214, 132, 58), []),
    ("TENSHINHAN", "Tenshinhan", (92, 178, 128), []),
    ("ANDROID_17", "Android 17", (64, 90, 72), []),
    ("ANDROID_18", "Android 18", (118, 158, 220), []),
    ("XICOR_AF", "Xicor AF", (228, 226, 176), ["DIVINE_FORM", "FINAL_FORM"]),
]

ENEMIES = [
    ("RADITZ", "Raditz", "LOG1", (104, 76, 54), "standard"),
    ("NAPPA", "Nappa", "LOG1", (190, 160, 112), "large"),
    ("VEGETA_SAIYAN", "Vegeta Saiyan", "LOG1", (42, 80, 170), "standard"),
    ("GINYU_FORCE", "Ginyu Force", "LOG1", (110, 72, 180), "standard"),
    ("FRIEZA_LOG1", "Frieza", "LOG1", (218, 218, 234), "standard"),
    ("FRIEZA_MINION", "Frieza Minion", "LOG1", (120, 170, 210), "standard"),
    ("WOLF_LOG1", "Wolf", "LOG1", (92, 92, 102), "standard"),
    ("ANDROID_16", "Android 16", "LOG2", (68, 160, 102), "large"),
    ("ANDROID_17_BOSS", "Android 17", "LOG2", (64, 90, 72), "standard"),
    ("ANDROID_18_BOSS", "Android 18", "LOG2", (118, 158, 220), "standard"),
    ("ANDROID_19", "Android 19", "LOG2", (230, 214, 186), "standard"),
    ("DR_GERO", "Dr. Gero", "LOG2", (86, 76, 96), "standard"),
    ("CELL_IMPERFECT", "Cell Imperfect", "LOG2", (74, 174, 82), "large"),
    ("CELL_SEMI", "Cell Semi-Perfect", "LOG2", (104, 190, 84), "large"),
    ("CELL_PERFECT", "Cell Perfect", "LOG2", (78, 208, 88), "large"),
    ("CELL_JR", "Cell Jr", "LOG2", (62, 142, 228), "standard"),
    ("COOLER", "Cooler", "LOG2", (156, 148, 218), "large"),
    ("MERCENARY_TAO", "Mercenary Tao", "LOG2", (236, 88, 74), "standard"),
    ("T_REX", "T-Rex", "LOG2", (92, 150, 72), "large"),
    ("TRICERATOPS", "Triceratops", "LOG2", (124, 148, 88), "large"),
    ("BEERUS", "Beerus", "SUPER", (126, 76, 178), "standard"),
    ("GOLDEN_FRIEZA", "Golden Frieza", "SUPER", (238, 198, 54), "standard"),
    ("HIT", "Hit", "SUPER", (88, 64, 132), "standard"),
    ("GOKU_BLACK", "Goku Black", "SUPER", (40, 42, 52), "standard"),
    ("ZAMASU", "Zamasu", "SUPER", (178, 228, 180), "standard"),
    ("JIREN", "Jiren", "SUPER", (206, 46, 42), "large"),
    ("BROLY_DBS", "Broly DBS", "SUPER", (92, 210, 76), "large"),
    ("MORO", "Moro", "SUPER", (86, 108, 136), "large"),
    ("GRANOLAH", "Granolah", "SUPER", (82, 178, 168), "standard"),
    ("GENERAL_RILDO", "General Rilldo", "GT", (128, 146, 160), "large"),
    ("BABY_VEGETA", "Baby Vegeta", "GT", (218, 208, 164), "large"),
    ("SUPER_17", "Super 17", "GT", (40, 46, 68), "large"),
    ("OMEGA_SHENRON", "Omega Shenron", "GT", (236, 236, 236), "large"),
    ("IKL_AF", "I'K'l", "AF", (182, 218, 238), "large"),
    ("XICOR_FINAL", "Xicor Final", "AF", (238, 226, 142), "large"),
]

MAPS = [
    ("CAPSULE_RIFT_LAB", "Capsule Corp Rift Lab", (46, 68, 96), (96, 220, 240)),
    ("BEERUS_PLANET", "Beerus Planet", (86, 66, 142), (172, 130, 226)),
    ("UNIVERSE_6_ARENA", "Universe 6 Arena", (96, 86, 70), (210, 180, 116)),
    ("FUTURE_CITY_RUINS", "Future City Ruins", (62, 58, 58), (196, 84, 50)),
    ("TOURNAMENT_POWER", "Tournament of Power", (46, 50, 70), (180, 180, 210)),
    ("PLANET_VAMPA", "Planet Vampa", (76, 86, 52), (170, 210, 80)),
    ("NEW_NAMEK", "New Namek", (58, 128, 92), (178, 230, 120)),
    ("PLANET_CEREAL", "Planet Cereal", (88, 130, 100), (220, 198, 122)),
    ("PLANET_M2_FACTORY", "Planet M-2 Factory", (70, 80, 88), (138, 154, 164)),
    ("GT_SHADOW_DRAGON_FIELD", "Shadow Dragon Field", (86, 72, 82), (210, 88, 62)),
    ("HELL_GT", "GT Hell", (82, 48, 58), (226, 72, 42)),
    ("LOG1_SNAKE_ROAD_MEMORY", "LOG1 Snake Road Memory", (72, 96, 66), (238, 184, 72)),
    ("LOG1_NAMEK_MEMORY", "LOG1 Namek Memory", (60, 132, 84), (170, 230, 106)),
    ("LOG2_WEST_CITY_MEMORY", "LOG2 West City Memory", (70, 92, 118), (98, 188, 238)),
    ("LOG2_CELL_GAMES_MEMORY", "LOG2 Cell Games Memory", (88, 74, 56), (210, 170, 96)),
    ("AF_KAIOSHIN_REALM", "AF Kaioshin Realm", (88, 118, 92), (210, 202, 118)),
    ("AF_XICOR_LAB", "AF Xicor Lab", (96, 64, 94), (226, 198, 238)),
]

ITEMS = [
    "BLACK_STAR_RADAR", "BLACK_STAR_1", "BLACK_STAR_2", "BLACK_STAR_3", "BLACK_STAR_4", "BLACK_STAR_5", "BLACK_STAR_6", "BLACK_STAR_7",
    "TIME_CHAMBER_KEY", "TOURNAMENT_INVITATION", "BABY_SCEPTER", "ANDROID_17_CORE", "MORO_SEAL_BOX", "KAIOSHIN_REALM_KEY",
    "IKL_SEAL_FRAGMENT", "STOLEN_GOKU_CELLS", "CREATOR_HEART", "DIVINE_EVIL_SEED", "SENZU_VIAL", "CAPSULE_ENERGY_DRINK",
]

TECHNIQUES = [
    "KAMEHAMEHA", "KAMEHAMEHA_10X", "SPIRIT_BOMB", "DRAGON_FIST", "DRAGON_GOD_FIST", "FINAL_FLASH", "FINAL_SHINE", "BURNING_ATTACK",
    "HEAT_DOME", "SPECIAL_BEAM_CANNON", "HELLZONE_GRENADE", "TIME_SKIP", "BLACK_KAMEHAMEHA", "SOUL_PUNISHER", "SPIRIT_SWORD", "DIVINE_JUDGMENT",
]


def ensure() -> None:
    for p in [OUT / "sprites" / "playable", OUT / "sprites" / "enemies", OUT / "portraits", OUT / "icons" / "items", OUT / "icons" / "techniques", OUT / "maps", OUT / "review"]:
        p.mkdir(parents=True, exist_ok=True)


def star_points(cx: float, cy: float, outer: float, inner: float) -> list[tuple[float, float]]:
    pts=[]
    for i in range(10):
        a=-math.pi/2+i*math.pi/5
        r=outer if i%2==0 else inner
        pts.append((cx+math.cos(a)*r, cy+math.sin(a)*r))
    return pts


def draw_actor_cell(base_color: tuple[int,int,int], label: str, size: int=40, direction: int=0, frame: int=0, aura: tuple[int,int,int] | None=None) -> Image.Image:
    img=Image.new("RGBA",(size,size),(0,0,0,0))
    d=ImageDraw.Draw(img)
    cx=size//2 + ((frame%2)*2-1 if frame else 0)
    foot=size-4
    if aura:
        d.ellipse((cx-size//3, foot-size//2, cx+size//3, foot+2), outline=aura+(150,))
    # shadow
    d.ellipse((cx-9, foot-4, cx+9, foot+1), fill=(20,20,24,100))
    # legs/body/head in Buu Fury-ish hard pixels
    dark=tuple(max(0,c//2) for c in base_color)
    hi=tuple(min(255,int(c*1.25)) for c in base_color)
    d.rectangle((cx-5, foot-17, cx+5, foot-7), fill=base_color+(255,), outline=dark+(255,))
    d.rectangle((cx-7, foot-8, cx-2, foot-2), fill=dark+(255,))
    d.rectangle((cx+2, foot-8, cx+7, foot-2), fill=dark+(255,))
    d.rectangle((cx-9, foot-16, cx-6, foot-9), fill=dark+(255,))
    d.rectangle((cx+6, foot-16, cx+9, foot-9), fill=dark+(255,))
    d.ellipse((cx-6, foot-28, cx+6, foot-16), fill=(236,178,126,255), outline=(70,42,30,255))
    # hair/silhouette by direction
    hair=(30,30,36) if sum(base_color)>430 else hi
    if direction==1:
        d.rectangle((cx-6, foot-28, cx+6, foot-23), fill=hair+(255,))
    elif direction in (2,3):
        d.polygon([(cx-7,foot-27),(cx+8,foot-25),(cx+4,foot-31)], fill=hair+(255,))
    else:
        d.polygon([(cx-7,foot-25),(cx-3,foot-32),(cx,foot-26),(cx+4,foot-32),(cx+7,foot-25)], fill=hair+(255,))
    # tiny label color pixels for review identity
    d.text((1,1), label[:2], fill=(255,255,255,255))
    return img


def make_standard_sheet(asset_id: str, color: tuple[int,int,int], path: Path, aura=None) -> dict[str,Any]:
    width=max(STD_FRAMES)*CELL
    height=sum(4*CELL for _ in STD_FRAMES)+8*(len(STD_FRAMES)-1)
    sheet=Image.new("RGBA",(width,height),(0,0,0,0))
    animations=[]; y=0
    for anim,frames in enumerate(STD_FRAMES):
        for direction in range(4):
            for frame in range(frames):
                cell=draw_actor_cell(color, asset_id, CELL, direction, frame, aura=aura)
                sheet.alpha_composite(cell,(frame*CELL,y+direction*CELL))
        animations.append({"animation": anim, "frames": frames, "directions": 4, "cell": [CELL,CELL], "region": [0,y,frames*CELL,4*CELL]})
        y+=4*CELL+8
    sheet.save(path, optimize=True)
    return {"asset_id": asset_id, "sheet": path.relative_to(ROOT).as_posix(), "size": [width,height], "animations": animations, "status": "draft_native_dimensions_needs_pixel_review"}


def make_enemy_sheet(asset_id: str, color: tuple[int,int,int], role: str, path: Path) -> dict[str,Any]:
    size=BOSS_CELL if role=="large" else CELL
    frames=[2,4,4,3,4,4]
    width=max(frames)*size
    height=sum(4*size for _ in frames)+8*(len(frames)-1)
    sheet=Image.new("RGBA",(width,height),(0,0,0,0))
    y=0; animations=[]
    for anim,fc in enumerate(frames):
        for direction in range(4):
            for frame in range(fc):
                cell=draw_actor_cell(color, asset_id, size, direction, frame, aura=(100,100,120) if role=="large" else None)
                sheet.alpha_composite(cell,(frame*size,y+direction*size))
        animations.append({"animation": anim, "frames": fc, "directions": 4, "cell": [size,size], "region": [0,y,fc*size,4*size]})
        y+=4*size+8
    sheet.save(path, optimize=True)
    return {"asset_id": asset_id, "role": role, "sheet": path.relative_to(ROOT).as_posix(), "size": [width,height], "animations": animations, "status": "draft_native_dimensions_needs_pixel_review"}


def make_portrait(asset_id: str, color: tuple[int,int,int]) -> str:
    img=Image.new("RGBA",(PORTRAIT,PORTRAIT),(0,0,0,0)); d=ImageDraw.Draw(img)
    dark=tuple(max(0,c//2) for c in color); hi=tuple(min(255,int(c*1.3)) for c in color)
    d.rectangle((2,2,37,37), fill=(28,36,54,255), outline=(210,190,80,255))
    d.ellipse((10,8,30,28), fill=(236,178,126,255), outline=dark+(255,))
    d.polygon([(9,15),(14,4),(20,12),(26,4),(31,15)], fill=hi+(255,))
    d.text((5,29), asset_id[:5], fill=(255,255,255,255))
    p=OUT/"portraits"/f"{asset_id}_portrait_40x40.png"; img.save(p,optimize=True)
    return p.relative_to(ROOT).as_posix()


def make_icon(asset_id: str, outdir: Path, color: tuple[int,int,int], size: int=16) -> str:
    img=Image.new("RGBA",(size,size),(0,0,0,0)); d=ImageDraw.Draw(img)
    d.rectangle((1,1,size-2,size-2), fill=color+(255,), outline=(30,30,34,255))
    d.polygon(star_points(size/2,size/2,size*0.33,size*0.14), fill=(20,20,24,255))
    if size>=32: d.text((3,size-12),asset_id[:4],fill=(255,255,255,255))
    p=outdir/f"{asset_id.lower()}_{size}x{size}.png"; img.save(p,optimize=True)
    return p.relative_to(ROOT).as_posix()


def make_map(map_id: str, title: str, base: tuple[int,int,int], accent: tuple[int,int,int]) -> dict[str,Any]:
    img=Image.new("RGBA",SCREEN,base+(255,)); d=ImageDraw.Draw(img)
    for y in range(0,SCREEN[1],TILE):
        for x in range(0,SCREEN[0],TILE):
            s=((x//8+y//8)%4)*5
            d.rectangle((x,y,x+7,y+7), fill=tuple(min(255,c+s) for c in base)+(255,))
            if (x*3+y*5)%96==0: d.point((x+4,y+4), fill=accent+(255,))
    d.rectangle((16,16,96,56), outline=accent+(255,), fill=tuple(max(0,c-20) for c in base)+(255,))
    d.rectangle((120,48,176,112), outline=accent+(255,), fill=tuple(min(255,c+20) for c in base)+(255,))
    d.rectangle((64,104,224,144), outline=accent+(255,), fill=tuple(max(0,c-8) for c in base)+(255,))
    d.text((6,146), title[:32], fill=tuple(min(255,c+80) for c in accent)+(255,))
    p=OUT/"maps"/f"{map_id}_preview_240x160.png"; img.convert("P",palette=Image.Palette.ADAPTIVE,colors=64).convert("RGBA").save(p,optimize=True)
    grid=[1]*(30*20); collision=[]
    for ty in range(20):
        for tx in range(30): collision.append(1 if tx in (0,29) or ty in (0,19) else 0)
    meta={"schema":"jurai.phase28.map_asset.v1","id":map_id,"title":title,"preview":p.relative_to(ROOT).as_posix(),"screen":[240,160],"tile":[8,8],"grid":[30,20],"collision_layer":collision,"status":"draft_needs_tilemap_native_conversion"}
    jp=OUT/"maps"/f"{map_id}.json"; jp.write_text(json.dumps(meta,indent=2)+"\n",encoding="utf-8")
    return meta


def main() -> None:
    ensure()
    playable_records=[]
    enemy_records=[]
    portrait_records=[]
    for asset_id,name,color,forms in PLAYABLES:
        aura=(255,230,80) if forms else None
        sheet_path=OUT/"sprites"/"playable"/f"{asset_id}_native40_fullsheet.png"
        playable_records.append({"name":name,"forms":forms,**make_standard_sheet(asset_id,color,sheet_path,aura=aura)})
        portrait_records.append({"asset_id":asset_id,"portrait":make_portrait(asset_id,color)})
    for asset_id,name,source,color,role in ENEMIES:
        sheet_path=OUT/"sprites"/"enemies"/f"{asset_id}_{'72x72' if role=='large' else '40x40'}_sheet.png"
        enemy_records.append({"name":name,"source":source,**make_enemy_sheet(asset_id,color,role,sheet_path)})
        portrait_records.append({"asset_id":asset_id,"portrait":make_portrait(asset_id,color)})
    item_records=[{"id":item,"icon16":make_icon(item,OUT/"icons"/"items",(220,150,55),16),"icon32":make_icon(item,OUT/"icons"/"items",(220,150,55),32)} for item in ITEMS]
    tech_records=[{"id":tech,"icon16":make_icon(tech,OUT/"icons"/"techniques",(70,160,230),16),"icon32":make_icon(tech,OUT/"icons"/"techniques",(70,160,230),32)} for tech in TECHNIQUES]
    map_records=[make_map(*m) for m in MAPS]

    # Review queue
    queue_path=OUT/"review"/"phase28_asset_review_queue.csv"
    with queue_path.open("w",newline="",encoding="utf-8") as fp:
        fields=["asset_id","category","file","status","reviewer","notes"]
        w=csv.DictWriter(fp,fieldnames=fields); w.writeheader()
        for rec in playable_records: w.writerow({"asset_id":rec["asset_id"],"category":"playable_sheet","file":rec["sheet"],"status":"TODO_PIXEL_REVIEW","reviewer":"","notes":""})
        for rec in enemy_records: w.writerow({"asset_id":rec["asset_id"],"category":"enemy_sheet","file":rec["sheet"],"status":"TODO_PIXEL_REVIEW","reviewer":"","notes":""})
        for rec in portrait_records: w.writerow({"asset_id":rec["asset_id"],"category":"portrait","file":rec["portrait"],"status":"TODO_PIXEL_REVIEW","reviewer":"","notes":""})
        for rec in item_records: w.writerow({"asset_id":rec["id"],"category":"item_icon","file":rec["icon16"],"status":"TODO_PIXEL_REVIEW","reviewer":"","notes":""})
        for rec in tech_records: w.writerow({"asset_id":rec["id"],"category":"technique_icon","file":rec["icon16"],"status":"TODO_PIXEL_REVIEW","reviewer":"","notes":""})
        for rec in map_records: w.writerow({"asset_id":rec["id"],"category":"map_preview","file":rec["preview"],"status":"TODO_TILE_REVIEW","reviewer":"","notes":""})

    manifest={
        "schema":"jurai.phase28.missing_asset_kit.v1",
        "policy":"native_dimensions_draft_assets_needing_pixel_review",
        "counts":{"playable_sheets":len(playable_records),"enemy_sheets":len(enemy_records),"portraits":len(portrait_records),"item_icons":len(item_records),"technique_icons":len(tech_records),"maps":len(map_records)},
        "dimensions":{"standard_actor":[40,40],"large_boss":[72,72],"portrait":[40,40],"map":[240,160],"tile":[8,8]},
        "playables":playable_records,
        "enemies":enemy_records,
        "portraits":portrait_records,
        "items":item_records,
        "techniques":tech_records,
        "maps":map_records,
        "review_queue":queue_path.relative_to(ROOT).as_posix(),
        "final_art_warning":"These are draft assets in native dimensions. They are not final pixel-perfect art until manually reviewed and cleaned."
    }
    manifest_path=OUT/"phase28_missing_asset_kit_manifest.json"; manifest_path.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

    # Contact sheets for quick inspection
    def contact(paths, outname, title):
        thumbs=[]
        for p in paths:
            im=Image.open(ROOT/p).convert("RGBA"); im.thumbnail((80,80),Image.Resampling.NEAREST); thumbs.append((Path(p).stem,im))
        w=4*150; h=((len(thumbs)+3)//4)*105+24
        sheet=Image.new("RGBA",(w,h),(20,20,28,255)); d=ImageDraw.Draw(sheet); d.text((4,4),title,fill=(255,230,130,255))
        for i,(label,im) in enumerate(thumbs):
            x=(i%4)*150; y=24+(i//4)*105; sheet.alpha_composite(im,(x,y+18)); d.text((x,y),label[:18],fill=(240,240,255,255))
        op=OUT/"review"/outname; sheet.save(op,optimize=True); return op.relative_to(ROOT).as_posix()
    contact_play=contact([r["sheet"] for r in playable_records],"playable_contact.png","Playable draft sheets")
    contact_enemy=contact([r["sheet"] for r in enemy_records],"enemy_contact.png","Enemy/Boss draft sheets")
    contact_maps=contact([r["preview"] for r in map_records],"map_contact.png","Map draft previews")

    # Zip package
    ZIP_OUT.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(ZIP_OUT,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as zf:
        for p in sorted(OUT.rglob("*")):
            if p.is_file(): zf.write(p,p.relative_to(ROOT).as_posix())
    zip_sha=hashlib.sha1(ZIP_OUT.read_bytes()).hexdigest()
    DOC.write_text("\n".join([
        "# Phase 28 — Missing Asset Kit",
        "",
        "Generated a full native-dimension draft asset kit for the remaining project content.",
        "",
        "## Counts",
        "",
        f"- Playable sheets: {len(playable_records)}",
        f"- Enemy/boss sheets: {len(enemy_records)}",
        f"- Portraits: {len(portrait_records)}",
        f"- Item icons: {len(item_records)}",
        f"- Technique icons: {len(tech_records)}",
        f"- Map previews/manifests: {len(map_records)}",
        "",
        "## Native dimensions",
        "",
        "- Standard actor cells: 40×40",
        "- Large boss cells: 72×72",
        "- Portraits: 40×40",
        "- Icons: 16×16 and 32×32",
        "- Maps: 240×160 with 8×8 tile grid",
        "",
        "## Important",
        "",
        "These assets are draft/native-dimension templates. They are not final pixel-perfect art until manually reviewed and cleaned.",
        "",
        "## Outputs",
        "",
        f"- Manifest: `{manifest_path.relative_to(ROOT)}`",
        f"- Review queue: `{queue_path.relative_to(ROOT)}`",
        f"- Playable contact: `{contact_play}`",
        f"- Enemy contact: `{contact_enemy}`",
        f"- Map contact: `{contact_maps}`",
        f"- Zip: `{ZIP_OUT.relative_to(ROOT)}` SHA-1 `{zip_sha}`",
        "",
    ])+"\n",encoding="utf-8")
    PHASE_DOC.write_text("\n".join([
        "# Remaining phases to complete a seamless playable LOG4 experience",
        "",
        "After the Phase 28 missing-asset kit, the remaining work is mostly integration and polish.",
        "",
        "## Remaining major phases",
        "",
        "1. **Phase 29 — Pixel-art approval pass:** manually review/clean the Phase 28 sheets and mark assets READY_FOR_ROM_TEST.",
        "2. **Phase 30 — Native asset-bank insertion:** convert approved assets to the exact Webfoot containers/palettes and append them without replacing original content.",
        "3. **Phase 31 — Real Gateway interaction:** make Bubbles/Gate Guide open the actual Super/GT/AF/LOG1/LOG2 selection menu.",
        "4. **Phase 32 — First playable route:** connect one complete route (recommended GT Black Star intro or LOG2 dimension) with map -> NPC -> item -> battle -> return.",
        "5. **Phase 33 — Full route expansion:** add remaining Super, GT, AF, LOG1 and LOG2 chapters with enemies and maps.",
        "6. **Phase 34 — Save/flag integration:** map reserved flags into real save data safely with migration/fallback.",
        "7. **Phase 35 — Full QA/release:** mGBA/hardware-like testing, collision, saves, route completion and final IPS/BPS packaging.",
        "",
        "**Estimated remaining major phases: 7.**",
        "",
        "The next playable milestone is Phase 31/32: a real gateway interaction and one complete mini-route.",
    ])+"\n",encoding="utf-8")
    print(f"Wrote {manifest_path}")
    print(f"Wrote {ZIP_OUT} {zip_sha}")
    print(f"Wrote {DOC}")

if __name__ == "__main__":
    main()
