#!/usr/bin/python
# -*- coding: UTF-8 -*-
import mysql.connector
import requests
import os

import sys

reload(sys)
sys.setdefaultencoding('utf-8')

ROOTPATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_COMPONENTS = 'base-components.properties'
COMMON_CONFIG = 'common-config.properties'
CONFPATH = '{}/config-template/'.format(ROOTPATH)
url = 'http://nacos-center.v-base:30848/nacos/v1/cs/configs?dataId=base-components&group=prophet&tenant=a85a37ef-5bec-478c-a60f-0b11f10b3da4'
SQLPATH = '{}/sql/'.format(ROOTPATH)

class Properties(object):

    def __init__(self, content):
        self.content = content
        self.properties = {}

    def getPropertiesByStr(self):
        try:
            for line in self.content.split('\r\n'):
                line = line.strip().replace('\n', '')
                if line.find("#") != -1:
                    line = line[0:line.find('#')]
                if line.find('=') > 0:
                    strs = line.split('=')
                    strs[1] = line[len(strs[0]) + 1:]
                    self.properties[strs[0].strip()] = strs[1].strip()
        except Exception as e:
            raise e
        return self.properties

    def getPropertiesByFile(self):
        try:
            fopen = open(self.content, 'r')
            for line in fopen:
                line = line.strip()
                if line.find("#") != -1:
                    line = line[0:line.find('#')]
                if line.find('=') > 0:
                    strs = line.split('=')
                    strs[1] = line[len(strs[0]) + 1:]
                    self.properties[strs[0].strip()] = strs[1].strip()
            fopen.close()
        except Exception as e:
            raise e
        return self.properties


