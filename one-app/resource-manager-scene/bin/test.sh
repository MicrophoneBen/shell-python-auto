#!/usr/bin/env bash

find $PWD -name "*.jar"




parse_para()
{
case "$1" in
start) model_start;;
stop) model_stop;;
status) model_status;;
*) echo "illage parameter : $1";print_usage;;
esac
}

parse_para
echo "更新应用JVM启动参数, 请依次输入应用启动的 最小堆内存空间,最大堆内存空间,默认元数据空间大小,最大的元数据空间大小。使用","分隔"