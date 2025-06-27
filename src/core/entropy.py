"""
熵生成模块
负责生成加密安全的随机熵，用于助记词生成
"""

import ctypes
import hashlib
import secrets


class SecureBytes:
    """安全字节类，确保在析构时清零内存"""

    def __init__(self, data: bytes):
        self._data = bytearray(data)
        self._ptr = ctypes.cast(
            ctypes.pointer(ctypes.c_char_p(bytes(self._data))),
            ctypes.POINTER(ctypes.c_char),
        )

    def __bytes__(self) -> bytes:
        return bytes(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __del__(self):
        """析构时安全清零内存"""
        if hasattr(self, "_data"):
            # 使用随机数据覆盖
            for i in range(len(self._data)):
                self._data[i] = secrets.randbits(8)
            # 再次清零
            for i in range(len(self._data)):
                self._data[i] = 0


class EntropyGenerator:
    """
    熵生成器类
    使用加密安全的随机数生成器(CSPRNG)生成高质量的随机熵
    增强内存安全性，防止敏感数据泄露
    """

    # 支持的熵长度映射（位数 -> 字节数）
    ENTROPY_LENGTHS = {
        128: 16,  # 12个助记词
        160: 20,  # 15个助记词
        192: 24,  # 18个助记词
        224: 28,  # 21个助记词
        256: 32,  # 24个助记词
    }

    @classmethod
    def generate_entropy(cls, bit_length: int = 256) -> SecureBytes:
        """
        生成指定长度的加密安全随机熵（内存安全版本）

        Args:
            bit_length (int): 熵的位长度，默认256位

        Returns:
            SecureBytes: 生成的安全随机熵（自动内存清理）

        Raises:
            ValueError: 如果提供的位长度不被支持
        """
        if bit_length not in cls.ENTROPY_LENGTHS:
            raise ValueError(
                f"不支持的熵长度: {bit_length}。支持的长度: {list(cls.ENTROPY_LENGTHS.keys())}"
            )

        byte_length = cls.ENTROPY_LENGTHS[bit_length]
        entropy_bytes = secrets.token_bytes(byte_length)

        # 返回安全字节对象
        return SecureBytes(entropy_bytes)

    @classmethod
    def calculate_checksum(cls, entropy: bytes, checksum_bits: int) -> int:
        """
        计算熵的校验和

        Args:
            entropy (bytes): 原始熵数据
            checksum_bits (int): 校验和位数

        Returns:
            int: 校验和值
        """
        # 使用SHA256哈希计算校验和
        hash_digest = hashlib.sha256(entropy).digest()

        # 取哈希的前几位作为校验和
        checksum = hash_digest[0]

        # 根据需要的位数提取校验和
        checksum = checksum >> (8 - checksum_bits)

        return checksum

    @classmethod
    def secure_compare(cls, data1: bytes, data2: bytes) -> bool:
        """
        安全比较两个字节串，防止时序攻击

        Args:
            data1 (bytes): 第一个数据
            data2 (bytes): 第二个数据

        Returns:
            bool: 是否相等
        """
        import hmac

        return hmac.compare_digest(data1, data2)

    @classmethod
    def secure_random_int(cls, min_val: int, max_val: int) -> int:
        """
        生成安全的随机整数（防止模偏差）

        Args:
            min_val (int): 最小值
            max_val (int): 最大值

        Returns:
            int: 安全的随机整数
        """
        return secrets.randbelow(max_val - min_val + 1) + min_val

    @classmethod
    def get_checksum_bits(cls, bit_length: int) -> int:
        """
        根据熵长度获取对应的校验和位数

        Args:
            bit_length (int): 熵的位长度

        Returns:
            int: 校验和位数
        """
        return bit_length // 32

    @classmethod
    def entropy_to_binary(cls, entropy: bytes) -> str:
        """
        将熵转换为二进制字符串

        Args:
            entropy (bytes): 熵数据

        Returns:
            str: 二进制字符串
        """
        return "".join(format(byte, "08b") for byte in entropy)

    @classmethod
    def add_checksum_to_entropy(cls, entropy: bytes) -> str:
        """
        为熵添加校验和并返回完整的二进制字符串

        Args:
            entropy (bytes): 原始熵

        Returns:
            str: 包含校验和的完整二进制字符串
        """
        bit_length = len(entropy) * 8
        checksum_bits = cls.get_checksum_bits(bit_length)

        # 计算校验和
        checksum = cls.calculate_checksum(entropy, checksum_bits)

        # 将熵转换为二进制
        entropy_binary = cls.entropy_to_binary(entropy)

        # 将校验和转换为二进制并添加到熵后面
        checksum_binary = format(checksum, f"0{checksum_bits}b")

        return entropy_binary + checksum_binary

    @classmethod
    def validate_entropy_length(cls, bit_length: int) -> bool:
        """
        验证熵长度是否有效

        Args:
            bit_length (int): 熵的位长度

        Returns:
            bool: 是否为有效长度
        """
        return bit_length in cls.ENTROPY_LENGTHS
