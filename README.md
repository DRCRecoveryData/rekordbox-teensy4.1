# DDJ-FLX4 Clean Fake — Teensy 4.1

Turn a Teensy 4.1 into a **Pioneer DDJ-FLX4** that rekordbox recognizes as a
genuine controller. Unlocks rekordbox's native controller / MIDI mode without
any physical buttons, faders, or encoders.

This is a **fake-only** build: the Teensy acts as a passive "license dongle."
It identifies itself to rekordbox, answers the handshake, and stays connected.
No outgoing MIDI, no LED feedback, no controls.

---

## ✨ What It Does

| Feature | Status |
| :--- | :---: |
| USB descriptor spoof (`2b73:0045`) | ✅ |
| Manufacturer / product name (`Pioneer DJ` / `DDJ-FLX4`) | ✅ |
| SysEx handshake response | ✅ |
| rekordbox MIDI mode unlock | ✅ |
| Physical buttons / faders / encoders | ❌ |
| LED feedback | ❌ |
| Outgoing MIDI from device | ❌ |

---

## 🧩 Requirements

### Hardware

- **Teensy 4.1** (Teensy 4.0 also works — change the board selection)
- USB cable (data-capable, not charge-only)
- Host computer:
  - Linux (Ubuntu / Debian / Arch tested)
  - macOS
  - Windows
- Windows VM (QEMU/KVM, VirtualBox, VMware) if you want to run rekordbox on
  a non-Windows host — Wine/Bottles **will not work** for USB passthrough.

### Software

- **Arduino IDE** 2.x with **Teensyduino** 1.59+ installed
- **Python 3.8+** (for the one-time `usb_desc.h` patch)
- **rekordbox** 6.6.6 or newer (FLX4 support started at 6.6.6)

---

## 🚀 Installation

### Step 1 — Install Teensyduino

1. Open Arduino IDE
2. **File → Preferences**
3. In *Additional boards manager URLs*, add:
   ```
   https://www.pjrc.com/teensy/package_teensy_index.json
   ```
4. **Tools → Board → Boards Manager** → search `teensy` → install latest

### Step 2 — Patch `usb_desc.h`

This changes the USB identity so the Teensy presents as a real Pioneer device.

**Linux / macOS:**
```bash
python3 patch_flx4.py
```

**Windows (PowerShell / CMD):**
```powershell
python patch_flx4.py
```

The script auto-detects the Teensy core path on all three platforms and creates
a `.bak` backup before modifying anything.

**To undo:**
```bash
python3 patch_flx4.py --restore
```

**To preview without changing anything:**
```bash
python3 patch_flx4.py --dry-run
```

Expected output:
```
Found: /home/user/.arduino15/packages/teensy/hardware/avr/1.62.0/cores/teensy4/usb_desc.h
Backup created: ...usb_desc.h.bak
Patched 6 lines
SUCCESS: usb_desc.h now spoofs Pioneer DDJ-FLX4
```

### Step 3 — Install udev rules (Linux only)

Skip on macOS / Windows.

```bash
wget https://www.pjrc.com/teensy/00-teensy.rules
sudo cp 00-teensy.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
```

Unplug and replug the Teensy.

### Step 4 — Configure Arduino IDE

| Setting | Value |
| :--- | :--- |
| Board | **Teensy 4.1** |
| USB Type | **MIDI** |
| CPU Speed | **600 MHz** |
| Optimize | Fastest |

> **Note:** After patching `usb_desc.h`, the Arduino IDE will no longer
> auto-detect the Teensy. Every upload now requires pressing the physical
> **Program** button on the board when the IDE prompts you.

### Step 5 — Upload the sketch

1. Open `DDJ_FLX4_Clean.ino` in Arduino IDE
2. Click **Upload**
3. When the IDE says *"Please press the PROGRAM MODE BUTTON on your Teensy"*,
   press the small button on the Teensy near the USB port
4. The upload completes, the board reboots, and re-enumerates as a DDJ-FLX4

---

## ✅ Verification

### Linux

```bash
lsusb | grep 2b73
```

Expected:
```
Bus 003 Device 018: ID 2b73:0045 Pioneer DJ DDJ-FLX4
```

Check ALSA MIDI:
```bash
aconnect -l
```

Expected:
```
client 24: 'DDJ-FLX4' [type=kernel,card=2]
    0 'DDJ-FLX4 MIDI 1 '
```

### macOS

