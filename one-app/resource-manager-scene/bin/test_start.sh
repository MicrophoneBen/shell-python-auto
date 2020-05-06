#!/usr/bin/env bash
MODEL_JAR="resource-manager-scene-1.3.1.jar"
function statistic_jar_file(){
c=0
for file in `find $PWD -name "*.jar"`
do
file_list[$c]=${file}
((c++))
done
size=${#file_list[@]}
if [ $size -gt "1" ];then
  echo "应用启动目录下存在多于一个的应用jar包,读入应用包失败,文件名如下"
    b=0
    for value in ${file_list[@]}
    do
      echo ${value}
    done
  return 1
elif [ $size -eq "1" ];then
  echo "当前应用启动目录下有且仅有一个jar包，开始读入应用包启动===>>>"
  return 0
fi
}
function chose_to_run(){
#获取应用启动版本号
version=${MODEL_JAR##*-}
version=${version%.*}
model_name=${MODEL_JAR%-*}
echo "当前启动的应用版本 ： $version"
if [ $size -gt "1" ];then
    echo "请输入应用启动的版本号 ： "
    read Args
    MODEL_JAR=$model_name-$Args.jar
fi
}

statistic_jar_file
chose_to_run
echo "$MODEL_JAR"