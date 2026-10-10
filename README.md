# DDJ-FLX4 — Teensy 4.1

A Teensy 4.1 that presents itself to any USB host as a genuine
**Pioneer / AlphaTheta DDJ-FLX4**, with a byte-for-byte USB descriptor
match confirmed against a real device.

rekordbox recognizes it instantly and unlocks native MIDI mode.

---

## Verified Descriptor Match

Confirmed with `lsusb -v` on Linux against both a real FLX4 and this build:

| Field | Real FLX4 | Teensy 4.1 | Match |
| :--- | :--- | :--- | :---: |
| `idVendor` | `0x2b73` AlphaTheta Corporation | `0x2b73` AlphaTheta Corporation | ✅ |
| `idProduct` | `0x0045` DDJ-FLX4 | `0x0045` DDJ-FLX4 | ✅ |
| `bcdDevice` | `1.07` | `1.07` | ✅ |
| `iManufacturer` | AlphaTheta Corporation | AlphaTheta Corporation | ✅ |
| `iProduct` | DDJ-FLX4 | DDJ-FLX4 | ✅ |
| `iSerial` | DAVC129281NN | DAVC129281NN | ✅ |

---

## What This Cannot Match

The real FLX4 exposes **7 USB interfaces**. The Teensy exposes **1** (MIDI only).
Matching the full interface tree would require rewriting the Teensy USB core.

| Feature | Real FLX4 | Teensy | Needed by rekordbox? |
| :--- | :--- | :--- | :---: |
| USB interfaces | 7 | 1 | ❌ No |
| USB Audio class | Yes | No | ❌ No |
| HID interface | Yes | No | ❌ No |
| Mass storage | Yes | No | ❌ No |
| MaxPower | 500 mA | 100 mA | ❌ No |

**Verified experimentally:** a sketch with no SysEx handler and no MIDI
output is still detected by rekordbox as "DDJ-FLX4 connected" with MIDI
mode unlocked. rekordbox checks only VID/PID.

---

## Why This Works

rekordbox identifies supported controllers by **USB descriptor alone**.
The community's documented SysEx handshake is not required for recognition
— it's a MIDI-only fallback that isn't even sent by a real FLX4.

This project therefore reduces the emulator to its minimum:

1. Patch the USB descriptor (`patch_flx4_total.py`)
2. Upload the firmware (`DDJ_FLX4_Total.ino`)
3. Plug in, launch rekordbox

No SysEx. No MIDI output. No CC state dump. No physical controls.

---

## Files

```
.
├── DDJ_FLX4_Total.ino      # Teensy 4.1 firmware (with serial override)
├── patch_flx4_total.py     # One-time usb_desc.h patcher
└── README.md               # This file
```

---

## Requirements

### Hardware
- **Teensy 4.1**
- USB data cable (not charge-only)
- Host: Linux, macOS, or Windows
- For rekordbox on Linux: **Windows VM** with USB passthrough
  (Wine/Bottles cannot pass USB devices)

### Software
- **Arduino IDE** 2.x
- **Teensyduino** 1.59 or newer
- **Python 3.8+**
- **rekordbox** 6.6.6 or newer (FLX4 support starts at 6.6.6)

---

## Installation

### 1. Install Teensyduino

1. Arduino IDE → **File → Preferences**
2. Under *Additional boards manager URLs*, add:
   ```
   https://www.pjrc.com/teensy/package_teensy_index.json
   ```
3. **Tools → Board → Boards Manager** → search `teensy` → install latest

### 2. Patch `usb_desc.h`

```bash
python3 patch_flx4_total.py
```

Expected output:

```
Found: /home/user/.arduino15/packages/teensy/hardware/avr/1.62.0/cores/teensy4/usb_desc.h
Backup created: ...usb_desc.h.bak
USB_MIDI block: lines 502–515
Inserted BCD_DEVICE
Inserted SERIAL_NUM + SERIAL_NUM_LEN
Patched/inserted 9 lines total

Descriptor verification:
────────────────────────────────────────────────────
  OK    VENDOR_ID
  OK    PRODUCT_ID
  OK    BCD_DEVICE
  OK    MANUFACTURER_NAME
  OK    MANUFACTURER_NAME_LEN
  OK    PRODUCT_NAME
  OK    PRODUCT_NAME_LEN
  OK    SERIAL_NUM
  OK    SERIAL_NUM_LEN
────────────────────────────────────────────────────
SUCCESS: usb_desc.h fully matches Pioneer DDJ-FLX4
```

