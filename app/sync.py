import os
import subprocess
from sqlalchemy.orm import sessionmaker
from app.models import Peer, ACL, ServerKey
WG_SERVER_PRIVATE_KEY_PATH = os.environ.get('WG_SERVER_PRIVATE_KEY_PATH', '/etc/wireguard/server_private.key')

WG_CONFIG_PATH = os.environ.get('WG_CONFIG_PATH', '/etc/wireguard/wg0.conf')
WG_INTERFACE = os.environ.get('WG_INTERFACE', 'wg0')

def generate_wg_config():
	from app.main import SessionLocal
	session = SessionLocal()
	peers = session.query(Peer).filter_by(status=True).all()
	acls = session.query(ACL).filter_by(enabled=True).all()
	# 获取服务端密钥
	server_key = session.query(ServerKey).first()
	if not server_key:
		# 自动生成
		print("[日志] 数据库无服务端密钥，自动生成...")
		private_key = subprocess.check_output(['wg', 'genkey']).decode().strip()
		public_key = subprocess.check_output(['wg', 'pubkey'], input=private_key.encode()).decode().strip()
		server_key = ServerKey(public_key=public_key, private_key=private_key)
		session.add(server_key)
		session.commit()
	server_private_key = server_key.private_key
	session.close()
	# 生成 PostUp/PostDown iptables 规则
	post_up_cmds, post_down_cmds = apply_acl_to_iptables(acls)
	post_up = " && ".join(post_up_cmds) if post_up_cmds else ""
	post_down = " && ".join(post_down_cmds) if post_down_cmds else ""

	config = [f"[Interface]\nPrivateKey = {server_private_key}\nAddress = 10.0.0.1/24\nListenPort = 51820\n" + (f"PostUp = {post_up}\n" if post_up else "") + (f"PostDown = {post_down}\n" if post_down else "")]
	for p in peers:
		remark = p.remark or ''
		peer_ip = p.peer_ip if hasattr(p, 'peer_ip') and p.peer_ip else ''
		endpoint = p.endpoint if hasattr(p, 'endpoint') and p.endpoint else ''
		keepalive = p.keepalive if hasattr(p, 'keepalive') and p.keepalive else 30
		# 构造 AllowedIPs，始终以 peer_ip/32 开头，后续追加自定义 allowed_ips
		allowed_ips_list = []
		if peer_ip:
			allowed_ips_list.append(f"{peer_ip}/32")
		if p.allowed_ips:
			# 去除重复的 peer_ip/32
			custom_ips = [ip.strip() for ip in p.allowed_ips.split(',') if ip.strip() and ip.strip() != f"{peer_ip}/32"]
			allowed_ips_list.extend(custom_ips)
		allowed_ips_str = ', '.join(allowed_ips_list)
		peer_config = f"[Peer]\n# {remark}\nPublicKey = {p.public_key}\n"
		if hasattr(p, 'preshared_key') and p.preshared_key:
			peer_config += f"PresharedKey = {p.preshared_key}\n"
		peer_config += f"AllowedIPs = {allowed_ips_str}\n"
		# if endpoint:
		# 	peer_config += f"Endpoint = {endpoint}\n"
		peer_config += f"PersistentKeepalive = {keepalive}\n"
		config.append(peer_config)
	return '\n'.join(config)

def generate_preshared_key():
	return subprocess.check_output(['wg', 'genpsk']).decode().strip()

def write_wg_config():
	config_text = generate_wg_config()
	with open(WG_CONFIG_PATH, 'w') as f:
		f.write(config_text)
	# 修正权限为 600，避免 world accessible 警告
	try:
		os.chmod(WG_CONFIG_PATH, 0o600)
	except Exception as e:
		print(f"警告: 设置 {WG_CONFIG_PATH} 权限失败: {e}")

def remove_old_wg_config():
	if os.path.exists(WG_CONFIG_PATH):
		try:
			print(f"[日志] 删除旧的 WireGuard 配置文件: {WG_CONFIG_PATH}")
			os.remove(WG_CONFIG_PATH)
			print(f"已删除旧的 WireGuard 配置文件: {WG_CONFIG_PATH}")
		except Exception as e:
			print(f"删除旧配置文件失败: {e}")

