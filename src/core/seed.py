"""
种子生成模块
使用PBKDF2算法从助记词生成种子
"""

import hashlib
import hmac
from typing import Optional


class SeedGenerator:
    """
    种子生成器类
    实现BIP-39标准的种子生成功能
    """

    # PBKDF2参数
    PBKDF2_ITERATIONS = 2048
    SEED_LENGTH = 64  # 64字节 = 512位

    @classmethod
    def mnemonic_to_seed(cls, mnemonic: str, passphrase: str = "") -> bytes:
        """
        将助记词转换为种子

        使用PBKDF2-HMAC-SHA512算法，迭代2048次

        Args:
            mnemonic (str): 助记词字符串
            passphrase (str): 可选的密码短语，默认为空字符串

        Returns:
            bytes: 生成的种子（64字节）
            
        Raises:
            ValueError: 如果助记词无效
        """
        # ✅ 安全修复：在生成种子前验证助记词的有效性
        if not cls._validate_mnemonic_before_seed_generation(mnemonic):
            raise ValueError(
                f"无效的助记词，无法生成种子。助记词必须是有效的BIP-39格式。\n"
                f"请检查：\n"
                f"1. 助记词长度是否正确（12/15/18/21/24词）\n"
                f"2. 所有单词是否都在BIP-39词汇表中\n"
                f"3. 校验和是否正确"
            )
        
        # 标准化助记词（移除多余空格，转换为小写）
        normalized_mnemonic = cls._normalize_mnemonic(mnemonic)

        # 构造盐值：固定前缀 "mnemonic" + 密码短语
        salt = ("mnemonic" + passphrase).encode("utf-8")

        # 使用PBKDF2-HMAC-SHA512生成种子
        seed = hashlib.pbkdf2_hmac(
            "sha512",
            normalized_mnemonic.encode("utf-8"),
            salt,
            cls.PBKDF2_ITERATIONS,
            cls.SEED_LENGTH,
        )

        return seed

    @classmethod
    def _validate_mnemonic_before_seed_generation(cls, mnemonic: str) -> bool:
        """
        在种子生成前验证助记词的有效性
        
        Args:
            mnemonic (str): 助记词字符串
            
        Returns:
            bool: 助记词是否有效
        """
        try:
            # 动态导入MnemonicGenerator避免循环引用
            import sys
            import os
            
            # 检查是否已经导入
            if 'core.mnemonic' not in sys.modules:
                # 添加路径并导入
                current_dir = os.path.dirname(os.path.abspath(__file__))
                parent_dir = os.path.dirname(current_dir)
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
                from core.mnemonic import MnemonicGenerator
            else:
                # 使用已导入的模块
                MnemonicGenerator = sys.modules['core.mnemonic'].MnemonicGenerator
            
            # 使用MnemonicGenerator验证助记词
            mnemonic_validator = MnemonicGenerator()
            return mnemonic_validator.validate_mnemonic(mnemonic)
            
        except Exception:
            # 如果验证过程出现任何异常，为安全起见返回False
            return False

    @classmethod
    def _normalize_mnemonic(cls, mnemonic: str) -> str:
        """
        标准化助记词格式

        Args:
            mnemonic (str): 原始助记词

        Returns:
            str: 标准化后的助记词
        """
        # 移除首尾空格，将多个空格替换为单个空格，转换为小写
        return " ".join(mnemonic.strip().lower().split())

    @classmethod
    def seed_to_hex(cls, seed: bytes) -> str:
        """
        将种子转换为十六进制字符串

        Args:
            seed (bytes): 种子数据

        Returns:
            str: 十六进制字符串
        """
        return seed.hex()

    @classmethod
    def hex_to_seed(cls, hex_string: str) -> bytes:
        """
        将十六进制字符串转换为种子

        Args:
            hex_string (str): 十六进制字符串

        Returns:
            bytes: 种子数据

        Raises:
            ValueError: 如果十六进制字符串无效
        """
        try:
            return bytes.fromhex(hex_string)
        except ValueError as e:
            raise ValueError(f"无效的十六进制字符串: {e}")

    @classmethod
    def validate_seed_length(cls, seed: bytes) -> bool:
        """
        验证种子长度是否正确

        Args:
            seed (bytes): 种子数据

        Returns:
            bool: 是否为有效长度
        """
        return len(seed) == cls.SEED_LENGTH

    @classmethod
    def generate_seed_with_custom_params(
        cls,
        mnemonic: str,
        passphrase: str = "",
        iterations: Optional[int] = None,
        length: Optional[int] = None,
    ) -> bytes:
        """
        使用自定义参数生成种子

        Args:
            mnemonic (str): 助记词字符串
            passphrase (str): 密码短语
            iterations (Optional[int]): PBKDF2迭代次数，默认使用标准值
            length (Optional[int]): 种子长度，默认使用标准值

        Returns:
            bytes: 生成的种子
        """
        normalized_mnemonic = cls._normalize_mnemonic(mnemonic)
        salt = ("mnemonic" + passphrase).encode("utf-8")

        iterations = iterations or cls.PBKDF2_ITERATIONS
        length = length or cls.SEED_LENGTH

        seed = hashlib.pbkdf2_hmac(
            "sha512", normalized_mnemonic.encode("utf-8"), salt, iterations, length
        )

        return seed

    @classmethod
    def compare_seeds(cls, seed1: bytes, seed2: bytes) -> bool:
        """
        安全比较两个种子是否相同

        Args:
            seed1 (bytes): 第一个种子
            seed2 (bytes): 第二个种子

        Returns:
            bool: 是否相同
        """
        return hmac.compare_digest(seed1, seed2)

    @classmethod
    def get_seed_info(cls, seed: bytes) -> dict:
        """
        获取种子的信息

        Args:
            seed (bytes): 种子数据

        Returns:
            dict: 种子信息
        """
        return {
            "length_bytes": len(seed),
            "length_bits": len(seed) * 8,
            "hex": cls.seed_to_hex(seed),
            "is_valid_length": cls.validate_seed_length(seed),
        }
