#!/usr/bin/env python3
"""
================================================================================
 DDJ-FLX4 Total Patcher for Teensy usb_desc.h
================================================================================

 Patches the Teensy 4.x USB descriptor to fully match a real DDJ-FLX4.

 Fields patched or inserted:
   VENDOR_ID            0x2B73
   PRODUCT_ID           0x0045
   BCD_DEVICE           0x0107
   MANUFACTURER_NAME    "AlphaTheta Corporation"
   PRODUCT_NAME         "DDJ-FLX4"
   SERIAL_NUM           "DAVC129281NN"  (actual serial is applied in the .ino
                                         via weak-symbol override)

 Auto-detects Arduino15 path on Linux / macOS / Windows.
 Safe to re-run (restores from .bak first).

 Usage:
   python3 patch_flx4_total.py            # apply
   python3 patch_flx4_total.py --restore  # undo
   python3 patch_flx4_total.py --dry-run  # preview
================================================================================
"""

import os
import re
import sys
import glob
import shutil
import platform
import argparse


# ============================================================================
# Real DDJ-FLX4 descriptor values (from lsusb -v on genuine hardware)
# ============================================================================

FLX4 = {
    "VENDOR_ID":             "0x2B73",
    "PRODUCT_ID":            "0x0045",
    "BCD_DEVICE":            "0x0107",
    "MANUFACTURER_NAME":     "{'A','l','p','h','a','T','h','e','t','a',' ','C','o','r','p','o','r','a','t','i','o','n'}",
    "MANUFACTURER_NAME_LEN": "22",
    "PRODUCT_NAME":          "{'D','D','J','-','F','L','X','4'}",
    "PRODUCT_NAME_LEN":      "9",
    "SERIAL_NUM":            "{'D','A','V','C','1','2','9','2','8','1','N','N'}",
    "SERIAL_NUM_LEN":        "13",
}


# ============================================================================
# Locate usb_desc.h on any platform
# ============================================================================

def find_usb_desc():
    home = os.path.expanduser("~")
    system = platform.system()

    if system == "Windows":
        candidates = [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Arduino15"),
            os.path.join(home, "AppData", "Local", "Arduino15"),
        ]
    elif system == "Darwin":
        candidates = [
            os.path.join(home, "Library", "Arduino15"),
            os.path.join(home, ".arduino15"),
        ]
    else:
        candidates = [
            os.path.join(home, ".arduino15"),
            os.path.join(home, ".var", "app", "cc.arduino.arduinoide",
                         "data", "arduino15"),
        ]

    for base in candidates:
        pattern = os.path.join(base, "packages", "teensy", "hardware", "avr",
                               "*", "cores", "teensy4", "usb_desc.h")
        matches = glob.glob(pattern)
        if matches:
            return sorted(matches)[-1]
    return None


# ============================================================================
# Apply patch
# ============================================================================

def patch(path, dry_run=False):
    bak = path + ".bak"

    # --- Backup or restore ---
    if not os.path.exists(bak):
        if dry_run:
            print(f"[dry-run] Would create backup: {bak}")
        else:
            shutil.copy2(path, bak)
            print(f"Backup created: {bak}")
    else:
        if dry_run:
            print(f"[dry-run] Would restore from: {bak}")
        else:
            shutil.copy2(bak, path)
            print(f"Restored from: {bak}")

    # --- Read ---
    with open(path, "r", encoding="utf-8", errors="surrogateescape") as f:
        lines = f.readlines()

    # --- Locate USB_MIDI block ---
    start = end = None
    for i, line in enumerate(lines):
        if re.match(r"^#elif defined\(USB_MIDI\)\s*$", line):
            start = i
            for j in range(i + 1, len(lines)):
                if (lines[j].startswith("#elif") or
                        lines[j].startswith("#else") or
                        lines[j].startswith("#endif")):
                    end = j
                    break
            break

    if start is None or end is None:
        print("ERROR: USB_MIDI block not found in usb_desc.h")
        return 0

    print(f"USB_MIDI block: lines {start + 1}\u2013{end}")

    # --- Pass 1: replace existing defines ---
    replaced = 0
    for i in range(start, end):
        for key, val in FLX4.items():
            if re.match(rf"^\s*#define\s+{key}\b", lines[i]):
                lines[i] = f"  #define {key}\t\t{val}\n"
                replaced += 1
                break

    # --- Pass 2: insert BCD_DEVICE after PRODUCT_ID ---
    inserted = 0
    block_text = "".join(lines[start:end])
    if "#define BCD_DEVICE" not in block_text:
        for i in range(start, end):
            if re.match(r"^\s*#define\s+PRODUCT_ID\b", lines[i]):
                lines.insert(i + 1,
                             f"  #define BCD_DEVICE\t\t{FLX4['BCD_DEVICE']}\n")
                end += 1
                inserted += 1
                print("Inserted BCD_DEVICE")
                break

    # --- Pass 3: insert SERIAL_NUM after PRODUCT_NAME_LEN ---
    block_text = "".join(lines[start:end])
    if "#define SERIAL_NUM" not in block_text:
        for i in range(start, end):
            if re.match(r"^\s*#define\s+PRODUCT_NAME_LEN\b", lines[i]):
                lines.insert(i + 1,
                             f"  #define SERIAL_NUM\t\t{FLX4['SERIAL_NUM']}\n")
                lines.insert(i + 2,
                             f"  #define SERIAL_NUM_LEN\t{FLX4['SERIAL_NUM_LEN']}\n")
                end += 2
                inserted += 2
                print("Inserted SERIAL_NUM + SERIAL_NUM_LEN")
                break

    # --- Write ---
    if dry_run:
        print(f"[dry-run] Would replace {replaced}, insert {inserted}")
        return replaced + inserted

    with open(path, "w", encoding="utf-8", errors="surrogateescape") as f:
        f.writelines(lines)

    return replaced + inserted