class InitDataBase(object):
    def __init__(self, dictProperties, commonProperties, model):
        self.dictProperties = dictProperties
        self.commonProperties = commonProperties
        self.model = model
        self.dictBase = self.getDict()

    def getDict(self):
        dictBase = {}
        dictBase['@_MYSQLIP_@'] = self.getNodeValue('mysql.ip', self.dictProperties)
        dictBase['@_MYSQLPORT_@'] = self.getNodeValue('mysql.port', self.dictProperties)
        dictBase['@_MYSQLUSERNAME_@'] = self.getNodeValue('mysql.username', self.dictProperties)
        dictBase['@_MYSQLPASSWORD_@'] = self.getNodeValue('mysql.password', self.dictProperties)
        dictBase['@_KAFKAIPPORT_@'] = self.getNodeValue('kafka.nodes', self.dictProperties)
        dictBase['@_ZKROOTPTH_@'] = self.getNodeValue('kafka.zkRootPath', self.dictProperties)
        dictBase['@_KAFKAUSERNAME_@'] = self.getNodeValue('kafka.username', self.dictProperties)
        dictBase['@_KAFKAPASSWORD_@'] = self.getNodeValue('kafka.password', self.dictProperties)
        dictBase['@_MPPDBTYPE_@'] = self.getNodeValue('mppdb.type', self.dictProperties)
        dictBase['@_MPPDBIP_@'] = self.getNodeValue('mppdb.ip', self.dictProperties)
        dictBase['@_MPPDBPORT_@'] = self.getNodeValue('mppdb.port', self.dictProperties)
        dictBase['@_MPPDBUSERNAME_@'] = self.getNodeValue('mppdb.username', self.dictProperties)
        dictBase['@_MPPDBPASSWORD_@'] = self.getNodeValue('mppdb.password', self.dictProperties)
        dictBase['@_MPPDBIPPORT_@'] = '{}:{}'.format(dictBase['@_MPPDBIP_@'], dictBase['@_MPPDBPORT_@'])
        dictBase['@_ZOOPEEPERADDRSS_@'] = self.getNodeValue('zookeeper.nodes', self.dictProperties)
        dictBase['@_ZOOPEEPERUSERNAME_@'] = self.getNodeValue('zookeeper.username', self.dictProperties)
        dictBase['@_ZOOPEEPERPASSWORD_@'] = self.getNodeValue('zookeeper.password', self.dictProperties)
        if '' != dictBase['@_ZKROOTPTH_@'] and not dictBase['@_ZKROOTPTH_@'].startswith('/'):
            dictBase['@_ZKROOTPTH_@'] = '/{}'.format(dictBase['@_ZKROOTPTH_@'])
        elif '' == dictBase['@_ZKROOTPTH_@']:
            dictBase['@_ZKROOTPTH_@'] = '/kafka'
        dictBase['@_KAFKAZOOPEEPER_@'] = '{}{}'.format(dictBase['@_ZOOPEEPERADDRSS_@'], dictBase['@_ZKROOTPTH_@'])
        dictBase['@_REDISADDRESS_@'] = self.getNodeValue('redis.nodes', self.dictProperties)
        dictBase['@_REDISSCHEME_@'] = self.getNodeValue('redis.scheme', self.dictProperties)
        dictBase['@_REDISUSERNAME_@'] = self.getNodeValue('redis.username', self.dictProperties)
        dictBase['@_REDISPASSWORD_@'] = self.getNodeValue('redis.password', self.dictProperties)
        dictBase['@_ESADDRESS_@'] = self.getNodeValue('elasticsearch.nodes', self.dictProperties)
        dictBase['@_ESERNAME_@'] = self.getNodeValue('elasticsearch.username', self.dictProperties)
        dictBase['@_ESWORD_@'] = self.getNodeValue('elasticsearch.password', self.dictProperties)
        dictBase['@_datax_report_mode_@'] = self.getNodeValue('task.report.mode', self.commonProperties)
        dictBase['@_dts_console_addresses_@'] = self.getNodeValue('dts.console.addresses', self.commonProperties)
        dts_console_addresses_list = dictBase['@_dts_console_addresses_@'].split(":")
        dictBase['@_dts_console_port_@'] = dts_console_addresses_list[len(dts_console_addresses_list) - 1].split("/")[0]
        dictBase['@_resource_manager_address_@'] = self.getNodeValue('resource.manager.address', self.commonProperties)
        dictBase['@_sys_dict_management_address_@'] = self.getNodeValue('sys.dict.management.address',
                                                                        self.commonProperties)
        dictBase['@_xxl_job_executor_ip_@'] = self.getNodeValue('xxl.job.executor.ip', self.commonProperties)
        dictBase['@_xxl_job_executor_username_@'] = self.getNodeValue('xxl.job.executor.username', self.commonProperties)
        dictBase['@_xxl_job_executor_password_@'] = self.getNodeValue('xxl.job.executor.password', self.commonProperties)
        dictBase['@_xxl_job_executor_port_@'] = self.getNodeValue('xxl.job.executor.port', self.commonProperties)
        dictBase['@_xxl_job_admin_addresses_@'] = self.getNodeValue('xxl.job.admin.addresses', self.commonProperties)
        xxl_job_admin_list = dictBase['@_xxl_job_admin_addresses_@'].split(":")
        dictBase['@_xxl_job_admin_port_@'] = xxl_job_admin_list[len(xxl_job_admin_list) - 1].split("/")[0]
        dictBase['@_deploy_dir_@'] = self.getNodeValue('deploy.soft.dir', self.commonProperties)
        dictBase['@_deploy_log_dir_@'] = self.getNodeValue('deploy.log.dir', self.commonProperties)

        return dictBase

    def getNodeValue(self, name, dict):
        if name in dict:
            return dict[name]
        else:
            return ""
            print("warning!!! nacos没有{}配置".format(name))

    def replaceFile(self, fileTemp, filep):
        global line_new
        fr = open(fileTemp, 'r')
        fw = open(filep, 'w+')
        for line in fr:
            line_new = line.encode('utf8')
              #.strip()
            for (k, v) in self.dictBase.items():
                line_new = line_new.replace(k, v)
            fw.write('{}'.format(line_new))
        fr.close()
        fw.close()

    def initByProperties(self):
        files = os.listdir(CONFPATH)
        for file in files:
            if not os.path.isdir(file) and file.endswith('.template'):
                conf_temp_path = '{}/{}'.format(CONFPATH, file)
                conf_path = '{}/{}'.format(CONFPATH, file.replace('.template', ''))
                self.replaceFile(conf_temp_path, conf_path)


    def initByInitMsql(self):
        global line_new
        mycursor = None
        mydb = None
        print("sdsd")
        print(self.dictProperties)
        try:
            mydb = mysql.connector.connect(user=self.dictProperties['mysql.username'],
                                           password=self.dictProperties['mysql.password'],
                                           host=self.dictProperties['mysql.ip'],
                                           port=self.dictProperties['mysql.port'], database='pd_dts')
            mycursor1 = mydb.cursor()
            mycursor = mydb.cursor()
            if model == 'dts-datax':
                # 初始化DICT_HOST_INFO
                sql = 'DELETE FROM `DICT_HOST_INFO` WHERE `HOST_IP`= \'{}\';' \
                    .format(self.getNodeValue('xxl.job.executor.ip', self.commonProperties))
                mycursor.execute(sql)
                sql = 'INSERT INTO `DICT_HOST_INFO`(`HOST_IP`, `PORT`, `USER_NAME`, `PASSWD`, `LOG_PATH`) ' \
                      'VALUES(\'{}\', 22, \'{}\', \'{}\', \'{}\');'.format(self.getNodeValue('xxl.job.executor.ip',
                                                                                             self.commonProperties),
                                                                           self.getNodeValue('xxl.job.executor.username', self.commonProperties),
                                                                           self.getNodeValue('xxl.job.executor.password', self.commonProperties),
                                                                           self.getNodeValue('deploy.log.dir', self.commonProperties) + '/dataworks/logs/dts/datax')
                mycursor.execute(sql)
                mydb.commit()
            elif model == 'dts-console':
                files = os.listdir(SQLPATH)
                for file in files:
                    if not os.path.isdir(file):
                        file_path_r = '{}/{}'.format(SQLPATH, file)
                        f_reader = open(file_path_r, 'rb')
                        line_new = ''
                        for line in f_reader:
                            line = line.encode('utf8').strip()
                            if line.startswith("-"):
                                continue
                            line_new = line_new + line
                            if line.endswith(";"):
                                for (k, v) in self.dictBase.items():
                                    line_new = line_new.replace(k, v)
                                print(line_new)
                                mycursor.execute(line_new)
                                mydb.commit()
                                line_new = ''
                        f_reader.close()
        except Exception as e:
           raise e
        finally:
            print("sds")
            if mycursor is not None:
                mycursor.close()
            if mydb is not None:
                mydb.close()


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            print('参数有误，请传入安装模块参数：dts-console/dts-datax/dgs-rulecheck')
            sys.exit(1)
        model = sys.argv[1]
        # 获取配置文件multidimensional.properties 数据
        commonProperties = Properties('{}/conf/{}'.format(ROOTPATH, COMMON_CONFIG)).getPropertiesByFile()
        # 是否需要从nacos获取配置
        is_sync = commonProperties['is.sync.base.config']
        if is_sync == '1':
            # 通过nacos获取配置
            try:
                rep = requests.get(url)
                if rep.status_code != 200:
                    raise Exception
                dictProperties = Properties(rep.text).getPropertiesByStr()
                initDataBase = InitDataBase(dictProperties, commonProperties, model)
            except Exception as e:
                print(e)
                print(
                    "从nacos获取失败，请手动填写基础配置:{}, 并将{} 中的is.sync.base.config改为2 ！".format(BASE_COMPONENTS, COMMON_CONFIG))
                sys.exit(1)
        else:
            # 通过手工填写基础配置获取
            baseCompProperties = Properties('{}/conf/{}'.format(ROOTPATH, BASE_COMPONENTS)).getPropertiesByFile()
            initDataBase = InitDataBase(baseCompProperties, commonProperties, model)
        # 初始化内置流程数据源信息
        initDataBase.initByInitMsql()
        print('初始化内置流程数据源信息 完成')
        # 初始化配置
        initDataBase.initByProperties()

        print('初始化配置 完成')
        sys.exit(0)
    except Exception as e:
        print(e)
        sys.exit(1)