def reload_wireguard(action):
	try:
		# 检查 wg-quick 是否存在
		wg_quick_path = None
		for path in ['/usr/bin/wg-quick', '/bin/wg-quick']:
			if os.path.exists(path):
				wg_quick_path = path
				break
		if not wg_quick_path:
			print("警告: wg-quick 命令不存在，跳过 WireGuard 重载")
			return False
		# 检查配置文件是否存在，决定是否执行 down
		if os.path.exists(WG_CONFIG_PATH):
			try:
				print(f"[日志] 执行: {wg_quick_path} down {WG_INTERFACE}")
				if action == 'down':
					subprocess.run([wg_quick_path, "down", WG_INTERFACE], check=True, capture_output=True)
			except subprocess.CalledProcessError as e:
				# 忽略 'is not a WireGuard interface' 错误
				if b'is not a WireGuard interface' in e.stderr:
					print(f"忽略: {WG_INTERFACE} 不是已激活的 WireGuard 接口")
				else:
					print(f"wg-quick down 错误: {e.stderr.decode().strip()}")
		print(f"[日志] 执行: {wg_quick_path} up {WG_INTERFACE}")
		if action == 'up':
			subprocess.run([wg_quick_path, "up", WG_INTERFACE], check=True)
		return True
	except Exception as e:
		print(f"WireGuard 重载失败: {e}")
		return False

# 防火墙 规则转 iptables 命令，并返回 PostUp/PostDown 命令列表

# 自动获取默认出口网卡名
def get_default_interface():
	import re
	try:
		route_info = subprocess.check_output("ip route | grep default", shell=True).decode()
		match = re.search(r'dev (\S+)', route_info)
		if match:
			return match.group(1)
	except Exception as e:
		print(f"自动获取网卡失败: {e}")
	return "eth0"  # 默认回退

