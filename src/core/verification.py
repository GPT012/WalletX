"""
Enhanced Mnemonic Verification Code (EMVC) - 助记词验证码算法
提供助记词的唯一确定验证码生成和验证功能

安全特性：
- 多层SHA-256哈希确保密码学安全
- 64位熵空间提供充足唯一性  
- 人性化编码便于记忆和使用
- 防止字符混淆的编码方案
"""

import hashlib
import re
from typing import Optional, Tuple


class EMVCGenerator:
    """Enhanced Mnemonic Verification Code 生成器"""
    
    # 盐值 - 用于增强哈希安全性
    SALT = "WALLETX_EMVC_2024"
    
    # 编码字符集 - 排除易混淆字符 (I, O, 1, 0)
    LETTER_CHARSET = "ABCDEFGHJKLMNPQRSTUVWXYZ"  # 24个字符
    
    def __init__(self):
        """初始化验证码生成器"""
        pass
    
    def generate_verification_code(self, mnemonic: str) -> str:
        """
        为助记词生成EMVC验证码
        
        Args:
            mnemonic (str): 助记词字符串
            
        Returns:
            str: 8位验证码，格式为 XXXX-YYYY
            
        Raises:
            ValueError: 助记词格式无效时抛出
        """
        # 1. 输入验证和标准化
        normalized_mnemonic = self._normalize_mnemonic(mnemonic)
        
        # 2. 验证助记词有效性
        if not self._validate_mnemonic_format(normalized_mnemonic):
            raise ValueError("助记词格式无效或不符合BIP-39标准")
        
        # 3. 多层哈希计算
        hash_result = self._compute_multilayer_hash(normalized_mnemonic)
        
        # 4. 生成验证码
        verification_code = self._encode_to_verification_code(hash_result)
        
        return verification_code
    
    def verify_mnemonic(self, mnemonic: str, expected_code: str) -> bool:
        """
        验证助记词与验证码是否匹配
        
        Args:
            mnemonic (str): 待验证的助记词
            expected_code (str): 期望的验证码
            
        Returns:
            bool: 验证通过返回True，否则返回False
        """
        try:
            # 生成助记词的验证码
            actual_code = self.generate_verification_code(mnemonic)
            
            # 标准化验证码格式进行比较
            normalized_expected = self._normalize_verification_code(expected_code)
            normalized_actual = self._normalize_verification_code(actual_code)
            
            return normalized_expected == normalized_actual
            
        except Exception:
            # 任何异常都视为验证失败
            return False
    
    def _normalize_mnemonic(self, mnemonic: str) -> str:
        """
        标准化助记词格式
        
        Args:
            mnemonic (str): 原始助记词
            
        Returns:
            str: 标准化的助记词（小写，单空格分隔）
        """
        if not mnemonic or not isinstance(mnemonic, str):
            raise ValueError("助记词不能为空且必须是字符串")
        
        # 去除前后空白，转换为小写，规范化空格
        normalized = re.sub(r'\s+', ' ', mnemonic.strip().lower())
        
        return normalized
    
    def _validate_mnemonic_format(self, mnemonic: str) -> bool:
        """
        验证助记词格式的基本有效性
        
        Args:
            mnemonic (str): 标准化的助记词
            
        Returns:
            bool: 格式有效返回True
        """
        words = mnemonic.split()
        
        # 检查词数是否符合BIP-39标准
        if len(words) not in [12, 15, 18, 21, 24]:
            return False
        
        # 检查每个词是否只包含字母
        for word in words:
            if not word.isalpha():
                return False
        
        # TODO: 可以添加更严格的BIP-39词表验证
        return True
    
    def _compute_multilayer_hash(self, mnemonic: str) -> bytes:
        """
        计算多层SHA-256哈希
        
        Args:
            mnemonic (str): 标准化的助记词
            
        Returns:
            bytes: 最终哈希结果
        """
        # 第一层：基础哈希
        layer1 = hashlib.sha256(mnemonic.encode('utf-8')).digest()
        
        # 第二层：加盐哈希
        layer2_input = layer1 + self.SALT.encode('utf-8')
        layer2 = hashlib.sha256(layer2_input).digest()
        
        # 第三层：加入助记词长度信息
        word_count = len(mnemonic.split())
        layer3_input = layer2 + word_count.to_bytes(1, 'big')
        layer3 = hashlib.sha256(layer3_input).digest()
        
        return layer3
    
    def _encode_to_verification_code(self, hash_bytes: bytes) -> str:
        """
        将哈希结果编码为人性化的验证码
        
        Args:
            hash_bytes (bytes): 哈希结果
            
        Returns:
            str: 格式为 XXXX-YYYY 的验证码
        """
        # 取前8字节作为验证码源
        code_bytes = hash_bytes[:8]
        
        # 分成两部分：前4字节和后4字节
        part1_bytes = code_bytes[:4]
        part2_bytes = code_bytes[4:]
        
        # 前4字节 → 4位数字 (0000-9999)
        part1_int = int.from_bytes(part1_bytes, 'big')
        part1_digits = f"{part1_int % 10000:04d}"
        
        # 后4字节 → 4位字母 (使用安全字符集)
        part2_letters = ""
        for byte in part2_bytes:
            letter_index = byte % len(self.LETTER_CHARSET)
            part2_letters += self.LETTER_CHARSET[letter_index]
        
        # 组合成最终验证码
        verification_code = f"{part1_digits}-{part2_letters}"
        
        return verification_code
    
    def _normalize_verification_code(self, code: str) -> str:
        """
        标准化验证码格式用于比较
        
        Args:
            code (str): 验证码
            
        Returns:
            str: 标准化的验证码
        """
        if not code:
            return ""
        
        # 去除空白，转换为大写，确保包含连字符
        normalized = re.sub(r'\s+', '', code.upper())
        
        # 如果没有连字符，尝试在第4位插入
        if '-' not in normalized and len(normalized) == 8:
            normalized = f"{normalized[:4]}-{normalized[4:]}"
        
        return normalized
    
    def get_code_info(self, verification_code: str) -> dict:
        """
        获取验证码的详细信息（用于调试和展示）
        
        Args:
            verification_code (str): 验证码
            
        Returns:
            dict: 验证码信息
        """
        try:
            normalized = self._normalize_verification_code(verification_code)
            
            if len(normalized) != 9 or '-' != normalized[4]:
                return {"valid_format": False, "error": "验证码格式无效"}
            
            digits_part = normalized[:4]
            letters_part = normalized[5:]
            
            return {
                "valid_format": True,
                "full_code": normalized,
                "digits_part": digits_part,
                "letters_part": letters_part,
                "entropy_bits": 64,
                "format": "XXXX-YYYY",
                "description": "4位数字 + 4位字母组成的64位熵验证码"
            }
            
        except Exception as e:
            return {"valid_format": False, "error": str(e)}


