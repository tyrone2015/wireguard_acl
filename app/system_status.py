from fastapi import APIRouter
from fastapi.responses import JSONResponse
import psutil
import time

router = APIRouter()

@router.get('/system/stats')
def system_stats():
    """返回基础的系统资源占用信息：CPU%、内存、磁盘、网络速率（单位：bytes/s）"""
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
