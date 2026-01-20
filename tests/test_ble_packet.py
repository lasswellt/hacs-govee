"""Test BLE packet builder."""

from __future__ import annotations

import base64

import pytest

from custom_components.govee.api.ble_packet import (
    DIY_COMMAND,
    DIY_PACKET_ID,
    DIY_STYLE_NAMES,
    DIYStyle,
    MUSIC_MODE_COMMAND,
    MUSIC_MODE_INDICATOR,
    MUSIC_PACKET_PREFIX,
    build_diy_speed_packet,
    build_diy_style_packet,
    build_music_mode_packet,
    build_packet,
    calculate_checksum,
    encode_packet_base64,
)


# ==============================================================================
# Checksum Tests
# ==============================================================================


class TestCalculateChecksum:
    """Test XOR checksum calculation."""

    def test_empty_list(self):
        """Test checksum of empty list."""
        assert calculate_checksum([]) == 0

    def test_single_byte(self):
        """Test checksum of single byte."""
        assert calculate_checksum([0xA1]) == 0xA1

    def test_two_bytes(self):
        """Test checksum of two bytes."""
        # 0xA1 ^ 0x02 = 0xA3
        assert calculate_checksum([0xA1, 0x02]) == 0xA3

    def test_multiple_bytes(self):
        """Test checksum of multiple bytes."""
        # XOR chain: A1 ^ 02 ^ 01 ^ 00 ^ 00 ^ 32
        data = [0xA1, 0x02, 0x01, 0x00, 0x00, 0x32]
        result = 0
        for b in data:
            result ^= b
        assert calculate_checksum(data) == result

    def test_all_zeros(self):
        """Test checksum of all zeros."""
        assert calculate_checksum([0x00, 0x00, 0x00]) == 0

    def test_all_ff(self):
        """Test checksum of all 0xFF."""
        # FF ^ FF ^ FF = FF (odd number of 0xFF)
        assert calculate_checksum([0xFF, 0xFF, 0xFF]) == 0xFF
        # FF ^ FF = 0 (even number)
        assert calculate_checksum([0xFF, 0xFF]) == 0

    def test_result_masked_to_byte(self):
        """Test that result is masked to 8 bits."""
        # Even with large intermediate values, result should be 0-255
        result = calculate_checksum([0xFF, 0x01])
        assert 0 <= result <= 255


# ==============================================================================
# Packet Builder Tests
# ==============================================================================


class TestBuildPacket:
    """Test packet building."""

    def test_packet_always_20_bytes(self):
        """Test that packets are always exactly 20 bytes."""
        # Short data
        packet = build_packet([0xA1])
        assert len(packet) == 20

        # Medium data
        packet = build_packet([0xA1, 0x02, 0x01, 0x00, 0x00, 0x50])
        assert len(packet) == 20

        # Full data (19 bytes)
        packet = build_packet([0x00] * 19)
        assert len(packet) == 20

    def test_packet_is_bytes(self):
        """Test that packet is returned as bytes."""
        packet = build_packet([0xA1, 0x02])
        assert isinstance(packet, bytes)

    def test_data_preserved(self):
        """Test that input data is preserved in packet."""
        data = [0xA1, 0x02, 0x01, 0x00, 0x00, 0x50]
        packet = build_packet(data)
        for i, byte in enumerate(data):
            assert packet[i] == byte

    def test_padding_with_zeros(self):
        """Test that short data is padded with zeros."""
        data = [0xA1, 0x02]
        packet = build_packet(data)

        # First two bytes are data
        assert packet[0] == 0xA1
        assert packet[1] == 0x02

        # Bytes 2-18 should be zero padding
        for i in range(2, 19):
            assert packet[i] == 0x00

    def test_checksum_at_end(self):
        """Test that checksum is at byte 19."""
        data = [0xA1, 0x02, 0x01, 0x00, 0x00, 0x50]
        packet = build_packet(data)

        # Calculate expected checksum (of first 19 bytes)
        padded = data + [0x00] * (19 - len(data))
        expected_checksum = calculate_checksum(padded)

        assert packet[19] == expected_checksum

    def test_truncates_long_data(self):
        """Test that data longer than 19 bytes is truncated."""
        data = list(range(25))  # 25 bytes
        packet = build_packet(data)

        assert len(packet) == 20
        # First 19 bytes should be 0-18
        for i in range(19):
            assert packet[i] == i


# ==============================================================================
# DIY Speed Packet Tests
# ==============================================================================