**Undo:**
```bash
python3 patch_flx4_total.py --restore
```

**Preview without writing:**
```bash
python3 patch_flx4_total.py --dry-run
```

### 3. Clean the Arduino build cache

Required — the Teensy core must be recompiled after `usb_desc.h` changes:

```bash
rm -rf ~/.cache/arduino/sketches/*
rm -rf /tmp/arduino_build_*
```

### 4. Upload the firmware

1. Open `DDJ_FLX4_Total.ino` in Arduino IDE
2. **Tools → Board → Teensy 4.1**
3. **Tools → USB Type → MIDI**
4. **Tools → CPU Speed → 600 MHz**
5. Click **Upload**
6. When the IDE prompts *"Please press the PROGRAM MODE BUTTON on your
   Teensy"*, press the small button on the board

> After the VID/PID change, every upload requires the physical Program
> button. The IDE will no longer auto-detect the board.

### 5. Linux udev rules (Linux hosts only)

```bash
wget https://www.pjrc.com/teensy/00-teensy.rules
sudo cp 00-teensy.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
```

Unplug and replug the Teensy.

---

## Verification

### Linux

```bash
lsusb -v -d 2b73:0045 2>/dev/null | \
  grep -E "idVendor|idProduct|bcdDevice|iManufacturer|iProduct|iSerial"
```

Expected output:

```
idVendor           0x2b73 AlphaTheta Corporation
idProduct          0x0045 DDJ-FLX4
bcdDevice            1.07
iManufacturer        1 AlphaTheta Corporation
iProduct             2 DDJ-FLX4
iSerial              3 DAVC129281NN
```

### macOS

```bash
system_profiler SPUSBDataType | grep -A6 "DDJ-FLX4"
```

### Windows

Open **Device Manager** → look for `AlphaTheta Corporation DDJ-FLX4`
under *Sound, video and game controllers* or *Universal Serial Bus devices*.

### rekordbox

Launch rekordbox with the Teensy connected. The bottom status bar shows
**"DDJ-FLX4 is connected"** and native MIDI mode is unlocked.

---

## Running rekordbox on Linux

rekordbox is Windows/macOS only. On Linux you have three options:

| Approach | USB passthrough | Works? |
| :--- | :---: | :---: |
| Wine / Bottles | ❌ | **No** — Wine cannot pass USB devices |
| Windows VM (QEMU/KVM, VirtualBox) | ✅ | **Yes** |
| Dual-boot Windows | ✅ | **Yes** |

### QEMU/KVM setup (recommended)

```bash
sudo apt install qemu-system-x86 libvirt-daemon-system \
                 virt-manager swtpm ovmf
sudo usermod -aG kvm,libvirt $USER
# log out and back in
```

In `virt-manager`, when creating the Windows VM:

1. Firmware → **UEFI x86_64** with **Secure Boot**
2. Add Hardware → **TPM** (emulated)
3. Add Hardware → **USB Host Device** →
   `2b73:0045 AlphaTheta Corporation DDJ-FLX4`

Install rekordbox inside the VM. It will detect the controller.

---

## Troubleshooting

| Symptom | Cause | Fix |
| :--- | :--- | :--- |
| `lsusb` shows `16c0:xxxx` after upload | Stale build cache | Clean build folder, re-upload |
| "No Teensy boards were found" on upload | VID changed | Press Program button when prompted |
| `patch_flx4_total.py` reports MISS | Whitespace in verifier | Cosmetic — check block manually |
| `iSerial` shows chip UID | Weak override not compiled | Re-clean cache, re-upload |
| rekordbox doesn't see controller | USB not passed to VM | Check virt-manager USB Host Device |

---

## Legal Notice

"Pioneer DJ", "AlphaTheta", "DDJ-FLX4", and "rekordbox" are trademarks of
AlphaTheta Corporation. This project is for **personal, educational, and
interoperability research** only.

- Do not sell or distribute hardware built from this code as genuine
  Pioneer product.
- The USB VID/PID used (`0x2b73:0x0045`) belongs to AlphaTheta Corporation.
  Using it on non-AlphaTheta hardware may violate USB-IF assignment rules
  in some jurisdictions.

Use at your own risk. The authors assume no liability for any consequences
arising from the use of this software.

---

## License

MIT
