import pytest
from cryptography.fernet import Fernet
from app.peer import encrypt_private_key, decrypt_private_key, generate_wg_keypair, validate_allowed_ips


class TestCrypto:
    """加密功能测试"""

    def test_generate_wg_keypair(self):
        """测试WireGuard密钥对生成"""
        public_key, private_key = generate_wg_keypair()

        # 验证密钥格式（base64编码，44字符）
        assert len(public_key) == 44
        assert len(private_key) == 44

        # 验证都是有效的base64
        import base64
        assert base64.b64decode(public_key)
        assert base64.b64decode(private_key)

    def test_encrypt_decrypt_private_key(self):
        """测试私钥加密解密"""
        # 生成测试密钥
        _, private_key = generate_wg_keypair()

        # 加密
        encrypted = encrypt_private_key(private_key)
        assert encrypted != private_key
        assert isinstance(encrypted, str)

        # 解密
        decrypted = decrypt_private_key(encrypted)
        assert decrypted == private_key

    def test_encrypt_decrypt_consistency(self):
        """测试多次加密解密的一致性"""
        _, private_key = generate_wg_keypair()

        # 多次加密应该产生不同结果
        encrypted1 = encrypt_private_key(private_key)
        encrypted2 = encrypt_private_key(private_key)
        assert encrypted1 != encrypted2

        # 但解密应该得到相同结果
        decrypted1 = decrypt_private_key(encrypted1)
        decrypted2 = decrypt_private_key(encrypted2)
        assert decrypted1 == decrypted2 == private_key


class TestValidation:
    """验证功能测试"""

    def test_validate_allowed_ips_valid(self):
        """测试有效IP验证"""
        valid_ips = [
            "192.168.1.0/24",
            "10.0.0.1/32",
            "172.16.0.0/16",
            "192.168.1.1/32, 192.168.2.0/24"
        ]

        for ip in valid_ips:
            assert validate_allowed_ips(ip)

    def test_validate_allowed_ips_invalid(self):
        """测试无效IP验证"""
        invalid_ips = [
            "invalid_ip",
            "192.168.1.256/24",
            "192.168.1.0/33",
            "not_an_ip",
            ""
        ]

        for ip in invalid_ips:
            assert not validate_allowed_ips(ip)

    def test_validate_allowed_ips_edge_cases(self):
        """测试边界情况"""
        # 单IP
        assert validate_allowed_ips("192.168.1.1")

        # CIDR边界
        assert validate_allowed_ips("0.0.0.0/0")
        assert validate_allowed_ips("255.255.255.255/32")

        # 多个IP用逗号分隔
        assert validate_allowed_ips("192.168.1.0/24, 10.0.0.0/8")


class TestKeyManagement:
    """密钥管理测试"""

    def test_key_uniqueness(self):
        """测试密钥唯一性"""
        keys = set()
        for _ in range(10):
            public_key, private_key = generate_wg_keypair()
            # 确保公钥唯一
            assert public_key not in keys
            keys.add(public_key)

    def test_key_format_consistency(self):
        """测试密钥格式一致性"""
        for _ in range(5):
            public_key, private_key = generate_wg_keypair()

            # 验证字符集（base64字符）
            import string
            valid_chars = string.ascii_letters + string.digits + "+/="
            assert all(c in valid_chars for c in public_key)
            assert all(c in valid_chars for c in private_key)

            # 验证长度
            assert len(public_key) == 44  # base64编码32字节
            assert len(private_key) == 44  # base64编码32字节

    def test_encryption_error_handling(self):
        """测试加密错误处理"""
        # 测试空字符串
        with pytest.raises(Exception):
            encrypt_private_key("")

        # 测试无效密钥
        with pytest.raises(Exception):
            encrypt_private_key("invalid_key")

        # 测试解密无效数据
        with pytest.raises(Exception):
            decrypt_private_key("invalid_encrypted_data")