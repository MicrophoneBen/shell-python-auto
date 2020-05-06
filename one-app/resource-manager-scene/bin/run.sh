#!/bin/bash

cd `dirname $0`
#-------------------------------------------------------------------
# 定义变量
#-------------------------------------------------------------------
# 模块名
MODEL_NAME="resource-manager-scene"

# 选项
MODEL_OPTS="-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=8888"

# 运行包名
MODEL_JAR="resource-manager-scene-1.1.0.jar"

# 运行参数
MODEL_VARS="--spring.config.location=../conf/application.yml --logging.config=../conf/logback-spring.xml"

# JVM参数
JVM_VARS="-server -XX:MetaspaceSize=512m -XX:MaxMetaspaceSize=512m -Xms2g -Xmx2g -Duser.timezone=GMT+08"

# 前台/后台: 0-前台， 1-后台
MODEL_DAEMON=0

# 日志 '&-':表示关闭标准输出日志
MODEL_LOG="../logs/error.log"

# 应用启动所需要的依赖文件，填入后，启动应用会进行文件检查
APP_FILE=(../conf/application.yml ../conf/logback-spring.xml)
#-------------------------------------------------------------------
# 以下内容请不要修改
#-------------------------------------------------------------------

SLEEP_MIN=5

# model info can be define here
MODEL_SYMBOL=${MODEL_NAME}
GREP_KEY="Diname="${MODEL_SYMBOL}


#----------------------------------------------------------
# function print usage
#----------------------------------------------------------

print_usage()
{
echo ""
echo "h|H|help|HELP             ---Print help information."
echo "start                     ---Start the ${MODEL_NAME} server."
echo "stop                      ---Stop the ${MODEL_NAME} server."
echo "status                    ---Status the ${MODEL_NAME} server."
echo "restart                   ---Restart the ${MODEL_NAME} server."
}

#--------------------------------------------------------------
# the function to show jvm parameters of jvm, and allow user to modify
#--------------------------------------------------------------
modify_jvm_param(){
    echo "更新应用JVM启动参数"
    echo "请输入应用启动的最小堆内存空间 : "
    read Xms
    echo "请输入应用启动的最大堆内存空间 : "
    read Xmx
    echo "请输入应用的默认元数据空间大小 : "
    read MetaspaceSize
    echo "请输入应用最大的元数据空间大小 : "
    read MaxMetaspaceSize
    JVM_VARS="-server -XX:MetaspaceSize=${MetaspaceSize} -XX:MaxMetaspaceSize=${MaxMetaspaceSize} -Xms${Xms} -Xmx${Xmx} -Duser.timezone=GMT+08"
    echo "当前的应用JVM启动参数 $JVM_VARS"
}