def apply_acl_to_iptables(acls):
	"""
	为 WireGuard 生成基于专用链 (WG_ACL) 的 iptables PostUp/PostDown 命令列表。

	设计要点：
	- 使用单独链 WG_ACL 来管理规则，便于一次性 flush/删除
	- 在 FORWARD 链上把 wg 接口到出口接口的流量跳转到 WG_ACL
	- 链内顺序： conntrack(ESTABLISHED,RELATED) -> per-ACL allow/deny -> 默认 DROP
	- 为 NAT 表添加 POSTROUTING MASQUERADE
	- 返回的命令已尽量使用容错写法（在 shell 中运行时不会因已存在而失败）
	"""
	post_up_cmds = []
	post_down_cmds = []

	iface = get_default_interface()
	# 1) 创建并清空专用链
	post_up_cmds.append("iptables -N WG_ACL 2>/dev/null || true")
	post_up_cmds.append("iptables -F WG_ACL")
	# 2) 在 FORWARD 链前端插入跳转，仅针对 wg -> iface 的流量
	post_up_cmds.append(f"iptables -I FORWARD 1 -i {WG_INTERFACE} -o {iface} -j WG_ACL")
	post_down_cmds.append(f"iptables -D FORWARD -i {WG_INTERFACE} -o {iface} -j WG_ACL 2>/dev/null || true")

	# 3) 链内基础规则：允许已建立连接的回包
	post_up_cmds.append("iptables -A WG_ACL -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT")
	post_down_cmds.insert(0, "iptables -F WG_ACL 2>/dev/null || true")

	# 4) 按 ACL 生成 allow/deny 规则
	from app.main import SessionLocal
	session = SessionLocal()
	peer_map = {p.id: p.peer_ip for p in session.query(Peer).all()}
	session.close()

	for acl in acls:
		if acl.action not in ["allow", "deny"]:
			continue
		if not getattr(acl, 'enabled', True):
			continue
		
		# 处理全局规则（peer_id为-1）和特定节点规则
		if acl.peer_id == -1:
			# 全局规则：为所有活跃节点应用
			target_peers = session.query(Peer).filter_by(status=True).all()
			peer_ips = [p.peer_ip for p in target_peers if p.peer_ip]
		else:
			# 特定节点规则
			peer_ip = peer_map.get(acl.peer_id)
			if not peer_ip:
				print(f"[日志] 跳过 ACL(id={acl.id}), 未找到对应 Peer IP")
				continue
			peer_ips = [peer_ip]
		
		# 为每个目标节点生成规则
		for peer_ip in peer_ips:
			direction = getattr(acl, 'direction', 'both') or 'both'
			
			target = acl.target
			port = getattr(acl, 'port', None) or ""
			protocol = getattr(acl, 'protocol', None) or ""
			# normalize '*' or 'all' to empty -> means all protocols (no -p)
			if isinstance(protocol, str) and protocol.strip() in ("*", "all"):
				protocol = ""

			proto_opt = f"-p {protocol.lower()}" if protocol else ""
			port_opt = ""
			if port and port != "*":
				if "-" in port:
					start, end = port.split('-', 1)
					port_opt = f"--dport {start}:{end}"
				else:
					port_opt = f"--dport {port}"

			# 根据方向生成不同的iptables规则
			if direction == 'inbound':
				# 入口方向：从外部进入WireGuard网络的流量
				base = f"-d {peer_ip} -s {target} -i {iface} -o {WG_INTERFACE}"
				if port_opt:
					# 对于入口流量，使用--dport匹配目标端口
					port_opt = port_opt.replace('--dport', '--dport')
			elif direction == 'outbound':
				# 出口方向：从WireGuard网络出去的流量
				base = f"-s {peer_ip} -d {target} -i {WG_INTERFACE} -o {iface}"
				if port_opt:
					# 对于出口流量，使用--dport匹配目标端口
					port_opt = port_opt.replace('--dport', '--dport')
			else:  # both
				# 双向流量：分别处理入口和出口
				# 入口方向
				base_in = f"-d {peer_ip} -s {target} -i {iface} -o {WG_INTERFACE}"
				# 出口方向
				base_out = f"-s {peer_ip} -d {target} -i {WG_INTERFACE} -o {iface}"
				
				if acl.action == 'allow':
					# 入口规则
					cmd_in = f"iptables -A WG_ACL {base_in} {proto_opt} {port_opt} -j ACCEPT"
					post_up_cmds.append(cmd_in.strip())
					post_down_cmds.append(f"iptables -D WG_ACL {base_in} {proto_opt} {port_opt} -j ACCEPT 2>/dev/null || true")
					
					# 出口规则
					cmd_out = f"iptables -A WG_ACL {base_out} {proto_opt} {port_opt} -j ACCEPT"
					post_up_cmds.append(cmd_out.strip())
					post_down_cmds.append(f"iptables -D WG_ACL {base_out} {proto_opt} {port_opt} -j ACCEPT 2>/dev/null || true")
				else:  # deny
					# 入口规则
					cmd_in = f"iptables -A WG_ACL {base_in} {proto_opt} {port_opt} -j DROP"
					post_up_cmds.append(cmd_in.strip())
					post_down_cmds.append(f"iptables -D WG_ACL {base_in} {proto_opt} {port_opt} -j DROP 2>/dev/null || true")
					
					# 出口规则
					cmd_out = f"iptables -A WG_ACL {base_out} {proto_opt} {port_opt} -j DROP"
					post_up_cmds.append(cmd_out.strip())
					post_down_cmds.append(f"iptables -D WG_ACL {base_out} {proto_opt} {port_opt} -j DROP 2>/dev/null || true")
				continue

			if acl.action == 'allow':
				cmd = f"iptables -A WG_ACL {base} {proto_opt} {port_opt} -j ACCEPT"
				post_up_cmds.append(cmd.strip())
				# 对应删除命令（尽量容错）
				post_down_cmds.append(f"iptables -D WG_ACL {base} {proto_opt} {port_opt} -j ACCEPT 2>/dev/null || true")
			else:  # deny
				cmd = f"iptables -A WG_ACL {base} {proto_opt} {port_opt} -j DROP"
				post_up_cmds.append(cmd.strip())
				post_down_cmds.append(f"iptables -D WG_ACL {base} {proto_opt} {port_opt} -j DROP 2>/dev/null || true")

	# 5) 链末默认 DROP，确保未匹配的流量被拒绝
	post_up_cmds.append("iptables -A WG_ACL -j DROP")
	post_down_cmds.append("iptables -F WG_ACL 2>/dev/null || true")

	# 6) NAT MASQUERADE：对整个 WireGuard peer 网段进行 SNAT
	try:
		import app.settings as _settings
		wg_cidr = _settings.PEER_IP_CIDR
	except Exception:
		wg_cidr = '10.0.0.0/24'

	# 使用 -C 检查是否已存在（以避免重复），在某些系统上 -C 不可用时回退到追加
	check_masq = f"iptables -t nat -C POSTROUTING -s {wg_cidr} -o {iface} -j MASQUERADE 2>/dev/null || iptables -t nat -A POSTROUTING -s {wg_cidr} -o {iface} -j MASQUERADE"
	post_up_cmds.append(check_masq)
	post_down_cmds.insert(0, f"iptables -t nat -D POSTROUTING -s {wg_cidr} -o {iface} -j MASQUERADE 2>/dev/null || true")

	# 7) 删除链和清理操作
	post_down_cmds.append(f"iptables -D FORWARD -i {WG_INTERFACE} -o {iface} -j WG_ACL 2>/dev/null || true")
	post_down_cmds.append("iptables -F WG_ACL 2>/dev/null || true")
	post_down_cmds.append("iptables -X WG_ACL 2>/dev/null || true")

	return post_up_cmds, post_down_cmds

def sync_wireguard():
	success = reload_wireguard('down')
	remove_old_wg_config()
	write_wg_config()
	success = reload_wireguard('up')
	return success

def sync_acl_and_wireguard():
	wg_success = sync_wireguard()
	return wg_success

