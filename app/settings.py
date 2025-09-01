import os
import ipaddress

# 默认 Peer IP 段，可通过环境变量或配置文件覆盖
PEER_IP_CIDR = os.environ.get('WG_PEER_IP_CIDR', '192.168.198.0/24')

# 全局 WireGuard 端点，可通过环境变量或配置文件覆盖
WG_GLOBAL_ENDPOINT = os.environ.get('WG_GLOBAL_ENDPOINT', '')

# 获取所有可用 IP
def get_available_peer_ips():
    net = ipaddress.ip_network(PEER_IP_CIDR)
    # Interface IP 默认取网段第一个可用地址
    interface_ip = str(list(net.hosts())[0])
    # 排除 Interface IP，避免冲突
    return [str(ip) for ip in net.hosts() if str(ip) != interface_ip]
