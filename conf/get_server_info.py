#!/usr/bin/python
# coding:utf-8

"""
采集机器自身信息
1 主机名
2 IP信息
3 内存
4 cpu信息
5 磁盘信息
6 制造商信息
7 出厂日期
8 系统版本
"""
import socket
import subprocess
import time
import platform
import json
import os
import re
import math

def get_hostname():
    return socket.gethostname()

def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def get_meminfo():
    with open("/proc/meminfo") as f:
        tmp = int(f.readline().split()[1])
        return num_format(tmp)

def get_cpu_info():
    ret = {'cpu':'','num':0}
    with open('/proc/cpuinfo') as f:
        for line in f:
            tmp = line.split(":")
            key = tmp[0].strip()
            if key == "processor":
                ret['num'] += 1
            if key == "model name":
                ret['cpu'] = tmp[1].strip()
    return ret

def dev_phy_size():
  ret = {}
  with open('/proc/partitions','r') as dp:
    res = ''
    for disk in dp.readlines():
      if re.search(r'[s,h,v]d[a-z]\n',disk):
        blknum = disk.strip().split(' ')[-2]
        dev = disk.strip().split(' ')[-1]
        size = int(blknum)*1024
        ret[dev]=humanize_bytes(size,2).strip()
    return ret

# 获取制造商信息
def get_manufacturer_info():
    ret = {}
    cmd = """/usr/sbin/dmidecode | grep -A6 'System Information'"""
    manufacturer_data = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE, stderr=subprocess.STDOUT)

    for line in manufacturer_data.stdout.readlines():
        if 'Manufacturer' in line:
            ret['manufacturers'] = line.split(':')[1].strip()
        elif 'Product Name' in line:
            ret['server_type'] = line.split(':')[1].strip()
        elif 'Serial Number' in line:
            ret['st'] = line.split(':')[1].strip()
        elif 'UUID' in line:
            ret['uuid'] = line.split(':')[1].strip()
    return ret

# 获取出厂日期
def get_real_date():
    cmd = """/usr/sbin/dmidecode | grep -i release"""
    date_data = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    real_date = date_data.stdout.readline().split(':')[1].strip()
    return time.strftime('%Y-%m-%d', time.strptime(real_date, "%m/%d/%Y"))

def get_os_version():
    return ' '.join(platform.linux_distribution())

# 将内存占用的数字带上单位
def num_format(num):
    num = int(num)
    o = 'KB'
    if num > 1024 * 1024:
        num /= 1024 * 1024.0
        o = 'GB'
        return '%.0f%s' % (math.ceil(num), o)
    elif num > 1024:
        num /= 1024.0
        o = 'MB'
        return '%.0f%s' % (math.ceil(num), o)

    return '%.0f%s' % (num, o)

def humanize_bytes(bytesize, precision=0):
    abbrevs = (
        (10**15, 'PB'),
        (10**12, 'TB'),
        (10**9, 'GB'),
        (10**6, 'MB'),
        (10**3, 'kB'),
        (1, 'bytes')
    )
    if bytesize == 1:
        return '1 byte'
    for factor, suffix in abbrevs:
        if bytesize >= factor:
            break
    return '%.*f%s' % (precision, float(bytesize) / factor, suffix)

def run():
    data = {}
    data["hostname"] = get_hostname()
    data["osVersion"] = get_os_version()
    data["ip"]=get_host_ip()
    cpu_info = get_cpu_info()
    data["cpuInfo"] = "{cpu} * {num}".format(**cpu_info)
    data["memInfo"] = get_meminfo()
    data["diskInfo"] = dev_phy_size()
    # data["manufacture_date"] = get_real_date()
    # data.update(get_manufacturer_info())

    print(data)

if __name__ == "__main__":
    run()