class TestBuildDiySpeedPacket:
    """Test DIY speed packet building."""

    def test_packet_length(self):
        """Test DIY speed packet is 20 bytes."""
        packet = build_diy_speed_packet(50)
        assert len(packet) == 20

    def test_packet_header(self):
        """Test DIY speed packet has correct header."""
        packet = build_diy_speed_packet(50)

        # Byte 0: DIY packet ID (0xA1)
        assert packet[0] == DIY_PACKET_ID
        assert packet[0] == 0xA1

        # Byte 1: DIY command (0x02)
        assert packet[1] == DIY_COMMAND
        assert packet[1] == 0x02

    def test_speed_byte_position(self):
        """Test speed value is at correct position (byte 5)."""
        packet = build_diy_speed_packet(75)
        assert packet[5] == 75

    def test_speed_zero(self):
        """Test speed 0 (static, no animation)."""
        packet = build_diy_speed_packet(0)
        assert packet[5] == 0

    def test_speed_max(self):
        """Test speed 100 (fastest)."""
        packet = build_diy_speed_packet(100)
        assert packet[5] == 100

    def test_speed_clamped_below(self):
        """Test speed below 0 is clamped to 0."""
        packet = build_diy_speed_packet(-10)
        assert packet[5] == 0

    def test_speed_clamped_above(self):
        """Test speed above 100 is clamped to 100."""
        packet = build_diy_speed_packet(150)
        assert packet[5] == 100

    def test_intermediate_bytes(self):
        """Test intermediate bytes have correct values."""
        packet = build_diy_speed_packet(50)

        # Byte 2: Number of segments/modes (0x01)
        assert packet[2] == 0x01

        # Byte 3: Style (0x00)
        assert packet[3] == 0x00

        # Byte 4: Mode (0x00)
        assert packet[4] == 0x00

    def test_valid_checksum(self):
        """Test packet has valid checksum."""
        packet = build_diy_speed_packet(50)

        # Recalculate checksum from first 19 bytes
        expected_checksum = calculate_checksum(list(packet[:19]))
        assert packet[19] == expected_checksum


# ==============================================================================
# Base64 Encoding Tests
# ==============================================================================


class TestEncodePacketBase64:
    """Test Base64 packet encoding."""

    def test_encodes_to_string(self):
        """Test that encoding returns a string."""
        packet = build_diy_speed_packet(50)
        encoded = encode_packet_base64(packet)
        assert isinstance(encoded, str)

    def test_ascii_only(self):
        """Test that encoded string is ASCII."""
        packet = build_diy_speed_packet(50)
        encoded = encode_packet_base64(packet)
        assert encoded.isascii()

    def test_valid_base64(self):
        """Test that encoded string is valid Base64."""
        packet = build_diy_speed_packet(50)
        encoded = encode_packet_base64(packet)

        # Should be decodable
        decoded = base64.b64decode(encoded)
        assert decoded == packet

    def test_round_trip(self):
        """Test encoding and decoding round trip."""
        for speed in [0, 25, 50, 75, 100]:
            packet = build_diy_speed_packet(speed)
            encoded = encode_packet_base64(packet)
            decoded = base64.b64decode(encoded)
            assert decoded == packet

    def test_consistent_encoding(self):
        """Test that same packet produces same encoding."""
        packet = build_diy_speed_packet(50)
        encoded1 = encode_packet_base64(packet)
        encoded2 = encode_packet_base64(packet)
        assert encoded1 == encoded2

    def test_expected_length(self):
        """Test that Base64 encoding has expected length.

        20 bytes -> ceil(20 * 4 / 3) = 28 characters (with padding)
        """
        packet = build_diy_speed_packet(50)
        encoded = encode_packet_base64(packet)
        assert len(encoded) == 28


# ==============================================================================
# Integration Tests
# ==============================================================================


class TestDiySpeedPacketIntegration:
    """Integration tests for DIY speed packet generation."""

    def test_full_workflow(self):
        """Test complete packet generation workflow."""
        speed = 75

        # Build packet
        packet = build_diy_speed_packet(speed)
        assert len(packet) == 20

        # Encode for transmission
        encoded = encode_packet_base64(packet)
        assert isinstance(encoded, str)

        # Verify can be decoded back
        decoded = base64.b64decode(encoded)
        assert decoded == packet
        assert decoded[5] == speed

    @pytest.mark.parametrize("speed", [0, 25, 50, 75, 100])
    def test_various_speeds(self, speed: int):
        """Test packet generation for various speed values."""
        packet = build_diy_speed_packet(speed)

        # Verify header
        assert packet[0] == 0xA1
        assert packet[1] == 0x02

        # Verify speed
        assert packet[5] == speed

        # Verify checksum
        expected_checksum = calculate_checksum(list(packet[:19]))
        assert packet[19] == expected_checksum


# ==============================================================================
# DIY Style Packet Tests
# ==============================================================================


