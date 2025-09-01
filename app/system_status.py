from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from app.models import Peer, ACL, Activity, User
from app.auth import get_current_user
import psutil
import time
import subprocess
import os
import logging
from datetime import datetime, timedelta

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get('/system/stats')
def system_stats(current_user: User = Depends(get_current_user)):
    """返回基础的系统资源占用信息：CPU%、内存、磁盘、网络速率（单位：bytes/s）"""
    try:
        # CPU 百分比（按总体）
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # 内存使用情况
        mem = psutil.virtual_memory()
        mem_total = mem.total
        mem_used = mem.used
        mem_percent = mem.percent

        # 磁盘使用情况（根分区）
        disk = psutil.disk_usage('/')
        disk_total = disk.total
        disk_used = disk.used
        disk_percent = disk.percent

        # 网络速率：采样两次计算速率
        net1 = psutil.net_io_counters()
        time.sleep(0.5)
        net2 = psutil.net_io_counters()
        interval = 0.5
        bytes_sent_per_s = (net2.bytes_sent - net1.bytes_sent) / interval
        bytes_recv_per_s = (net2.bytes_recv - net1.bytes_recv) / interval

        data = {
            'cpu_percent': cpu_percent,
            'memory': {
                'total': mem_total,
                'used': mem_used,
                'percent': mem_percent
            },
            'disk': {
                'total': disk_total,
                'used': disk_used,
                'percent': disk_percent
            },
            'network': {
                'bytes_sent_per_s': bytes_sent_per_s,
                'bytes_recv_per_s': bytes_recv_per_s
            }
        }

        return JSONResponse(content=data)

    except Exception as e:
        logger.error(f"获取系统统计信息时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail="获取系统统计失败")


@router.get('/system/advanced-stats')
def advanced_system_stats(current_user: User = Depends(get_current_user)):
    """返回高级系统统计信息"""
    try:
        from app.main import SessionLocal
        session = SessionLocal()

        # 数据库统计
        peer_count = session.query(Peer).count()
        active_peer_count = session.query(Peer).filter_by(status=True).count()
        acl_count = session.query(ACL).count()
        enabled_acl_count = session.query(ACL).filter_by(enabled=True).count()

        # 活动统计（最近24小时）
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_activities = session.query(Activity).filter(
            Activity.created_at >= yesterday
        ).count()

        session.close()

        # WireGuard接口统计
        wg_stats = get_wireguard_stats()

        # 进程统计
        process_stats = get_process_stats()

        data = {
            'database': {
                'total_peers': peer_count,
                'active_peers': active_peer_count,
                'total_acls': acl_count,
                'enabled_acls': enabled_acl_count,
                'recent_activities': recent_activities
            },
            'wireguard': wg_stats,
            'processes': process_stats,
            'timestamp': datetime.utcnow().isoformat()
        }

        return JSONResponse(content=data)

    except Exception as e:
        logger.error(f"获取高级系统统计时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail="获取高级统计失败")


def get_wireguard_stats():
    """获取WireGuard接口统计"""
    try:
        # 检查WireGuard接口状态
        result = subprocess.run(['wg', 'show', 'wg0'], capture_output=True, text=True)
        if result.returncode != 0:
            return {'status': 'down', 'peers': 0, 'transfer': {'rx': 0, 'tx': 0}}

        # 解析wg show输出
        lines = result.stdout.strip().split('\n')
        peer_count = 0
        total_rx = 0
        total_tx = 0

        for line in lines:
            if 'peer:' in line:
                peer_count += 1
            elif 'transfer:' in line:
                # 解析传输数据
                parts = line.split()
                if len(parts) >= 3:
                    rx_str = parts[1].replace(',', '')
                    tx_str = parts[2].replace(',', '')
                    try:
                        total_rx += int(rx_str)
                        total_tx += int(tx_str)
                    except ValueError:
                        pass

        return {
            'status': 'up',
            'peers': peer_count,
            'transfer': {
                'rx': total_rx,
                'tx': total_tx
            }
        }

    except Exception as e:
        logger.warning(f"获取WireGuard统计失败: {str(e)}")
        return {'status': 'error', 'peers': 0, 'transfer': {'rx': 0, 'tx': 0}}


def get_process_stats():
    """获取进程统计"""
    try:
        # 获取Python进程信息
        python_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if 'python' in proc.info['name'].lower():
                    python_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_percent': proc.info['memory_percent']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return {
            'python_processes': python_processes,
            'total_python_processes': len(python_processes)
        }

    except Exception as e:
        logger.warning(f"获取进程统计失败: {str(e)}")
        return {'python_processes': [], 'total_python_processes': 0}


@router.get('/system/performance-history')
def get_performance_history(hours: int = 24, current_user: User = Depends(get_current_user)):
    """获取性能历史数据"""
    try:
        # 这里可以实现历史数据收集和存储
        # 目前返回实时数据作为示例
        current_stats = system_stats(current_user)

        # 模拟历史数据（实际应用中应该从数据库或时间序列数据库获取）
        history_data = {
            'period': f'{hours} hours',
            'data_points': 1,
            'current': current_stats.body.decode() if hasattr(current_stats, 'body') else current_stats,
            'note': '历史数据功能待实现'
        }

        return JSONResponse(content=history_data)

    except Exception as e:
        logger.error(f"获取性能历史时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail="获取性能历史失败")


@router.get('/system/health-detailed')
def detailed_health_check(current_user: User = Depends(get_current_user)):
    """详细健康检查"""
    try:
        health_status = {
            'overall': 'healthy',
            'checks': {},
            'timestamp': datetime.utcnow().isoformat()
        }

        # 数据库连接检查
        try:
            from app.main import SessionLocal
            session = SessionLocal()
            session.execute("SELECT 1")
            session.close()
            health_status['checks']['database'] = {'status': 'ok', 'message': '数据库连接正常'}
        except Exception as e:
            health_status['checks']['database'] = {'status': 'error', 'message': str(e)}
            health_status['overall'] = 'unhealthy'

        # WireGuard服务检查
        wg_stats = get_wireguard_stats()
        if wg_stats['status'] == 'up':
            health_status['checks']['wireguard'] = {'status': 'ok', 'message': 'WireGuard服务正常'}
        else:
            health_status['checks']['wireguard'] = {'status': 'warning', 'message': 'WireGuard服务未运行'}
            if health_status['overall'] == 'healthy':
                health_status['overall'] = 'degraded'

        # 系统资源检查
        mem = psutil.virtual_memory()
        if mem.percent > 90:
            health_status['checks']['memory'] = {'status': 'error', 'message': f'内存使用率过高: {mem.percent}%'}
            health_status['overall'] = 'unhealthy'
        elif mem.percent > 80:
            health_status['checks']['memory'] = {'status': 'warning', 'message': f'内存使用率较高: {mem.percent}%'}
            if health_status['overall'] == 'healthy':
                health_status['overall'] = 'degraded'
        else:
            health_status['checks']['memory'] = {'status': 'ok', 'message': f'内存使用正常: {mem.percent}%'}

        # 磁盘空间检查
        disk = psutil.disk_usage('/')
        if disk.percent > 90:
            health_status['checks']['disk'] = {'status': 'error', 'message': f'磁盘使用率过高: {disk.percent}%'}
            health_status['overall'] = 'unhealthy'
        elif disk.percent > 80:
            health_status['checks']['disk'] = {'status': 'warning', 'message': f'磁盘使用率较高: {disk.percent}%'}
            if health_status['overall'] == 'healthy':
                health_status['overall'] = 'degraded'
        else:
            health_status['checks']['disk'] = {'status': 'ok', 'message': f'磁盘使用正常: {disk.percent}%'}

        return JSONResponse(content=health_status)

    except Exception as e:
        logger.error(f"详细健康检查时发生错误: {str(e)}")
        return JSONResponse(content={
            'overall': 'error',
            'checks': {'system': {'status': 'error', 'message': str(e)}},
            'timestamp': datetime.utcnow().isoformat()
        })
