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


modify_jvm_param_one_line(){
    echo "更新应用JVM启动参数, 请依次输入应用启动的 最小堆内存空间,最大堆内存空间,默认元数据空间大小,最大的元数据空间大小, 使用 "," 分隔"
    read jvmParams
    array=(${jvmParams//,/ })
    JVM_VARS="-server -XX:MetaspaceSize=${array[0]} -XX:MaxMetaspaceSize=${array[1]} -Xms${array[2]} -Xmx${array[3]}} -Duser.timezone=GMT+08"
    echo "当前的应用JVM启动参数 $JVM_VARS"
}

echo "更新应用JVM启动参数, 请依次输入应用启动的 最小堆内存空间,最大堆内存空间,默认元数据空间大小,最大的元数据空间大小。使用","分隔"
modify_jvm_param_one_line