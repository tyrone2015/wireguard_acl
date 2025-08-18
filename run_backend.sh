#!/bin/bash
set -e

# 默认上游 DNS，可通过环境变量 UPSTREAM_DNS 指定（多个用空格分隔）
: ${UPSTREAM_DNS:="127.0.0.11"}

# 生成 dnsmasq 配置
DNSMASQ_CONF=/etc/dnsmasq.d/wireguard_acl.conf
mkdir -p /etc/dnsmasq.d
cat > ${DNSMASQ_CONF} <<EOF
# dnsmasq for wireguard_acl
# 监听所有接口，确保 REDIRECT 能被本地处理
listen-address=0.0.0.0
bind-interfaces
no-resolv
cache-size=1000
EOF

# 添加上游
for ns in ${UPSTREAM_DNS}; do
  echo "server=${ns}" >> ${DNSMASQ_CONF}
done

# 启动 dnsmasq
echo "Starting dnsmasq with upstream: ${UPSTREAM_DNS}"
rm -f /var/run/dnsmasq/dnsmasq.pid || true
dnsmasq --keep-in-foreground --conf-file=${DNSMASQ_CONF} &
DNSMASQ_PID=$!

# 确保 dnsmasq 已监听 53
sleep 0.5
ss -lntu | grep ':53' || true

# 启动 uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