```bash
system_profiler SPUSBDataType | grep -A5 FLX4
```

### Windows

Open **Device Manager** → look under *Sound, video and game controllers*
or *Universal Serial Bus devices*. You should see `Pioneer DJ DDJ-FLX4`.

### rekordbox

1. Launch rekordbox (in a Windows VM if you're on Linux/macOS)
2. The bottom status bar should show **DDJ-FLX4**
3. **Preferences → Controller** should list the DDJ-FLX4
4. The MIDI mode unlock banner should disappear

---

## 🐧 Running rekordbox on Linux

rekordbox is Windows/macOS only. On Linux, you have two options:

| Approach | USB passthrough | Works? |
| :--- | :---: | :---: |
| Wine / Bottles | ❌ | **No** — Wine lacks USB driver support |
| Windows VM (QEMU/KVM, VirtualBox) | ✅ | **Yes** |
| Dual-boot Windows | ✅ | **Yes** |

### QEMU/KVM + USB passthrough (recommended)

1. Install the stack:
   ```bash
   sudo apt install qemu-system-x86 libvirt-daemon-system virt-manager swtpm ovmf
   sudo usermod -aG kvm,libvirt $USER
   # log out and back in
   ```

2. Create a Windows VM in `virt-manager` with:
   - Firmware: **UEFI x86_64** + **Secure Boot**
   - Add Hardware → **TPM** (emulated)
   - Add Hardware → **USB Host Device** → select `2b73:0045 Pioneer DJ DDJ-FLX4`

3. Install rekordbox inside the VM.

4. Launch rekordbox — it should see the DDJ-FLX4.

---

## 🛠️ Troubleshooting

### "No Teensy boards were found" on upload

Expected after patching `usb_desc.h`. Press the physical **Program** button
on the Teensy when the IDE prompts you. You have ~8 seconds.

### `lsusb` shows `16c0:0485` instead of `2b73:0045`

The patch didn't take effect. Re-run `patch_flx4.py` and re-upload the sketch.

### `lsusb` shows nothing after upload

The board is in bootloader mode. Press Program, re-upload.

### rekordbox doesn't see the controller

- Confirm the USB device is passed through to the Windows VM
- Check **Device Manager** in Windows for `Pioneer DJ DDJ-FLX4`
- Make sure you're not running rekordbox under Wine — it will not work
- Try a different rekordbox version (6.8.4 is well-tested)

### rekordbox disconnects after a few minutes

rekordbox is sending a keep-alive SysEx your firmware isn't answering.
To diagnose:

1. Change **Tools → USB Type → Serial + MIDI**
2. Set `#define DEBUG_SYSEX 1` in the sketch
3. Re-upload
4. Open **Tools → Serial Monitor** (115200 baud)
5. Reproduce the disconnect — the last SysEx printed before the drop is
   the one that needs a reply
6. Add a matching response in `handleSysEx()`

### Connection drops after a Windows update

Windows Update may have reassigned the device. In the VM, check Device Manager
and re-run **Add Hardware → USB Host Device** in virt-manager.

---

## 📂 File Layout

```
.
├── DDJ_FLX4_Clean.ino     # Teensy 4.1 firmware (fake-only)
├── patch_flx4.py          # One-time usb_desc.h patcher
└── README.md              # This file
```

---

## ⚖️ Legal Notice

This project is intended for **personal, educational, and interoperability
research**. Emulating a USB device descriptor and responding to a SysEx query
is a technical exercise in USB/MIDI protocol understanding.

- **Do not** use this to violate any software license agreement.
- **Do not** distribute or sell hardware built from this code as a genuine
  Pioneer product.
- "Pioneer DJ", "DDJ-FLX4", and "rekordbox" are trademarks of their
  respective owners. This project is not affiliated with or endorsed by
  Pioneer DJ / AlphaTheta Corporation.
- The USB VID/PID used (`2b73:0045`) belongs to Pioneer DJ. Using it on
  non-Pioneer hardware may violate USB-IF assignment rules in some
  jurisdictions.

Use at your own risk. The authors assume no liability for any consequences
arising from the use of this software.

---

## 🙏 Credits

- **PJRC / Paul Stoffregen** — Teensy platform and Teensyduino core
- **Community researchers** — SysEx handshake reverse-engineering
- **Mixxx project** — DDJ-FLX4 MIDI map reference

---

## 📜 License

MIT License — see code headers for details.