#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
助记词验证模块 - 精简版
实现BIP-39标准的核心验证功能
"""

import hashlib
from typing import Dict, List

from .wordlists import WordlistManager


class MnemonicValidator:
    """BIP-39助记词验证器 - 核心功能版"""

    def __init__(self):
        """初始化验证器"""
        self.wordlist_manager = WordlistManager()

    def validate_mnemonic_format(self, mnemonic: str) -> Dict:
        """验证助记词格式"""
        result = {
            "is_valid": True,
            "errors": [],
            "word_count": 0,
        }

        if not isinstance(mnemonic, str):
            result["is_valid"] = False
            result["errors"].append("助记词必须是字符串")
            return result

        # 清理并分割单词
        words = mnemonic.strip().lower().split()
        result["word_count"] = len(words)

        # 检查单词数量
        if len(words) not in [12, 15, 18, 21, 24]:
            result["is_valid"] = False
            result["errors"].append("助记词长度必须为12、15、18、21或24个单词")

        return result

    def validate_mnemonic_words(self, mnemonic: str) -> Dict:
        """验证助记词中的单词是否在词汇表中"""
        result = {"is_valid": True, "errors": [], "invalid_words": []}

        words = mnemonic.strip().lower().split()
        wordlist = self.wordlist_manager.get_wordlist()

        for word in words:
            if word not in wordlist:
                result["is_valid"] = False
                result["invalid_words"].append(word)

        if result["invalid_words"]:
            result["errors"].append(f"无效单词: {', '.join(result['invalid_words'])}")

        return result

    def validate_mnemonic_checksum(self, mnemonic: str) -> Dict:
        """验证助记词校验和"""
        result = {"is_valid": True, "errors": []}

        try:
            words = mnemonic.strip().lower().split()
            wordlist = self.wordlist_manager.get_wordlist()

            # 转换为二进制
            binary_str = ""
            for word in words:
                index = wordlist.index(word)
                binary_str += format(index, "011b")

            # 分离熵和校验和
            entropy_bits = len(words) * 11 - len(words) // 3
            entropy_binary = binary_str[:entropy_bits]
            checksum_binary = binary_str[entropy_bits:]

            # 计算预期校验和
            entropy_bytes = self._binary_to_bytes(entropy_binary)
            hash_bytes = hashlib.sha256(entropy_bytes).digest()
            calculated_checksum = format(hash_bytes[0], "08b")[: len(checksum_binary)]

            if checksum_binary != calculated_checksum:
                result["is_valid"] = False
                result["errors"].append("校验和验证失败")

        except Exception as e:
            result["is_valid"] = False
            result["errors"].append(f"校验和验证出错: {str(e)}")

        return result

    def comprehensive_validate(self, mnemonic: str) -> Dict:
        """全面验证助记词"""
        result = {
            "is_valid": True,
            "errors": [],
            "format_valid": False,
            "words_valid": False,
            "checksum_valid": False,
        }

        # 格式验证
        format_result = self.validate_mnemonic_format(mnemonic)
        result["format_valid"] = format_result["is_valid"]
        result["errors"].extend(format_result["errors"])

        if not format_result["is_valid"]:
            result["is_valid"] = False
            return result

        # 单词验证
        words_result = self.validate_mnemonic_words(mnemonic)
        result["words_valid"] = words_result["is_valid"]
        result["errors"].extend(words_result["errors"])

        if not words_result["is_valid"]:
            result["is_valid"] = False
            return result

        # 校验和验证
        checksum_result = self.validate_mnemonic_checksum(mnemonic)
        result["checksum_valid"] = checksum_result["is_valid"]
        result["errors"].extend(checksum_result["errors"])

        if not checksum_result["is_valid"]:
            result["is_valid"] = False

        return result

    def _binary_to_bytes(self, binary_string: str) -> bytes:
        """将二进制字符串转换为字节"""
        # 补齐到8的倍数
        padded = binary_string.ljust((len(binary_string) + 7) // 8 * 8, "0")
        return bytes(
            int(padded[i : i + 8], 2) for i in range(0, len(padded), 8)
        )


# 快捷函数
def validate_mnemonic(mnemonic: str) -> bool:
    """快速验证助记词是否有效"""
    validator = MnemonicValidator()
    result = validator.comprehensive_validate(mnemonic)
    return result["is_valid"]
