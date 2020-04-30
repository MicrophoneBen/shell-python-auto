#!/bin/bash

#环境检查
# 检是否已安装java
java -version
if [ $? -gt 1 ];then
   echo "请安装java1.8或以上版本！"
   exit 1
fi


parentDir=`dirname $0`
path2=`cd $parentDir;pwd`
root_dir=`dirname $0`
install_dir=`cd $path2;cd ../;pwd`

cd $install_dir

echo "install_dir=${install_dir}"


#获取版本号，版本号必填！
version=`(cat ${install_dir}/conf/common-config.properties | grep "version=" | awk -F'=' '{ print $2 }' | sed s/[[:space:]]//g)`

if [ -z "$version"  ];then

  echo "请指定配置文件：${install_dir}/conf/common-config.properties的系统版本号"
  exit 1
fi


#获取服务安装路径
deploy_dir=`(cat ${install_dir}/conf/common-config.properties | grep "deploy.soft.dir=" | awk -F'=' '{ print $2 }' | sed s/[[:space:]]//g)`

if [ -z "$deploy_dir"  ];then

  deploy_dir="/opt/dataworks"
  echo "安装目录没有指定，默认安装目录为:${deploy_dir}"

else
  #添加dataworks目录
  deploy_dir="${deploy_dir}/dataworks"

  echo "安装路径为：${deploy_dir}"

fi


#如果安装路径不存在则创建
if [ ! -d ${deploy_dir} ]; then
 mkdir -p ${deploy_dir}

fi

dts_deploy_dir="${deploy_dir}/dts"

if [ ! -d ${dts_deploy_dir} ]; then
#创建dts目录
  mkdir -p ${dts_deploy_dir}

fi




#设置datax/data-rule-check安装路径变量job-engine通过环境变量获取执行脚本

export_var="export DTS_SCRIPT_ROOT_PATH=${dts_deploy_dir}"
if ! cat /etc/profile | grep "export DTS_SCRIPT_ROOT_PATH=">/dev/null; then
  echo "export DTS_SCRIPT_ROOT_PATH=${dts_deploy_dir}" >> /etc/profile
else
  sed -i "/^export DTS_SCRIPT_ROOT_PATH=/c${export_var}" /etc/profile
fi

#获取日志文件根目录
deploy_log_dir=`(cat ${install_dir}/conf/common-config.properties | grep "deploy.log.dir=" | awk -F'=' '{ print $2 }' | sed s/[[:space:]]//g)`

if [ -z "$deploy_log_dir"  ];then

  deploy_log_dir="/var/log/dataworks/logs"
  echo "安装目录没有指定，默认安装目录为:${deploy_log_dir}"

else
  #添加dataworks目录
  deploy_log_dir="${deploy_log_dir}/dataworks/logs"

  echo "日志文件路径为：${deploy_log_dir}"

fi

#如果日志文件路径不存在则创建
if [ ! -d ${deploy_log_dir} ]; then
 mkdir -p ${deploy_log_dir}

fi

dts_deploy_log_dir="${deploy_log_dir}/dts"

if [ ! -d ${dts_deploy_log_dir} ]; then
 mkdir -p ${dts_deploy_log_dir}

fi


# 设置log目录的环境变量，在启动脚本中获取环境变量设置系统变量
export_log_var="export DTS_LOG_ROOT_PATH=${dts_deploy_log_dir}"
if ! cat /etc/profile | grep "export DTS_LOG_ROOT_PATH=">/dev/null; then
  echo "export DTS_LOG_ROOT_PATH=${dts_deploy_log_dir}" >> /etc/profile
else
  sed -i "/^export DTS_LOG_ROOT_PATH=/c${export_log_var}" /etc/profile
fi

export_version_var="export DTS_VERSION=${version}"
if ! cat /etc/profile | grep "export DTS_VERSION=">/dev/null; then
  echo "export DTS_VERSION=${version}" >> /etc/profile
else
  sed -i "/^export DTS_VERSION=/c${export_version_var}" /etc/profile
fi

source /etc/profile

# 初始化配置
echo "初始化配置"
python ${install_dir}/sh/install.py "dts-console"

if [ $? != 0 ]; then
  echo "初始化配置失败"
  exit 1
fi

#安装服务

#安装dts-console
if [ ! -f ${install_dir}/dts-console-${version}.tar.gz ]; then
  echo "${install_dir}/dts-console-${version}.tar.gz 不存在"
  exit 1
else
    echo "开始安装dts-console-${version}"
        rm -rf ${dts_deploy_dir}/dts-console
        tar -zxf ${install_dir}/dts-console-${version}.tar.gz -C ${dts_deploy_dir}/
fi

# 替换文件dts-console的application.properties
cp -f config-template/dts.console.application.properties ${dts_deploy_dir}/dts-console/conf/application.properties

echo "启动dts-console ..."
sh ${dts_deploy_dir}/dts-console/bin/run.sh stop
sh ${dts_deploy_dir}/dts-console/bin/run.sh start

echo "启动完成！"

echo "添加开机自启动..."
if [ -f "/etc/init.d/DtsConsoleAutoStart" ];then
  chmod +x /etc/init.d/DtsConsoleAutoStart
  chkconfig --add /etc/init.d/DtsConsoleAutoStart
  echo "添加dts-console自启动成功"
else
  touch /etc/init.d/DtsConsoleAutoStart
  echo '#!/bin/sh' > /etc/init.d/DtsConsoleAutoStart
  echo '# chkconfig: 2345 10 90' >> /etc/init.d/DtsConsoleAutoStart
  echo '# description: console启动命令...' >> /etc/init.d/DtsConsoleAutoStart
  echo "sh ${dts_deploy_dir}/dts-console/bin/run.sh start >/dev/null 2>/dev/null" >> /etc/init.d/DtsConsoleAutoStart
  chmod +x /etc/init.d/DtsConsoleAutoStart
  chkconfig --add /etc/init.d/DtsConsoleAutoStart
  echo "添加das-console自启动成功"
fi


#添加定时检查任务，每30分钟检查，不存在则启动
cat /var/spool/cron/root |grep "${dts_deploy_dir}/dts-console/bin/run.sh start"
if [ $? -ne 0  ];then
  echo "添加定时检查任务，每30分钟检查，不存在则启动"
  if [ ! -d "${dts_deploy_log_dir}/dts-console" ]; then
     mkdir ${dts_deploy_log_dir}/dts-console
  fi
  echo "dts_deploy_log_dir = ${dts_deploy_log_dir}"
  echo "*/30 * * * * source /etc/profile;sh ${dts_deploy_dir}/dts-console/bin/run.sh start > ${dts_deploy_log_dir}/dts-console/check.log  2>&1" >> /var/spool/cron/root
fi

echo "安装结束"