class TestDIYStyleEnum:
    """Test DIYStyle enum and mappings."""

    def test_style_values(self):
        """Test DIY style enum values."""
        assert DIYStyle.FADE == 0x00
        assert DIYStyle.JUMPING == 0x01
        assert DIYStyle.FLICKER == 0x02
        assert DIYStyle.MARQUEE == 0x03
        assert DIYStyle.MUSIC == 0x04

    def test_style_names_mapping(self):
        """Test style name to enum mapping."""
        assert DIY_STYLE_NAMES["Fade"] == DIYStyle.FADE
        assert DIY_STYLE_NAMES["Jumping"] == DIYStyle.JUMPING
        assert DIY_STYLE_NAMES["Flicker"] == DIYStyle.FLICKER
        assert DIY_STYLE_NAMES["Marquee"] == DIYStyle.MARQUEE
        assert DIY_STYLE_NAMES["Music"] == DIYStyle.MUSIC

    def test_all_styles_mapped(self):
        """Test all styles have name mappings."""
        assert len(DIY_STYLE_NAMES) == 5


class TestBuildDiyStylePacket:
    """Test DIY style packet building."""

    def test_packet_length(self):
        """Test DIY style packet is 20 bytes."""
        packet = build_diy_style_packet(DIYStyle.FADE, 50)
        assert len(packet) == 20

    def test_packet_header(self):
        """Test DIY style packet has correct header."""
        packet = build_diy_style_packet(DIYStyle.JUMPING, 50)

        # Byte 0: DIY packet ID (0xA1)
        assert packet[0] == DIY_PACKET_ID
        assert packet[0] == 0xA1

        # Byte 1: DIY command (0x02)
        assert packet[1] == DIY_COMMAND
        assert packet[1] == 0x02

    def test_style_byte_position(self):
        """Test style value is at correct position (byte 3)."""
        packet = build_diy_style_packet(DIYStyle.MARQUEE, 50)
        assert packet[3] == DIYStyle.MARQUEE
        assert packet[3] == 0x03

    def test_speed_byte_position(self):
        """Test speed value is at correct position (byte 5)."""
        packet = build_diy_style_packet(DIYStyle.FADE, 75)
        assert packet[5] == 75

    @pytest.mark.parametrize(
        "style,expected",
        [
            (DIYStyle.FADE, 0x00),
            (DIYStyle.JUMPING, 0x01),
            (DIYStyle.FLICKER, 0x02),
            (DIYStyle.MARQUEE, 0x03),
            (DIYStyle.MUSIC, 0x04),
        ],
    )
    def test_all_styles(self, style: DIYStyle, expected: int):
        """Test packet generation for all styles."""
        packet = build_diy_style_packet(style, 50)
        assert packet[3] == expected

    def test_style_from_int(self):
        """Test style from integer value."""
        packet = build_diy_style_packet(2, 50)  # Flicker
        assert packet[3] == 0x02

    def test_style_clamped_below(self):
        """Test style below 0 is clamped to 0."""
        packet = build_diy_style_packet(-1, 50)
        assert packet[3] == 0

    def test_style_clamped_above(self):
        """Test style above 4 is clamped to 4."""
        packet = build_diy_style_packet(10, 50)
        assert packet[3] == 4

    def test_speed_clamped_below(self):
        """Test speed below 0 is clamped to 0."""
        packet = build_diy_style_packet(DIYStyle.FADE, -10)
        assert packet[5] == 0

    def test_speed_clamped_above(self):
        """Test speed above 100 is clamped to 100."""
        packet = build_diy_style_packet(DIYStyle.FADE, 150)
        assert packet[5] == 100

    def test_intermediate_bytes(self):
        """Test intermediate bytes have correct values."""
        packet = build_diy_style_packet(DIYStyle.JUMPING, 50)

        # Byte 2: Number of segments/modes (0x01)
        assert packet[2] == 0x01

        # Byte 4: Mode (0x00)
        assert packet[4] == 0x00

    def test_valid_checksum(self):
        """Test packet has valid checksum."""
        packet = build_diy_style_packet(DIYStyle.FLICKER, 50)

        # Recalculate checksum from first 19 bytes
        expected_checksum = calculate_checksum(list(packet[:19]))
        assert packet[19] == expected_checksum


# ==============================================================================
# Music Mode Packet Tests
# ==============================================================================


