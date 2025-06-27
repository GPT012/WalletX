"""
助记词生成模块
实现BIP-39标准的助记词生成、验证和转换功能
增强版：集成EMVC验证码功能
"""

import os
import sys
from typing import List, Tuple

# 添加src目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.entropy import EntropyGenerator
from core.verification import EMVCGenerator
from utils.wordlists import WordlistManager


class MnemonicGenerator:
    """
    助记词生成器类
    实现BIP-39标准的助记词相关功能
    增强版：包含EMVC验证码生成和验证
    """

    def __init__(self, language: str = "english"):
        """
        初始化助记词生成器

        Args:
            language (str): 语言类型，默认为英语
        """
        self.language = language
        self.wordlist_manager = WordlistManager()
        self.wordlist = self.wordlist_manager.get_wordlist(language)
        self.emvc_generator = EMVCGenerator()  # 新增：验证码生成器

    def generate_mnemonic(self, bit_length: int = 256) -> str:
        """
        生成助记词

        Args:
            bit_length (int): 熵的位长度，默认256位

        Returns:
            str: 生成的助记词字符串
        """
        # 生成熵
        entropy = EntropyGenerator.generate_entropy(bit_length)

        # 添加校验和
        entropy_with_checksum = EntropyGenerator.add_checksum_to_entropy(bytes(entropy))

        # 转换为助记词
        return self._binary_to_mnemonic(entropy_with_checksum)

    def generate_mnemonic_with_verification(self, bit_length: int = 256) -> Tuple[str, str]:
        """
        生成助记词和对应的EMVC验证码
        
        Args:
            bit_length (int): 熵的位长度，默认256位
            
        Returns:
            Tuple[str, str]: (助记词, 验证码)
        """
        # 生成助记词
        mnemonic = self.generate_mnemonic(bit_length)
        
        # 生成验证码
        verification_code = self.emvc_generator.generate_verification_code(mnemonic)
        
        return mnemonic, verification_code

    def generate_verification_code(self, mnemonic: str) -> str:
        """
        为现有助记词生成EMVC验证码
        
        Args:
            mnemonic (str): 助记词字符串
            
        Returns:
            str: 验证码
            
        Raises:
            ValueError: 助记词无效时抛出
        """
        # 先验证助记词有效性
        if not self.validate_mnemonic(mnemonic):
            raise ValueError("助记词无效，无法生成验证码")
        
        return self.emvc_generator.generate_verification_code(mnemonic)

    def verify_mnemonic_with_code(self, mnemonic: str, verification_code: str) -> bool:
        """
        验证助记词与验证码是否匹配
        
        Args:
            mnemonic (str): 助记词字符串
            verification_code (str): 验证码
            
        Returns:
            bool: 验证结果
        """
        # 首先验证助记词本身的有效性
        if not self.validate_mnemonic(mnemonic):
            return False
        
        # 验证助记词与验证码的匹配性
        return self.emvc_generator.verify_mnemonic(mnemonic, verification_code)

    def get_verification_code_info(self, verification_code: str) -> dict:
        """
        获取验证码的详细信息
        
        Args:
            verification_code (str): 验证码
            
        Returns:
            dict: 验证码信息
        """
        return self.emvc_generator.get_code_info(verification_code)

    def _binary_to_mnemonic(self, binary_string: str) -> str:
        """
        将二进制字符串转换为助记词

        Args:
            binary_string (str): 二进制字符串

        Returns:
            str: 助记词字符串
        """
        # 每11位对应一个单词
        words = []
        for i in range(0, len(binary_string), 11):
            # 取11位二进制
            word_bits = binary_string[i : i + 11]
            # 转换为索引
            word_index = int(word_bits, 2)
            # 获取对应的单词
            words.append(self.wordlist[word_index])

        return " ".join(words)

    def validate_mnemonic(self, mnemonic: str) -> bool:
        """
        验证助记词是否有效

        Args:
            mnemonic (str): 助记词字符串

        Returns:
            bool: 是否有效
        """
        try:
            words = mnemonic.strip().split()

            # 检查单词数量
            if len(words) not in [12, 15, 18, 21, 24]:
                return False

            # 检查所有单词是否在词汇表中
            for word in words:
                if word not in self.wordlist:
                    return False

            # 转换为二进制并验证校验和
            binary_string = self._mnemonic_to_binary(words)

            # 计算期望的校验和
            entropy_bits = len(binary_string) - len(binary_string) // 33
            checksum_bits = len(binary_string) - entropy_bits

            entropy_binary = binary_string[:entropy_bits]
            checksum_binary = binary_string[entropy_bits:]

            # 将二进制熵转换为字节
            entropy_bytes = self._binary_to_bytes(entropy_binary)

            # 计算校验和
            expected_checksum = EntropyGenerator.calculate_checksum(
                entropy_bytes, checksum_bits
            )
            actual_checksum = int(checksum_binary, 2)

            return expected_checksum == actual_checksum

        except Exception:
            return False

    def _mnemonic_to_binary(self, words: List[str]) -> str:
        """
        将助记词转换为二进制字符串

        Args:
            words (List[str]): 助记词列表

        Returns:
            str: 二进制字符串
        """
        binary_string = ""
        for word in words:
            word_index = self.wordlist.index(word)
            binary_string += format(word_index, "011b")

        return binary_string

    def _binary_to_bytes(self, binary_string: str) -> bytes:
        """
        将二进制字符串转换为字节

        Args:
            binary_string (str): 二进制字符串

        Returns:
            bytes: 字节数据
        """
        # 确保二进制字符串长度是8的倍数
        while len(binary_string) % 8 != 0:
            binary_string = "0" + binary_string

        # 转换为字节
        byte_array = bytearray()
        for i in range(0, len(binary_string), 8):
            byte_value = int(binary_string[i : i + 8], 2)
            byte_array.append(byte_value)

        return bytes(byte_array)

    def mnemonic_to_entropy(self, mnemonic: str) -> bytes:
        """
        将助记词转换回熵

        Args:
            mnemonic (str): 助记词字符串

        Returns:
            bytes: 原始熵数据

        Raises:
            ValueError: 如果助记词无效
        """
        if not self.validate_mnemonic(mnemonic):
            raise ValueError("无效的助记词")

        words = mnemonic.strip().split()
        binary_string = self._mnemonic_to_binary(words)

        # 分离熵和校验和
        entropy_bits = len(binary_string) - len(binary_string) // 33
        entropy_binary = binary_string[:entropy_bits]

        return self._binary_to_bytes(entropy_binary)

    def get_word_count_from_entropy(self, bit_length: int) -> int:
        """
        根据熵长度获取对应的助记词数量

        Args:
            bit_length (int): 熵的位长度

        Returns:
            int: 助记词数量
        """
        return (bit_length + bit_length // 32) // 11

    def get_supported_languages(self) -> List[str]:
        """
        获取支持的语言列表

        Returns:
            List[str]: 支持的语言列表
        """
        return self.wordlist_manager.get_supported_languages()

    def change_language(self, language: str) -> None:
        """
        更改助记词语言

        Args:
            language (str): 新的语言类型

        Raises:
            ValueError: 如果语言不被支持
        """
        if language not in self.get_supported_languages():
            raise ValueError(f"不支持的语言: {language}")

        self.language = language
        self.wordlist = self.wordlist_manager.get_wordlist(language)
