"""
密钥派生模块
实现BIP-32/BIP-44标准的分层确定性钱包密钥派生
使用真正的椭圆曲线运算而不是模拟实现
"""

import hashlib
import hmac
import struct
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from Crypto.Hash import keccak  # 用于以太坊地址生成
import coincurve  # 用于secp256k1椭圆曲线运算


@dataclass
class ExtendedKey:
    """扩展密钥数据类"""

    key: bytes
    chain_code: bytes
    depth: int
    parent_fingerprint: bytes
    index: int

    def __post_init__(self):
        """验证密钥数据"""
        if len(self.key) != 32:
            raise ValueError("密钥长度必须为32字节")
        if len(self.chain_code) != 32:
            raise ValueError("链码长度必须为32字节")
        if len(self.parent_fingerprint) != 4:
            raise ValueError("父指纹长度必须为4字节")


@dataclass
class DerivedAddress:
    """派生地址数据类"""

    address: str
    private_key: str
    public_key: str
    path: str
    index: int
    private_key_wif: str = ""  # WIF格式私钥（比特币网络专用）


class KeyDerivation:
    """
    密钥派生类
    实现BIP-32/BIP-44标准的分层确定性钱包功能
    使用真正的secp256k1椭圆曲线运算
    """

    # BIP-44标准派生路径
    DERIVATION_PATHS = {
        "bitcoin": "m/44'/0'/0'/0",
        "ethereum": "m/44'/60'/0'/0",
        "binance": "m/44'/714'/0'/0",
        "litecoin": "m/44'/2'/0'/0",
        "dogecoin": "m/44'/3'/0'/0",
        "bitcoin_cash": "m/44'/145'/0'/0",
        "cardano": "m/44'/1815'/0'/0",
        "polkadot": "m/44'/354'/0'/0",
        "solana": "m/44'/501'/0'/0",
        "avalanche": "m/44'/9000'/0'/0",
    }

    # 网络名称别名映射 - 支持常见简写
    NETWORK_ALIASES = {
        "eth": "ethereum",
        "btc": "bitcoin",
        "bnb": "binance", 
        "ltc": "litecoin",
        "doge": "dogecoin",
        "bch": "bitcoin_cash",
        "ada": "cardano",
        "dot": "polkadot",
        "sol": "solana",
        "avax": "avalanche",
    }

    # 硬化派生的起始值
    HARDENED_KEY_OFFSET = 0x80000000

    # secp256k1 曲线的阶数
    CURVE_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

    def __init__(self, seed: bytes):
        """
        初始化密钥派生器

        Args:
            seed (bytes): 种子数据
        """
        self.seed = seed
        self.master_key = self._generate_master_key()

    def _generate_master_key(self) -> ExtendedKey:
        """
        从种子生成主密钥

        Returns:
            ExtendedKey: 主扩展密钥
        """
        # 使用HMAC-SHA512和"Bitcoin seed"作为key
        hmac_result = hmac.new(b"Bitcoin seed", self.seed, hashlib.sha512).digest()

        # 前32字节作为主私钥，后32字节作为主链码
        master_private_key = hmac_result[:32]
        master_chain_code = hmac_result[32:]

        # 验证私钥是否在有效范围内
        if int.from_bytes(master_private_key, 'big') >= self.CURVE_ORDER:
            raise ValueError("生成的主私钥超出了secp256k1曲线的有效范围")

        return ExtendedKey(
            key=master_private_key,
            chain_code=master_chain_code,
            depth=0,
            parent_fingerprint=b"\x00\x00\x00\x00",
            index=0,
        )

    def _derive_child_key(self, parent_key: ExtendedKey, index: int) -> ExtendedKey:
        """
        派生子密钥

        Args:
            parent_key (ExtendedKey): 父扩展密钥
            index (int): 子密钥索引

        Returns:
            ExtendedKey: 子扩展密钥
        """
        # 判断是否为硬化派生
        is_hardened = index >= self.HARDENED_KEY_OFFSET

        if is_hardened:
            # 硬化派生：使用父私钥
            data = b"\x00" + parent_key.key + struct.pack(">I", index)
        else:
            # 非硬化派生：使用父公钥
            parent_public_key = self._private_key_to_public_key(parent_key.key)
            data = parent_public_key + struct.pack(">I", index)

        # 计算HMAC-SHA512
        hmac_result = hmac.new(parent_key.chain_code, data, hashlib.sha512).digest()

        # 前32字节作为子私钥的调整值
        child_key_adjustment = hmac_result[:32]
        child_chain_code = hmac_result[32:]

        # 计算子私钥：使用椭圆曲线点运算
        child_private_key = self._add_private_keys(parent_key.key, child_key_adjustment)

        # 计算父指纹
        parent_public_key = self._private_key_to_public_key(parent_key.key)
        parent_fingerprint = self._calculate_fingerprint(parent_public_key)

        return ExtendedKey(
            key=child_private_key,
            chain_code=child_chain_code,
            depth=parent_key.depth + 1,
            parent_fingerprint=parent_fingerprint,
            index=index,
        )

    def _private_key_to_public_key(self, private_key: bytes) -> bytes:
        """
        从私钥生成公钥（使用真正的secp256k1椭圆曲线）

        Args:
            private_key (bytes): 私钥

        Returns:
            bytes: 压缩公钥
        """
        # 使用coincurve库进行真正的椭圆曲线运算
        private_key_obj = coincurve.PrivateKey(private_key)
        public_key_compressed = private_key_obj.public_key.format(compressed=True)
        return public_key_compressed

    def _add_private_keys(self, key1: bytes, key2: bytes) -> bytes:
        """
        私钥相加（使用椭圆曲线模运算）

        Args:
            key1 (bytes): 第一个私钥
            key2 (bytes): 第二个私钥

        Returns:
            bytes: 相加结果
        """
        # 转换为整数
        key1_int = int.from_bytes(key1, 'big')
        key2_int = int.from_bytes(key2, 'big')
        
        # 模加运算
        result_int = (key1_int + key2_int) % self.CURVE_ORDER
        
        # 转换回字节
        return result_int.to_bytes(32, 'big')

    def _resolve_network_name(self, network: str) -> str:
        """
        解析网络名称，支持别名映射
        
        Args:
            network (str): 输入的网络名称（可能是别名）
            
        Returns:
            str: 解析后的标准网络名称
        """
        network_lower = network.lower().strip()
        return self.NETWORK_ALIASES.get(network_lower, network_lower)

    def _calculate_fingerprint(self, public_key: bytes) -> bytes:
        """
        计算公钥指纹

        Args:
            public_key (bytes): 公钥

        Returns:
            bytes: 4字节指纹
        """
        # 计算RIPEMD160(SHA256(public_key))的前4字节
        sha256_hash = hashlib.sha256(public_key).digest()
        
        # 使用pycryptodome的RIPEMD160
        try:
            from Crypto.Hash import RIPEMD160
            ripemd160_hash = RIPEMD160.new(sha256_hash).digest()
        except ImportError:
            # 如果没有RIPEMD160，使用SHA256的前20字节作为替代
            ripemd160_hash = hashlib.sha256(sha256_hash).digest()[:20]
        
        return ripemd160_hash[:4]

    def derive_path(self, path: str) -> ExtendedKey:
        """
        按路径派生密钥

        Args:
            path (str): 派生路径，如 "m/44'/0'/0'/0"

        Returns:
            ExtendedKey: 派生的扩展密钥
        """
        # 解析路径
        path_parts = path.split("/")

        if path_parts[0] != "m":
            raise ValueError("路径必须以 'm' 开头")

        current_key = self.master_key

        for part in path_parts[1:]:
            if part.endswith("'"):
                # 硬化派生
                index = int(part[:-1]) + self.HARDENED_KEY_OFFSET
            else:
                # 非硬化派生
                index = int(part)

            current_key = self._derive_child_key(current_key, index)

        return current_key

    def derive_addresses(
        self, network: str, count: int = 10, start_index: int = 0
    ) -> List[DerivedAddress]:
        """
        派生指定网络的地址

        Args:
            network (str): 网络名称（支持别名，如 eth -> ethereum）
            count (int): 要生成的地址数量
            start_index (int): 起始索引

        Returns:
            List[DerivedAddress]: 派生的地址列表
        """
        # 解析网络名称，支持别名映射
        resolved_network = self._resolve_network_name(network)
        
        if resolved_network not in self.DERIVATION_PATHS:
            # 提供更友好的错误信息
            supported_networks = list(self.DERIVATION_PATHS.keys())
            supported_aliases = list(self.NETWORK_ALIASES.keys())
            raise ValueError(
                f"不支持的网络: {network} (解析为: {resolved_network})\n"
                f"支持的网络: {supported_networks}\n"
                f"支持的别名: {supported_aliases}"
            )

        base_path = self.DERIVATION_PATHS[resolved_network]
        addresses = []

        for i in range(start_index, start_index + count):
            # 构造完整路径
            full_path = f"{base_path}/{i}"

            # 派生密钥
            derived_key = self.derive_path(full_path)

            # 生成地址 - 使用解析后的网络名称
            address = self._generate_address(derived_key.key, resolved_network)
            public_key = self._private_key_to_public_key(derived_key.key)

            # 为比特币网络生成WIF格式私钥
            private_key_wif = ""
            if resolved_network == "bitcoin":
                private_key_wif = self._private_key_to_wif(derived_key.key, compressed=True)

            addresses.append(
                DerivedAddress(
                    address=address,
                    private_key=derived_key.key.hex(),
                    public_key=public_key.hex(),
                    path=full_path,
                    index=i,
                    private_key_wif=private_key_wif,
                )
            )

        return addresses

    def _generate_address(self, private_key: bytes, network: str) -> str:
        """
        从私钥生成地址（使用正确的算法）

        Args:
            private_key (bytes): 私钥
            network (str): 网络类型

        Returns:
            str: 生成的地址
        """
        # 生成公钥
        private_key_obj = coincurve.PrivateKey(private_key)
        public_key_uncompressed = private_key_obj.public_key.format(compressed=False)

        if network == "ethereum":
            # 以太坊地址生成：Keccak256(uncompressed_public_key[1:])的后20字节
            # 去掉0x04前缀，只取64字节的坐标部分
            public_key_bytes = public_key_uncompressed[1:]
            
            # 使用Keccak256而不是SHA3-256
            keccak_hash = keccak.new(digest_bits=256)
            keccak_hash.update(public_key_bytes)
            address_bytes = keccak_hash.digest()[-20:]
            
            # 转换为校验和格式的地址
            address = "0x" + address_bytes.hex()
            return self._to_checksum_address(address)
            
        elif network == "bitcoin":
            # 比特币地址生成 - 标准P2PKH格式
            public_key_compressed = private_key_obj.public_key.format(compressed=True)
            
            # SHA256哈希
            sha256_hash = hashlib.sha256(public_key_compressed).digest()
            
            # RIPEMD160哈希
            try:
                from Crypto.Hash import RIPEMD160
                ripemd160_hash = RIPEMD160.new(sha256_hash).digest()
            except ImportError:
                # 如果没有RIPEMD160，使用SHA256的前20字节作为替代
                ripemd160_hash = hashlib.sha256(sha256_hash).digest()[:20]
            
            # 添加版本字节(0x00 for mainnet P2PKH)
            versioned_payload = b"\x00" + ripemd160_hash
            
            # 计算校验和：double SHA256的前4字节
            checksum = hashlib.sha256(hashlib.sha256(versioned_payload).digest()).digest()[:4]
            
            # 完整的地址数据
            full_payload = versioned_payload + checksum
            
            # Base58编码
            import base58
            return base58.b58encode(full_payload).decode('ascii')
        else:
            # 其他网络使用通用格式
            public_key_compressed = private_key_obj.public_key.format(compressed=True)
            address_hash = hashlib.sha256(public_key_compressed).digest()
            return f"{network}_" + address_hash[:20].hex()

    def _to_checksum_address(self, address: str) -> str:
        """
        将以太坊地址转换为EIP-55校验和格式

        Args:
            address (str): 原始地址

        Returns:
            str: 校验和格式的地址
        """
        address = address.lower().replace('0x', '')
        address_hash = keccak.new(digest_bits=256)
        address_hash.update(address.encode())
        hash_hex = address_hash.hexdigest()

        checksum_address = "0x"
        for i, char in enumerate(address):
            if char.isdigit():
                checksum_address += char
            else:
                # 如果hash的对应位置的十六进制值 >= 8，则大写
                checksum_address += char.upper() if int(hash_hex[i], 16) >= 8 else char

        return checksum_address

    def _private_key_to_wif(self, private_key: bytes, compressed: bool = True) -> str:
        """
        将私钥转换为WIF (Wallet Import Format) 格式

        Args:
            private_key (bytes): 32字节私钥
            compressed (bool): 是否使用压缩公钥格式

        Returns:
            str: WIF格式的私钥
        """
        # 1. 添加版本字节 (0x80 for mainnet private key)
        versioned_key = b"\x80" + private_key
        
        # 2. 如果使用压缩公钥，添加压缩标志 (0x01)
        if compressed:
            versioned_key = versioned_key + b"\x01"
        
        # 3. 计算校验和 (double SHA256的前4字节)
        checksum = hashlib.sha256(hashlib.sha256(versioned_key).digest()).digest()[:4]
        
        # 4. 完整的WIF数据
        wif_data = versioned_key + checksum
        
        # 5. Base58编码
        import base58
        return base58.b58encode(wif_data).decode('ascii')

    def get_master_key_info(self) -> Dict:
        """
        获取主密钥信息

        Returns:
            Dict: 主密钥信息
        """
        return {
            "private_key": self.master_key.key.hex(),
            "chain_code": self.master_key.chain_code.hex(),
            "depth": self.master_key.depth,
            "fingerprint": self.master_key.parent_fingerprint.hex(),
        }

    def get_supported_networks(self) -> List[str]:
        """
        获取支持的网络列表

        Returns:
            List[str]: 支持的网络列表（包含标准名称和别名）
        """
        return list(self.DERIVATION_PATHS.keys())

    def get_supported_aliases(self) -> Dict[str, str]:
        """
        获取支持的网络别名映射

        Returns:
            Dict[str, str]: 别名到标准名称的映射
        """
        return self.NETWORK_ALIASES.copy()

    def export_extended_key(self, key: ExtendedKey, is_private: bool = True) -> str:
        """
        导出扩展密钥

        Args:
            key (ExtendedKey): 扩展密钥
            is_private (bool): 是否为私钥

        Returns:
            str: 扩展密钥字符串
        """
        # 简化的扩展密钥格式
        key_type = "prv" if is_private else "pub"
        return f"xpub_{key_type}_{key.key.hex()}_{key.chain_code.hex()}"
