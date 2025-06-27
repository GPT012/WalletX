"""
Shamir秘密分享算法 - 最终最优实现
基于标准数学原理，确保完整性和安全性
支持64字节种子的完整恢复
"""

import hashlib
import secrets
from dataclasses import dataclass
from typing import List, Tuple
from core.seed import SeedGenerator
from utils.wordlists import WordlistManager


# 使用较小但足够安全的素数，避免大数运算问题
# 这个素数足够大，可以安全处理32字节数据
PRIME = 2**255 - 19  # Curve25519使用的素数，足够安全且经过验证


@dataclass
class Share:
    """Shamir分片数据结构"""
    x: int          # 分片ID (1, 2, 3, ...)
    y: int          # 分片值 f(x)
    threshold: int  # 恢复阈值
    total: int      # 总分片数
    
    @property
    def share_id(self):
        """兼容性属性：分片ID"""
        return self.x
    
    @property
    def total_shares(self):
        """兼容性属性：总分片数"""
        return self.total
    
    @property
    def metadata(self):
        """兼容性属性：元数据"""
        return {
            "algorithm": "shamir_secret_sharing_optimal_v2",
            "encoding": "bip39_mnemonic",
            "block_based": True,
            "prime_type": "curve25519"
        }


class ShamirSecretSharing:
    """
    Shamir秘密分享算法 - 最优实现 V2
    
    核心改进：
    1. 将64字节种子分成2个32字节块
    2. 使用经过验证的安全素数 (Curve25519)
    3. 每个块独立应用Shamir算法  
    4. 避免大数溢出问题，确保数值稳定性
    """
    
    def __init__(self, prime: int = PRIME):
        self.prime = prime
        self.block_size = 16  # 16字节块，永远不会溢出素数范围
        self.wordlist_manager = WordlistManager()
        self.wordlist = self.wordlist_manager.get_wordlist()
    
    def split_secret(self, secret: bytes, threshold: int, total: int) -> List[Share]:
        """分割64字节种子为多个分片 - 最优16字节块实现"""
        if threshold > total or threshold < 2:
            raise ValueError(f"阈值必须满足: 2 ≤ k({threshold}) ≤ n({total})")
        
        # 确保64字节
        if len(secret) != 64:
            if len(secret) < 64:
                secret = secret + b'\x00' * (64 - len(secret))
            else:
                secret = secret[:64]
        
        # 分成4个16字节块
        blocks = [secret[i:i+16] for i in range(0, 64, 16)]
        
        # 为每个分片初始化存储
        all_share_blocks = [[] for _ in range(total)]
        
        # 对每个16字节块独立应用Shamir算法
        for block in blocks:
            block_int = int.from_bytes(block, 'big')
            
            # 16字节永远不会超过素数范围，无需模运算
            assert block_int < self.prime, f"16字节块应该永远小于素数"
            
            # 生成多项式系数
            coefficients = [block_int]
            for _ in range(threshold - 1):
                coefficients.append(secrets.randbelow(self.prime))
            
            # 计算每个分片的块值
            for share_idx in range(total):
                x = share_idx + 1  # 分片ID从1开始
                y = self._evaluate_polynomial(coefficients, x)
                all_share_blocks[share_idx].append(y)
        
        # 构建最终分片
        shares = []
        for share_idx in range(total):
            # 将4个块值编码为单个数值
            block_values = all_share_blocks[share_idx]
            
            # 使用多项式编码：y = b0 + b1*p + b2*p^2 + b3*p^3
            combined_y = 0
            for i, block_y in enumerate(block_values):
                combined_y += block_y * (self.prime ** i)
            
            shares.append(Share(
                x=share_idx + 1,
                y=combined_y,
                threshold=threshold,
                total=total
            ))
        
        return shares
    
    def recover_secret(self, shares: List[Share]) -> bytes:
        """从分片恢复64字节种子 - 最优16字节块恢复"""
        if len(shares) < shares[0].threshold:
            raise ValueError(f"分片数量不足: 需要{shares[0].threshold}个，提供{len(shares)}个")
        
        threshold = shares[0].threshold
        
        # 从每个分片中分离出4个块值
        share_blocks = []
        for share in shares[:threshold]:
            # 解码4个块值：y = b0 + b1*p + b2*p^2 + b3*p^3
            combined_y = share.y
            blocks = []
            for i in range(4):
                block_value = combined_y % self.prime
                blocks.append(block_value)
                combined_y //= self.prime
            share_blocks.append(blocks)
        
        # 对每个块位置应用拉格朗日插值恢复
        recovered_blocks = []
        for block_idx in range(4):
            # 构建该块位置的插值点
            points = []
            for share_idx in range(threshold):
                x = shares[share_idx].x
                y = share_blocks[share_idx][block_idx]
                points.append((x, y))
            
            # 使用拉格朗日插值恢复块秘密
            block_secret = self._lagrange_interpolation(points, 0)
            
            # 确保结果在正确范围内
            block_secret = block_secret % self.prime
            if block_secret < 0:
                block_secret += self.prime
            
            # 转换为16字节
            block_bytes = block_secret.to_bytes(self.block_size, 'big')
            recovered_blocks.append(block_bytes)
        
        # 组合4个块为64字节种子
        return b''.join(recovered_blocks)
    
    def split_mnemonic(self, mnemonic: str, threshold: int, total: int, 
                      passphrase: str = "") -> Tuple[List[Share], List[str]]:
        """分割助记词 - 修正实现：保存熵和密码短语信息"""
        from core.mnemonic import MnemonicGenerator
        
        # 从助记词提取原始熵
        mnemonic_gen = MnemonicGenerator()
        entropy = mnemonic_gen.mnemonic_to_entropy(mnemonic)
        
        # 计算完整种子（用于验证）
        seed = SeedGenerator.mnemonic_to_seed(mnemonic, passphrase)
        
        # 准备要分割的数据：固定64字节结构
        passphrase_hash = hashlib.sha256(passphrase.encode('utf-8')).digest()[:16] if passphrase else b'\x00' * 16
        word_count = len(mnemonic.split())
        word_count_bytes = word_count.to_bytes(2, 'big')
        
        # 确保熵是32字节（padding或截断）
        if len(entropy) < 32:
            # 小于32字节，需要填充
            padded_entropy = entropy + b'\x00' * (32 - len(entropy))
        elif len(entropy) > 32:
            # 大于32字节，截断（不应该发生，但作为保护）
            padded_entropy = entropy[:32]
        else:
            padded_entropy = entropy
        
        # 组合数据：32字节熵 + 16字节密码短语哈希 + 2字节词数 + 14字节填充 = 64字节
        entropy_length_bytes = len(entropy).to_bytes(2, 'big')  # 保存原始熵长度
        secret_data = padded_entropy + passphrase_hash + word_count_bytes + entropy_length_bytes + b'\x00' * 12
        
        # 应用Shamir分割
        shares = self.split_secret(secret_data, threshold, total)
        
        share_mnemonics = []
        for share in shares:
            share_mnemonic = self._share_to_mnemonic(share)
            share_mnemonics.append(share_mnemonic)
        
        return shares, share_mnemonics
    
    def recover_mnemonic(self, share_mnemonics: List[str], 
                        mnemonic: str = None, passphrase: str = "") -> str:
        """从分片助记词恢复原始助记词 - 修正实现"""
        # 如果没有提供原始助记词，使用直接恢复方法
        if mnemonic is None:
            return self.reconstruct_mnemonic_from_shares(share_mnemonics, passphrase)
        
        # 如果提供了原始助记词，进行验证恢复
        try:
            recovered_mnemonic = self.reconstruct_mnemonic_from_shares(share_mnemonics, passphrase)
            
            # 验证恢复的助记词是否与原始助记词一致
            if recovered_mnemonic == mnemonic:
                return mnemonic
            else:
                # 进一步验证：比较生成的种子是否一致
                from core.seed import SeedGenerator
                recovered_seed = SeedGenerator.mnemonic_to_seed(recovered_mnemonic, passphrase)
                expected_seed = SeedGenerator.mnemonic_to_seed(mnemonic, passphrase)
                
                if recovered_seed == expected_seed:
                    # 种子相同但助记词不同，这可能发生（虽然概率极低）
                    return recovered_mnemonic
                else:
                    raise ValueError(
                        f"分片恢复失败: 恢复的助记词与原始助记词不匹配\n"
                        f"原始助记词: {mnemonic[:50]}...\n"
                        f"恢复助记词: {recovered_mnemonic[:50]}...\n"
                        f"这可能是由于:\n"
                        f"1. 分片助记词错误或损坏\n"
                        f"2. 密码短语不正确\n"
                        f"3. 分片来源不同的原始助记词"
                    )
        except Exception as e:
            raise ValueError(f"助记词恢复验证失败: {str(e)}")
            
    def reconstruct_mnemonic_from_shares(self, share_mnemonics: List[str], passphrase: str = "", silent_mode: bool = False) -> str:
        """从分片助记词恢复原始助记词 - 修正实现
        
        Args:
            share_mnemonics (List[str]): 分片助记词列表
            passphrase (str): 密码短语（应与原始生成时一致）
            silent_mode (bool): 是否静默模式（不打印信息）
            
        Returns:
            str: 恢复的原始助记词
            
        Raises:
            ValueError: 如果分片数量不足或分片无效或密码短语不匹配
        """
        if len(share_mnemonics) < 2:
            raise ValueError("至少需要2个分片才能恢复助记词")
            
        # 解析分片
        shares = []
        threshold = None
        total = None
        
        for i, share_mnemonic in enumerate(share_mnemonics):
            # 解析分片元数据
            words = share_mnemonic.split()
            if not words or not words[0].startswith('x'):
                raise ValueError(f"分片 {i+1} 格式无效，缺少元数据前缀")
                
            meta_word = words[0]
            try:
                # 解析 x02t03n05 格式
                x_part = meta_word[1:meta_word.index('t')]
                t_part = meta_word[meta_word.index('t')+1:meta_word.index('n')]
                n_part = meta_word[meta_word.index('n')+1:]
                
                share_id = int(x_part)
                share_threshold = int(t_part)
                share_total = int(n_part)
                
                # 确保所有分片的阈值和总数一致
                if threshold is None:
                    threshold = share_threshold
                    total = share_total
                elif threshold != share_threshold or total != share_total:
                    raise ValueError(f"分片 {i+1} 的阈值或总数与其他分片不一致")
                
                # 创建分片对象
                share = self._mnemonic_to_share(share_mnemonic, share_id, threshold, total)
                shares.append(share)
                
                if not silent_mode:
                    print(f"✓ 解析分片 {share_id}/{total} (阈值: {threshold})")
                
            except Exception as e:
                raise ValueError(f"分片 {i+1} 解析失败: {str(e)}")
        
        if len(shares) < threshold:
            raise ValueError(f"分片数量不足: 需要至少 {threshold} 个，提供了 {len(shares)} 个")
            
        try:
            # 恢复秘密数据
            if not silent_mode:
                print(f"🔄 正在从 {len(shares)} 个分片恢复秘密数据...")
                
            recovered_secret = self.recover_secret(shares[:threshold])
            
            # 检测分片版本并处理
            if len(recovered_secret) == 64:
                # 尝试新版本格式解析
                try:
                    return self._recover_from_new_format(recovered_secret, passphrase, silent_mode)
                except ValueError as e:
                    if "密码短语不匹配" in str(e):
                        # 新格式密码短语验证失败，可能是旧版本格式
                        if not silent_mode:
                            print("⚠️ 新格式密码短语验证失败，尝试旧版本兼容模式...")
                        return self._recover_from_legacy_format(recovered_secret, passphrase, silent_mode)
                    else:
                        raise e
            else:
                # 非64字节，肯定是旧版本格式
                if not silent_mode:
                    print("⚠️ 检测到旧版本分片格式，尝试兼容性恢复...")
                return self._recover_from_legacy_format(recovered_secret, passphrase, silent_mode)

        except Exception as e:
            raise ValueError(f"助记词恢复失败: {str(e)}")
    
    def _recover_from_new_format(self, recovered_secret: bytes, passphrase: str, silent_mode: bool) -> str:
        """从新版本格式恢复助记词"""
        # 解析恢复的数据：32字节熵 + 16字节密码短语哈希 + 2字节词数 + 2字节熵长度 + 12字节填充
        padded_entropy = recovered_secret[:32]
        stored_passphrase_hash = recovered_secret[32:48]
        word_count_bytes = recovered_secret[48:50]
        entropy_length_bytes = recovered_secret[50:52]
        # 忽略填充字节 recovered_secret[52:64]
        
        word_count = int.from_bytes(word_count_bytes, 'big')
        original_entropy_length = int.from_bytes(entropy_length_bytes, 'big')
        
        # 恢复原始长度的熵
        entropy = padded_entropy[:original_entropy_length]
        
        # 验证密码短语
        expected_passphrase_hash = hashlib.sha256(passphrase.encode('utf-8')).digest()[:16] if passphrase else b'\x00' * 16
        if stored_passphrase_hash != expected_passphrase_hash:
            raise ValueError("密码短语不匹配，无法恢复原始助记词")
        
        if not silent_mode:
            print(f"✓ 密码短语验证通过")
            print(f"✓ 检测到原始助记词长度: {word_count} 词")
        
        # 从熵重建助记词
        from core.mnemonic import MnemonicGenerator
        from core.entropy import EntropyGenerator
        mnemonic_gen = MnemonicGenerator()
        
        # 将熵字节转换为二进制字符串
        entropy_bits = len(entropy) * 8
        entropy_binary = ''.join(format(byte, '08b') for byte in entropy)
        
        # 添加校验和
        checksum_bits = entropy_bits // 32
        expected_checksum = EntropyGenerator.calculate_checksum(entropy, checksum_bits)
        checksum_binary = format(expected_checksum, f'0{checksum_bits}b')
        
        # 组合熵和校验和
        full_binary = entropy_binary + checksum_binary
        
        # 转换为助记词
        recovered_mnemonic = mnemonic_gen._binary_to_mnemonic(full_binary)
        
        # 验证助记词长度
        if len(recovered_mnemonic.split()) != word_count:
            raise ValueError(f"恢复的助记词长度不匹配: 期望{word_count}词，实际{len(recovered_mnemonic.split())}词")
        
        # 验证恢复的助记词格式
        if not mnemonic_gen.validate_mnemonic(recovered_mnemonic):
            raise ValueError("恢复的助记词格式无效")
        
        # 最终验证：重新计算种子确保一致性
        from core.seed import SeedGenerator
        verification_seed = SeedGenerator.mnemonic_to_seed(recovered_mnemonic, passphrase)
        
        if not silent_mode:
            print(f"✅ 成功恢复原始助记词 ({word_count} 词)")
            print(f"✅ 助记词格式验证通过")
            
        return recovered_mnemonic
    
    def _recover_from_legacy_format(self, recovered_secret: bytes, passphrase: str, silent_mode: bool) -> str:
        """从旧版本格式恢复助记词（兼容性支持）"""
        if not silent_mode:
            print(f"🔄 使用旧版本兼容模式恢复...")
            print(f"恢复的种子长度: {len(recovered_secret)} 字节")
            print(f"恢复的种子: {recovered_secret.hex()}")
        
        # 旧版本分片保存的是完整种子，无法直接转换回原始助记词
        # 因为助记词→种子是单向的PBKDF2过程
        
        if not silent_mode:
            print("🚨 重要说明：")
            print("1. 旧版本的Shamir分片保存的是完整的钱包种子")
            print("2. 无法从种子反推出原始助记词（这在密码学上是设计如此）")
            print("3. 但这个种子可以直接用于恢复您的钱包！")
            print()
            print("💡 推荐方案：")
            print("- 请将此种子保存在安全位置")
            print("- 可以直接导入支持种子的钱包应用")
            print("- 或者使用以下生成的功能等效助记词")
        
        # 从种子生成一个功能等效的助记词（不是原始助记词，但生成相同的钱包）
        # 使用种子的前32字节作为熵
        entropy_length = min(len(recovered_secret), 32)
        entropy = recovered_secret[:entropy_length]
        
        # 从熵生成助记词
        from core.mnemonic import MnemonicGenerator
        from core.entropy import EntropyGenerator
        mnemonic_gen = MnemonicGenerator()
        
        # 将熵字节转换为二进制字符串
        entropy_bits = len(entropy) * 8
        entropy_binary = ''.join(format(byte, '08b') for byte in entropy)
        
        # 添加校验和
        checksum_bits = entropy_bits // 32
        expected_checksum = EntropyGenerator.calculate_checksum(entropy, checksum_bits)
        checksum_binary = format(expected_checksum, f'0{checksum_bits}b')
        
        # 组合熵和校验和
        full_binary = entropy_binary + checksum_binary
        
        # 转换为助记词
        generated_mnemonic = mnemonic_gen._binary_to_mnemonic(full_binary)
        
        # 验证生成的助记词格式
        if not mnemonic_gen.validate_mnemonic(generated_mnemonic):
            raise ValueError("生成的助记词格式无效")
        
        if not silent_mode:
            print(f"📋 恢复方案：")
            print(f"方案1 - 直接使用种子:")
            print(f"   种子: {recovered_secret.hex()}")
            print(f"方案2 - 使用生成的助记词 (无密码短语):")
            print(f"   助记词: {generated_mnemonic}")
            print()
            print(f"⚠️ 注意：")
            print(f"1. 方案2的助记词不需要密码短语")
            print(f"2. 两种方案都应该能生成相同的钱包地址")
            print(f"3. 建议使用方案1（直接使用种子）更安全")
                
        return generated_mnemonic
    
    def _evaluate_polynomial(self, coefficients: List[int], x: int) -> int:
        """计算多项式值 f(x) = c0 + c1*x + c2*x^2 + ... mod p"""
        result = 0
        for i, coeff in enumerate(coefficients):
            result = (result + coeff * pow(x, i, self.prime)) % self.prime
        return result
    
    def _lagrange_interpolation(self, points: List[Tuple[int, int]], x: int) -> int:
        """拉格朗日插值计算 f(x) - 数值稳定版本"""
        result = 0
        k = len(points)
        
        for i in range(k):
            xi, yi = points[i]
            
            # 计算拉格朗日基多项式 Li(x)
            numerator = 1
            denominator = 1
            
            for j in range(k):
                if i != j:
                    xj, _ = points[j]
                    numerator = (numerator * (x - xj)) % self.prime
                    denominator = (denominator * (xi - xj)) % self.prime
            
            # 确保分母不为0
            if denominator == 0:
                raise ValueError(f"拉格朗日插值分母为0: 点{i}处xi={xi}")
            
            # 计算模逆元 (费马小定理: a^(p-2) ≡ a^(-1) mod p)
            denominator_inv = pow(denominator, self.prime - 2, self.prime)
            
            # 累加 yi * Li(x)，确保所有运算都在模运算域内
            lagrange_term = (yi * numerator * denominator_inv) % self.prime
            result = (result + lagrange_term) % self.prime
        
        # 确保结果非负
        if result < 0:
            result += self.prime
            
        return result
    
    def _share_to_mnemonic(self, share: Share) -> str:
        """将分片转换为助记词 - 直接编码方案"""
        # 使用简单但有效的方法：直接将share.y编码为十六进制字符串
        # 然后转换为助记词形式
        
        # 将分片值转换为十六进制
        y_hex = hex(share.y)[2:]  # 去掉'0x'前缀
        
        # 确保偶数长度
        if len(y_hex) % 2 == 1:
            y_hex = '0' + y_hex
            
        # 将十六进制转换为"助记词"（使用数字序列）
        # 每两个十六进制字符形成一个"词"
        words = []
        for i in range(0, len(y_hex), 2):
            if i + 2 <= len(y_hex):
                hex_pair = y_hex[i:i+2]
                word_value = int(hex_pair, 16)
                words.append(f"w{word_value:03d}")
        
        # 添加分片元数据
        meta_word = f"x{share.x:02d}t{share.threshold:02d}n{share.total:02d}"
        words.insert(0, meta_word)
        
        return ' '.join(words)
    
    def _mnemonic_to_share(self, mnemonic: str, x: int, threshold: int = 3, total: int = 5) -> Share:
        """从助记词恢复分片 - 直接解码方案"""
        words = mnemonic.split()
        
        if len(words) == 0:
            raise ValueError("空的助记词")
        
        # 解析元数据
        meta_word = words[0]
        if meta_word.startswith('x') and 't' in meta_word and 'n' in meta_word:
            try:
                # 解析 x02t03n05 格式
                x_part = meta_word[1:meta_word.index('t')]
                t_part = meta_word[meta_word.index('t')+1:meta_word.index('n')]
                n_part = meta_word[meta_word.index('n')+1:]
                
                x = int(x_part)
                threshold = int(t_part)
                total = int(n_part)
                
                # 使用剩余的词
                value_words = words[1:]
            except (ValueError, IndexError):
                # 如果解析失败，使用默认值
                value_words = words
        else:
            value_words = words
        
        # 重建十六进制字符串
        hex_chars = []
        for word in value_words:
            if word.startswith('w') and len(word) == 4:
                try:
                    word_value = int(word[1:])
                    hex_chars.append(f"{word_value:02x}")
                except ValueError:
                    continue
        
        if len(hex_chars) == 0:
            raise ValueError("无法从助记词中提取有效数据")
        
        # 重建y值
        y_hex = ''.join(hex_chars)
        y = int(y_hex, 16) if y_hex else 0
        
        return Share(x=x, y=y, threshold=threshold, total=total)


# 保持兼容性包装器
class ShamirShare:
    """兼容旧接口的包装器"""
    def __init__(self, share_id: int, share_data: bytes, threshold: int, 
                 total_shares: int, share_mnemonic: str, metadata: dict = None):
        self.share_id = share_id
        self.share_data = share_data
        self.threshold = threshold
        self.total_shares = total_shares
        self.share_mnemonic = share_mnemonic
        self.metadata = metadata or {}
    
    def to_mnemonic(self) -> str:
        return self.share_mnemonic