# ============================================================================
# Restore from backup
# ============================================================================

def restore(path):
    bak = path + ".bak"
    if not os.path.exists(bak):
        print(f"No backup found: {bak}")
        return False
    shutil.copy2(bak, path)
    print(f"Restored original from: {bak}")
    return True


# ============================================================================
# Verify with regex (handles any whitespace between define and value)
# ============================================================================

def verify(path):
    with open(path, "r", encoding="utf-8", errors="surrogateescape") as f:
        c = f.read()

    checks = [
        ("VENDOR_ID",             r"#define\s+VENDOR_ID\s+0x2B73"),
        ("PRODUCT_ID",            r"#define\s+PRODUCT_ID\s+0x0045"),
        ("BCD_DEVICE",            r"#define\s+BCD_DEVICE\s+0x0107"),
        ("MANUFACTURER_NAME",     r"'A','l','p','h','a','T','h','e','t','a'"),
        ("MANUFACTURER_NAME_LEN", r"#define\s+MANUFACTURER_NAME_LEN\s+22"),
        ("PRODUCT_NAME",          r"'D','D','J','-','F','L','X','4'"),
        ("PRODUCT_NAME_LEN",      r"#define\s+PRODUCT_NAME_LEN\s+9"),
        ("SERIAL_NUM",            r"'D','A','V','C','1','2','9','2','8','1','N','N'"),
        ("SERIAL_NUM_LEN",        r"#define\s+SERIAL_NUM_LEN\s+13"),
    ]

    print("\nDescriptor verification:")
    print("\u2500" * 52)
    all_ok = True
    for name, pat in checks:
        ok = re.search(pat, c) is not None
        print(f"  {'OK  ' if ok else 'MISS'}  {name}")
        all_ok = all_ok and ok
    print("\u2500" * 52)

    if all_ok:
        print("SUCCESS: usb_desc.h fully matches Pioneer DDJ-FLX4")
    else:
        print("WARNING: some fields are still missing")
    return all_ok


# ============================================================================
# Main
# ============================================================================

def main():
    ap = argparse.ArgumentParser(
        description="Patch Teensy usb_desc.h to fully match a DDJ-FLX4")
    ap.add_argument("--restore", action="store_true",
                    help="restore original from .bak")
    ap.add_argument("--dry-run", action="store_true",
                    help="preview without writing")
    args = ap.parse_args()

    path = find_usb_desc()
    if not path:
        print("ERROR: usb_desc.h not found. Is Teensyduino installed?")
        sys.exit(1)

    print(f"Found: {path}\n")

    if args.restore:
        restore(path)
        return

    n = patch(path, dry_run=args.dry_run)
    print(f"\nPatched/inserted {n} lines total")

    if not args.dry_run:
        ok = verify(path)

        print("\nFinal USB_MIDI block:")
        print("\u2500" * 52)
        with open(path, "r", encoding="utf-8",
                  errors="surrogateescape") as f:
            content = f.read()
        m = re.search(
            r"(#elif defined\(USB_MIDI\).*?)(?=\n#elif|\n#else|\n#endif)",
            content, re.DOTALL)
        if m:
            for line in m.group(1).splitlines()[:12]:
                print(line)
        print("\u2500" * 52)

        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