modify_jvm_param_one_line(){
    echo "更新应用JVM启动参数, 请依次输入应用启动的 最小堆内存空间,最大堆内存空间,默认元数据空间大小,最大的元数据空间大小, 使用 "," 分隔"
    read jvmParams
    array=(${jvmParams//,/ })
    JVM_VARS="-server -XX:MetaspaceSize=${array[0]} -XX:MaxMetaspaceSize=${array[1]} -Xms${array[2]} -Xmx${array[3]}} -Duser.timezone=GMT+08"
    echo "当前的应用JVM启动参数 $JVM_VARS"
}
#-------------------------------------------------------------------
# function model_is_exist (兼容alpine)
#-------------------------------------------------------------------

modelService_is_exist()                                                                                       
{                                                                                                             
localServerId=`ps -ef |grep -w "${GREP_KEY}" | grep -v grep | awk '{print $2}'`                                                                               
if [[ -z "${localServerId}" ]]
then                                                                           
return 1                                                                       
else     
expr ${localServerId} + 0 &>/dev/null                                                                         
if [ $? -ne 0 ]                                                                                               
then                                                                                                          
localServerId=`ps -ef |grep -w "${GREP_KEY}" | grep -v grep | awk '{print $1}'`  
fi
echo "pid is ${localServerId}"   
return 0
fi
}

#-------------------------------------------------------------------
# function check_user_id
# return 0 ---- supper user
# return 1 ---- normal user
#-------------------------------------------------------------------

# check_user_id ()
# {
# localMyId=$(id|awk '{print $1}')
# localMyId=${localMyId:4:1}
# if [ "${localMyId}" -eq "0" ]
# then
# return 0
# else
# return 1
# fi
# }

#-------------------------------------------------------------------
# function statistic the jar component,
# return 0, only one jar and start project
# return 1, more than one jar and fail to start project
#-------------------------------------------------------------------
function statistic_jar_file(){
c=0
for file in `find $PWD -name "*.jar"`
do
file_list[$c]=${file}
((c++))
done
size=${#file_list[@]}
if [[ $size -gt "1" ]];then
  echo "应用启动目录下存在多于一个的应用jar包,读入失败,文件名如下"
    b=0
    for value in ${file_list[@]}
    do
      echo ${value}
    done
elif [[ $size -eq "1" ]];then
  echo "当前应用启动目录下有且仅有一个jar包，开始读入应用包启动===>>>"
fi
}

#-------------------------------------------------------------------
#function 当应用包多于两个时候，让用户输入决定启动的应用包版本
#-------------------------------------------------------------------
function chose_to_run(){
#获取应用启动版本号
version=${MODEL_JAR##*-}
version=${version%.*}
model_name=${MODEL_JAR%-*}
echo "当前启动的应用版本 ： $version"
if [[ $size -gt "1" ]];then
    echo "请输入应用启动的版本号 ： "
    read Args
    MODEL_JAR=$model_name-$Args.jar
fi
}

#-------------------------------------------------------------------
#function 检测应用包启动所需文件是否存在
#-------------------------------------------------------------------
function file_is_exist(){
    item=0
    ls $PWD | grep ${MODEL_JAR}
    if [[ $? -eq "0" ]]; then
       echo "即将启动的应用Jar包是 ： $MODEL_JAR"
    elif [[ $? -ne "0" ]];then
       echo "不存在该应用包 ： $MODEL_JAR，应用启动失败，请重新运行脚本"
       exit 2
    fi
    for item in ${APP_FILE[@]}
    do
      if [[ ! -f  "${item}" ]]; then
            echo "不存在该配置文件 $item，无法启动应用, 请检查配置文件后重试"
            exit 2
      fi
    done

}

#-------------------------------------------------------------------
# function model_start
#-------------------------------------------------------------------

model_start ()
{
modelService_is_exist
if [[ $? -eq "0" ]];then
        echo "${MODEL_NAME} is running yet. pid ${localServerId}."
        return 0
else
        if [[ $MODEL_DAEMON -eq "0" ]]
        then
                echo "try to start ${MODEL_NAME} ... foreground"
                $JAVA_HOME/bin/java -${GREP_KEY} ${MODEL_OPTS} -jar ${JVM_VARS} ${MODEL_JAR} ${MODEL_VARS}
        else
                echo "try to start ${MODEL_NAME} ... backgroud"
                nohup $JAVA_HOME/bin/java -${GREP_KEY} ${MODEL_OPTS} -jar ${JVM_VARS} ${MODEL_JAR} ${MODEL_VARS} 1>&- 2>>${MODEL_LOG} &
                sleep $SLEEP_MIN
                modelService_is_exist
                if [ $? -eq "0" ]
                then
                        echo "${MODEL_NAME} is running. pid ${localServerId}."
                        return 0
                else
                        echo "failed to start ${MODEL_NAME}! see the output log for more details."
                        return 1
                fi
        fi
fi
}

create_log_file()
{
 #创建文件夹
if [[ ! -d "${MODEL_LOG%/*}" ]]; then
    mkdir -p ${MODEL_LOG%/*}
fi
#创建文件
if [[ ! -f "${MODEL_LOG}" ]];then
    touch ${MODEL_LOG}
fi
}

#-------------------------------------------------------------------
# function model_stop
#-------------------------------------------------------------------

model_stop()
{
echo "try to stop ${MODEL_NAME} ..."
modelService_is_exist
if [ $? -eq 0 ]
then
kill -9 ${localServerId}
if [ $? -ne 0 ]
then
echo "failed to stop ${MODEL_NAME}!"
return 1
else
echo "${MODEL_NAME} stopped."
return 0
fi
else
echo "${MODEL_NAME} is not running!"
return 1
fi
}

#-------------------------------------------------------------------
# function model_status
#-------------------------------------------------------------------

model_status()
{
modelService_is_exist
if [ $? -eq 0 ]
then
echo "${MODEL_NAME} is running. pid ${localServerId}."
else
echo "${MODEL_NAME} is not running."
fi
}

#-------------------------------------------------------------------
#
#-------------------------------------------------------------------

#-------------------------------------------------------------------
# function parse_para
#-------------------------------------------------------------------

parse_para()
{
if [[ -n "$2" ]];then
#获取应用启动版本号
    version=${MODEL_JAR##*-}
    version=${version%.*}
    model_name=${MODEL_JAR%-*}
    Args="$2"
    MODEL_JAR=${model_name}-${Args}.jar
    echo "当前启动的应用包 ： ${MODEL_JAR}"
    file_is_exist
    create_log_file
    model_start
else
    case "$1" in
    START|Start|start)
        statistic_jar_file
        chose_to_run
        file_is_exist
        create_log_file
        model_start
        ;;
    STOP|Stop|stop) model_stop;;
    STATUS|status|status) model_status;;
    RESTART|Restart|restart)
        model_status
        MODEL_JAR=` ps -ef |grep ${localServerId}| grep -v grep | awk '{print $18}' `
        model_stop
        file_is_exist
        echo "${MODEL_JAR}"
        model_start
        ;;
    *) echo "illage parameter : $1";print_usage;;
    esac
fi
}

#-------------------------------------------------------------------
# main
#-------------------------------------------------------------------

echo "当前应用启动的默认JVM参数为 ： $JVM_VARS"
parse_para $1 $2

