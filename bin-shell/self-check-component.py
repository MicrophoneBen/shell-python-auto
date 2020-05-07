#!/usr/bin/env python
# coding=utf-8
__author__ = 'ZhangBingQuan'
__date__ = '2020/5/07'
# config_configparser.py 配置文件
# configparser 可以读写和解析注释文件, 但是没有写入注释的功能

import pymysql
import configparser
import re


def config_read():
    """
    解析配置文件
    """
    # 配置字典
    config_dict = {}

    # 读取
    config = configparser.ConfigParser()

    config.read(filenames='properties.ini', encoding="UTF-8")
    # config.read('C:\\Users\\Administrator\\PycharmProjects\\public-center-service\\bin-shell\\properties.ini', "UTF-8")

    lists_header = config.sections()  # 配置组名、
    print(lists_header)

    # 读取Redis
    redis = config['Redis']
    redis_node = redis["redis.node"]
    redis_mode = redis['redis.mode']
    config_dict['redis_node'] = redis_node
    config_dict['redis_mode'] = redis_mode

    # 读取Mysql
    boolean = 'MySql' in config  # 配置组是否存在
    mysql = "mysql"
    if boolean:
        mysql = config['MySql']
    boolean = config.has_section("MySql")
    for key in config['MySql']:
        config_dict[key] = mysql[key]

    # 读取Kafka
    kafka = config['Kafka']
    kafka_node = kafka["kafka.nodes"]
    config_dict['kafka_node'] = kafka_node
    # 读取ZK
    zk = config['Zookeeper']
    zk_node = zk['zookeeper.nodes']
    config_dict['zk_node'] = zk_node
    # 读取ES 2.1.2
    es2 = config['ElasticSearch2']
    es2_node_tcp = es2['elasticsearch2.nodes.tcp']
    es2_node_http = es2['elasticsearch2.nodes.http']
    config_dict['es2_node_tcp'] = es2_node_tcp
    config_dict['es2_node_http'] = es2_node_http
    # 读取ES 7.2.1
    es7 = config['ElasticSearch7']
    es7_node_tcp = es7['elasticsearch7.nodes.tcp']
    es7_node_http = es7['elasticsearch7.nodes.http']
    config_dict['es7_node_tcp'] = es7_node_tcp
    config_dict['es7_node_http'] = es7_node_http
    return config_dict


def mysql_connector_test(mysql_config):
    print(mysql_config)

    # 注意把password设为你的root口令:
    conn = pymysql.connect(host=mysql_config['ip'], port=int(mysql_config['port']),
                           user=mysql_config['user'], passwd=mysql_config['password'], db=mysql_config['database'])
    # 运行查询:
    cursor = conn.cursor()
    cursor.execute('select * from SYS_USER where USER_CODE = %s', ['admin'])
    values = cursor.fetchall()
    print(values)
    # 关闭Cursor和Connection:
    cursor.close()

    # 得到一个可以执行SQL语句的光标对象
    cursor = conn.cursor()
    sql = "INSERT INTO SYS_USER (`USER_CODE`,`USER_NAME`,`PASSWORD`) VALUES (%s, %s, %s);"
    usercode = "Alex"
    username = "Alex"
    password = "7C6579CB1F4DB2EE2668AA761309D39E"
    try:
        # 执行SQL语句
        cursor.execute(sql, [usercode, username, password])
        # 提交事务
        conn.commit()
    except Exception as exception:
        # 有异常，回滚
        conn.rollback()
    cursor.close()
    # 得到一个可以执行SQL语句的光标对象
    cursor = conn.cursor()
    sql = "DELETE FROM SYS_USER WHERE USER_CODE=%s;"
    try:
        cursor.execute(sql, ["Alex"])
        # 提交事务
        conn.commit()
    except Exception as e:
        # 有异常，回滚事务
        conn.rollback()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    config_dict = config_read()

    mysql_connector_test(config_dict)

    # config_func()
