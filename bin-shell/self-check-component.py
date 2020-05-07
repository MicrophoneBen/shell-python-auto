#!/usr/bin/env python
# coding=utf-8
__author__ = 'ZhangBingQuan'
__date__ = '2020/5/07'
# config_configparser.py 配置文件
# configparser 可以读写和解析注释文件, 但是没有写入注释的功能

import pymysql
import configparser
import redis
import rediscluster
# 导入安装包
from pykafka import KafkaClient


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


def mysql_connector_test(ip, port, user, password, database):
    print("当前的MySql连接信息是 ： ", ip, port, user, password, database)

    # 注意把password设为你的root口令:
    conn = pymysql.connect(host=ip, port=int(port), user=user, password=password, database=database)
    return conn


def handler_sysmanager_db(ip, port, user, password, database):
    conn = mysql_connector_test(ip, port, user, password, database)
    # 运行查询:
    cursor = conn.cursor()
    cursor.execute('select * from SYS_USER where USER_CODE = %s', ['admin'])
    values = cursor.fetchall()
    print("查询数据库获取admin用户的信息", values)
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


# Redis单机测试连接
def redis_connect_test(host, port, password):
    conn = redis.StrictRedis(connection_pool=redis.ConnectionPool(host=host, port=port, password=password))
    # String类型的写入和读取
    conn.set("test_conn", "python_test_redis_conn")
    value = conn.get("test_conn")
    print("原来写入的Value是 ： {python_test_redis_conn}， 读取到的Value是 ： %s", value)
    # 列表类型的写入与读取
    conn.lpush("list_conn", "python, go, C++, Java")
    rel = conn.lrange("list_conn", 0, -1)
    print("原来写入的Value是 ： {python, go, C++, Java}， 读取到的Value是 ： %s", rel)

    conn.delete("test_conn")
    conn.delete("list_conn")


def get_cluster_conn(cluster_nodes):
    cluster_list = []
    redis_list = cluster_nodes.split(",")
    for item in redis_list:
        redis_node = {}
        rel = item.split(":")
        redis_node['host'] = rel[0]
        redis_node['port'] = rel[1]
        cluster_list.append(redis_node)
    print("当前连接测试的Redis集群信息是 : ", cluster_list)
    conn = rediscluster.RedisCluster(
        startup_nodes=cluster_list,
        decode_responses=True,
        max_connections=300
    )
    return conn


def handler_redis_cluster(cluster_nodes):
    conn = get_cluster_conn(cluster_nodes)
    # String类型的写入和读取
    conn.set("test_conn", "python_test_redis_conn")
    value = conn.get("test_conn")
    print("原来写入的Value是 ： {python_test_redis_conn}， 读取到的Value是 ： ", value)
    # 列表类型的写入与读取
    conn.lpush("list_conn", "python, go, C++, Java")
    rel = conn.lrange("list_conn", 0, -1)
    print("原来写入的Value是 ： {python, go, C++, Java}， 读取到的Value是 ： ", rel)

    conn.delete("test_conn")
    conn.delete("list_conn")


def handler_kafka_cluster(kafka_nodes):
    # 设置客户端的连接信息
    client = KafkaClient(hosts=kafka_nodes)
    # 打印所有的topic
    print("当前Kafka的所有topic列表如下 ： ", client.topics)


if __name__ == "__main__":
    config_dict = config_read()
    print("读取到的配置文件如下 ： ", config_dict)

    handler_sysmanager_db(config_dict['ip'], config_dict['port'], config_dict['user'],
                          config_dict['password'], config_dict['database'])

    handler_redis_cluster(config_dict['redis_node'])

    handler_kafka_cluster(config_dict['kafka_node'])

    # config_func()