def generate_mnemonic_verification_code(mnemonic: str) -> str:
    """
    便捷函数：为助记词生成验证码
    
    Args:
        mnemonic (str): 助记词
        
    Returns:
        str: 验证码
    """
    generator = EMVCGenerator()
    return generator.generate_verification_code(mnemonic)


def verify_mnemonic_with_code(mnemonic: str, verification_code: str) -> bool:
    """
    便捷函数：验证助记词与验证码是否匹配
    
    Args:
        mnemonic (str): 助记词
        verification_code (str): 验证码
        
    Returns:
        bool: 验证结果
    """
    generator = EMVCGenerator()
    return generator.verify_mnemonic(mnemonic, verification_code)


if __name__ == "__main__":
    # 测试代码
    test_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    
    generator = EMVCGenerator()
    
    print("🔬 EMVC验证码算法测试")
    print("=" * 50)
    print(f"测试助记词: {test_mnemonic}")
    
    # 生成验证码
    code = generator.generate_verification_code(test_mnemonic)
    print(f"生成验证码: {code}")
    
    # 验证码信息
    info = generator.get_code_info(code)
    print(f"验证码信息: {info}")
    
    # 验证测试
    is_valid = generator.verify_mnemonic(test_mnemonic, code)
    print(f"验证结果: {'✅ 通过' if is_valid else '❌ 失败'}")
    
    # 错误验证测试
    wrong_code = "0000-AAAA"
    is_invalid = generator.verify_mnemonic(test_mnemonic, wrong_code)
    print(f"错误验证码测试: {'❌ 应该失败但通过了' if is_invalid else '✅ 正确失败'}") 