class TestBuildMusicModePacket:
    """Test music mode packet building."""

    def test_packet_length(self):
        """Test music mode packet is 20 bytes."""
        packet = build_music_mode_packet(True, 50)
        assert len(packet) == 20

    def test_packet_header(self):
        """Test music mode packet has correct header."""
        packet = build_music_mode_packet(True, 50)

        # Byte 0: Standard command prefix (0x33)
        assert packet[0] == MUSIC_PACKET_PREFIX
        assert packet[0] == 0x33

        # Byte 1: Music mode command (0x05)
        assert packet[1] == MUSIC_MODE_COMMAND
        assert packet[1] == 0x05

        # Byte 2: Music mode indicator (0x01)
        assert packet[2] == MUSIC_MODE_INDICATOR
        assert packet[2] == 0x01

    def test_enabled_byte_position(self):
        """Test enabled value is at correct position (byte 3)."""
        packet_on = build_music_mode_packet(True, 50)
        assert packet_on[3] == 0x01

        packet_off = build_music_mode_packet(False, 50)
        assert packet_off[3] == 0x00

    def test_sensitivity_byte_position(self):
        """Test sensitivity value is at correct position (byte 4)."""
        packet = build_music_mode_packet(True, 75)
        assert packet[4] == 75

    def test_enabled_on(self):
        """Test music mode enabled packet."""
        packet = build_music_mode_packet(True, 50)
        assert packet[3] == 0x01

    def test_enabled_off(self):
        """Test music mode disabled packet."""
        packet = build_music_mode_packet(False, 50)
        assert packet[3] == 0x00

    def test_sensitivity_zero(self):
        """Test sensitivity 0 (minimum)."""
        packet = build_music_mode_packet(True, 0)
        assert packet[4] == 0

    def test_sensitivity_max(self):
        """Test sensitivity 100 (maximum)."""
        packet = build_music_mode_packet(True, 100)
        assert packet[4] == 100

    def test_sensitivity_clamped_below(self):
        """Test sensitivity below 0 is clamped to 0."""
        packet = build_music_mode_packet(True, -10)
        assert packet[4] == 0

    def test_sensitivity_clamped_above(self):
        """Test sensitivity above 100 is clamped to 100."""
        packet = build_music_mode_packet(True, 150)
        assert packet[4] == 100

    def test_default_sensitivity(self):
        """Test default sensitivity value."""
        packet = build_music_mode_packet(True)
        assert packet[4] == 50

    def test_valid_checksum(self):
        """Test packet has valid checksum."""
        packet = build_music_mode_packet(True, 50)

        # Recalculate checksum from first 19 bytes
        expected_checksum = calculate_checksum(list(packet[:19]))
        assert packet[19] == expected_checksum

    @pytest.mark.parametrize("sensitivity", [0, 25, 50, 75, 100])
    def test_various_sensitivities(self, sensitivity: int):
        """Test packet generation for various sensitivity values."""
        packet = build_music_mode_packet(True, sensitivity)

        # Verify header
        assert packet[0] == 0x33
        assert packet[1] == 0x05
        assert packet[2] == 0x01

        # Verify sensitivity
        assert packet[4] == sensitivity

        # Verify checksum
        expected_checksum = calculate_checksum(list(packet[:19]))
        assert packet[19] == expected_checksum


# ==============================================================================
# Integration Tests for New Packet Types
# ==============================================================================


class TestDiyStylePacketIntegration:
    """Integration tests for DIY style packet generation."""

    def test_full_workflow(self):
        """Test complete DIY style packet generation workflow."""
        style = DIYStyle.MARQUEE
        speed = 75

        # Build packet
        packet = build_diy_style_packet(style, speed)
        assert len(packet) == 20

        # Encode for transmission
        encoded = encode_packet_base64(packet)
        assert isinstance(encoded, str)

        # Verify can be decoded back
        decoded = base64.b64decode(encoded)
        assert decoded == packet
        assert decoded[3] == style
        assert decoded[5] == speed


class TestMusicModePacketIntegration:
    """Integration tests for music mode packet generation."""

    def test_full_workflow_on(self):
        """Test complete music mode ON packet generation workflow."""
        # Build packet
        packet = build_music_mode_packet(True, 75)
        assert len(packet) == 20

        # Encode for transmission
        encoded = encode_packet_base64(packet)
        assert isinstance(encoded, str)

        # Verify can be decoded back
        decoded = base64.b64decode(encoded)
        assert decoded == packet
        assert decoded[3] == 0x01  # Enabled
        assert decoded[4] == 75  # Sensitivity

    def test_full_workflow_off(self):
        """Test complete music mode OFF packet generation workflow."""
        # Build packet
        packet = build_music_mode_packet(False, 50)
        assert len(packet) == 20

        # Encode for transmission
        encoded = encode_packet_base64(packet)
        assert isinstance(encoded, str)

        # Verify can be decoded back
        decoded = base64.b64decode(encoded)
        assert decoded == packet
        assert decoded[3] == 0x00  # Disabled
        assert decoded[4] == 50  # Sensitivity
