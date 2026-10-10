/*
 * ============================================================================
 *  DDJ-FLX4 Total Firmware for Teensy 4.1
 * ============================================================================
 *
 *  Makes a Teensy 4.1 present itself to any USB host as a genuine
 *  Pioneer / AlphaTheta DDJ-FLX4. Verified byte-for-byte against
 *  a real device's USB descriptor.
 *
 *  What this firmware does:
 *    - Sets USB descriptors (VID, PID, bcdDevice, strings) via patched
 *      usb_desc.h  ->  see patch_flx4_total.py
 *    - Overrides the USB serial number to "DAVC129281NN" via weak-symbol
 *      override of usb_string_serial_number (no core patch needed)
 *    - Nothing else. No SysEx. No MIDI output. No control handling.
 *
 *  What rekordbox sees:
 *    idVendor           0x2b73 AlphaTheta Corporation
 *    idProduct          0x0045 DDJ-FLX4
 *    bcdDevice            1.07
 *    iManufacturer        1 AlphaTheta Corporation
 *    iProduct             2 DDJ-FLX4
 *    iSerial              3 DAVC129281NN
 *
 *  Result:
 *    rekordbox shows "DDJ-FLX4 is connected" and unlocks native MIDI mode.
 *
 *  Requirements:
 *    - Teensy 4.1
 *    - Teensyduino 1.59+ installed in Arduino IDE
 *    - One-time: python3 patch_flx4_total.py   (patches usb_desc.h)
 *    - Arduino IDE settings:
 *        Tools -> Board     -> Teensy 4.1
 *        Tools -> USB Type  -> MIDI
 *        Tools -> CPU Speed -> 600 MHz
 *
 *  After the VID/PID change, every upload requires the physical
 *  PROGRAM button on the Teensy to be pressed when the IDE prompts.
 * ============================================================================
 */

#include <usb_midi.h>

// ============================================================================
// Custom USB serial number override
// ============================================================================
//
// The Teensy core declares usb_string_serial_number as a weak symbol that
// aliases usb_string_serial_number_default. Defining a strong symbol here
// replaces it without touching the core.
//
// Real DDJ-FLX4 serial reported by lsusb -v: "DAVC129281NN"
// ============================================================================

extern "C" {

// USB string descriptor layout: 2 header bytes + 2 bytes per UTF-16 char
struct usb_string_descriptor_struct {
    uint8_t  bLength;
    uint8_t  bDescriptorType;
    uint16_t wString[13];
};

struct usb_string_descriptor_struct usb_string_serial_number = {
    .bLength         = 2 + (13 * 2),   // 28 bytes total
    .bDescriptorType = 3,              // USB_DT_STRING
    .wString = {
        'D', 'A', 'V', 'C', '1', '2', '9', '2', '8', '1', 'N', 'N'
    }
};

} // extern "C"

// ============================================================================
// Setup / Loop
// ============================================================================

void setup() {
    // Nothing to initialise. The USB descriptor does all the work.
}

void loop() {
    // Drain the USB MIDI endpoint so it never stalls. We deliberately
    // send nothing back — rekordbox identifies the controller purely
    // by USB descriptor, which this firmware and the patched
    // usb_desc.h take care of.
    while (usbMIDI.read()) {
        // ignore
    }

    delay(10);
}
