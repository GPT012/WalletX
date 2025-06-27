"""
熵生成模块测试
"""

import pytest

from src.core.entropy import EntropyGenerator, SecureBytes


class TestEntropyGenerator:
    """熵生成器测试类"""

    def test_generate_entropy_default(self):
        """测试默认熵生成"""
        entropy = EntropyGenerator.generate_entropy()
        assert len(entropy) == 32  # 256位 = 32字节
        assert isinstance(entropy, SecureBytes)

    def test_generate_entropy_different_lengths(self):
        """测试不同长度的熵生成"""
        test_cases = [(128, 16), (160, 20), (192, 24), (224, 28), (256, 32)]

        for bit_length, expected_bytes in test_cases:
            entropy = EntropyGenerator.generate_entropy(bit_length)
            assert len(entropy) == expected_bytes
            assert isinstance(entropy, SecureBytes)

    def test_generate_entropy_invalid_length(self):
        """测试无效长度的熵生成"""
        with pytest.raises(ValueError):
            EntropyGenerator.generate_entropy(100)

    def test_entropy_randomness(self):
        """测试熵的随机性"""
        entropy1 = EntropyGenerator.generate_entropy(256)
        entropy2 = EntropyGenerator.generate_entropy(256)

        # 两次生成的熵应该不同（比较字节内容）
        assert bytes(entropy1) != bytes(entropy2)

    def test_calculate_checksum(self):
        """测试校验和计算"""
        test_entropy = b"\x00" * 16  # 128位全零熵
        checksum = EntropyGenerator.calculate_checksum(test_entropy, 4)

        assert isinstance(checksum, int)
        assert 0 <= checksum <= 15  # 4位校验和的范围

    def test_get_checksum_bits(self):
        """测试校验和位数计算"""
        test_cases = [(128, 4), (160, 5), (192, 6), (224, 7), (256, 8)]

        for bit_length, expected_checksum_bits in test_cases:
            checksum_bits = EntropyGenerator.get_checksum_bits(bit_length)
            assert checksum_bits == expected_checksum_bits

    def test_entropy_to_binary(self):
        """测试熵转二进制"""
        test_entropy = b"\xff\x00"  # 11111111 00000000
        binary = EntropyGenerator.entropy_to_binary(test_entropy)

        assert binary == "1111111100000000"
        assert len(binary) == 16

    def test_add_checksum_to_entropy(self):
        """测试添加校验和"""
        test_entropy = b"\x00" * 16  # 128位全零熵
        result = EntropyGenerator.add_checksum_to_entropy(test_entropy)

        # 128位熵 + 4位校验和 = 132位
        assert len(result) == 132
        assert result.startswith("0" * 128)  # 前128位应该是0

    def test_validate_entropy_length(self):
        """测试熵长度验证"""
        valid_lengths = [128, 160, 192, 224, 256]
        invalid_lengths = [64, 100, 300]

        for length in valid_lengths:
            assert EntropyGenerator.validate_entropy_length(length) is True

        for length in invalid_lengths:
            assert EntropyGenerator.validate_entropy_length(length) is False
