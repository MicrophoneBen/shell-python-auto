#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function
import sys
import os
import signal
import subprocess
import time
import re
import socket
import json
from optparse import OptionParser
from optparse import OptionGroup
from string import Template
import codecs
import platform

import requests
import yaml


def isWindows():
    return platform.system() == 'Windows'

DATAX_HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_dist = os.environ
DTS_LOG_ROOT_PATH = env_dist.get('DTS_LOG_ROOT_PATH', '')
print(DTS_LOG_ROOT_PATH)
DATAX_VERSION = 'DATAX-OPENSOURCE-3.0'
if isWindows():
    codecs.register(lambda name: name == 'cp65001' and codecs.lookup('utf-8') or None)
    CLASS_PATH = ("%s/lib/*") % (DATAX_HOME)
else:
    CLASS_PATH = ("%s/lib/*:%s/conf/:.") % (DATAX_HOME,DATAX_HOME)
LOG4J_FILE = ("%s/conf/log4j2.xml") % (DATAX_HOME)
DEFAULT_JVM = "-Xms2g -Xmx2g -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=%s/datax.hprof" % (DTS_LOG_ROOT_PATH)
DEFAULT_PROPERTY_CONF = "-Dfile.encoding=UTF-8 -Djava.security.egd=file:///dev/urandom -Ddatax.home=%s -Dlog4j.configurationFile=%s -Dlog.dir=%s" % (
    DATAX_HOME, LOG4J_FILE, DTS_LOG_ROOT_PATH)
ENGINE_COMMAND = "java -server ${jvm} %s -classpath %s  ${params} com.alibaba.datax.core.Engine -mode ${mode} -jobid ${jobid} -job ${job}" % (
    DEFAULT_PROPERTY_CONF, CLASS_PATH)
print("ENGINE_COMMAND="+ENGINE_COMMAND)
REMOTE_DEBUG_CONFIG = "-Xdebug -Xrunjdwp:transport=dt_socket,server=y,address=9996"

RET_STATE = {
    "KILL": 143,
    "FAIL": -1,
    "OK": 0,
    "RUN": 1,
    "RETRY": 2
}

CONF_PATH = DATAX_HOME + '/conf'
taskId = ''
taskInstanceId = ''
is_open_data_check = 'false'
flowId = ''
stepId = ''
LOG_FIELD_SEPARATOR = '\"|++|\"'

def getLocalIp():
    try:
        return socket.gethostbyname(socket.getfqdn(socket.gethostname()))
    except:
        return "Unknown"


def suicide(signum, e):
    global child_process
    print("[Error] DataX receive unexpected signal {}, starts to suicide.".format(signum),file=sys.stderr)

    if child_process:
        child_process.send_signal(signal.SIGQUIT)
        time.sleep(1)
        child_process.kill()
    print("DataX Process was killed ! you did ?",file=sys.stderr)
    sys.exit(RET_STATE["KILL"])


def register_signal():
    if not isWindows():
        global child_process
        signal.signal(2, suicide)
        signal.signal(3, suicide)
        signal.signal(15, suicide)


def getOptionParser():
    usage = "usage: %prog [options] job-url-or-path"
    parser = OptionParser(usage=usage)

    prodEnvOptionGroup = OptionGroup(parser, "Product Env Options",
                                     "Normal user use these options to set jvm parameters, job runtime mode etc. "
                                     "Make sure these options can be used in Product Env.")
    prodEnvOptionGroup.add_option("-j", "--jvm", metavar="<jvm parameters>", dest="jvmParameters", action="store",
                                  default=DEFAULT_JVM, help="Set jvm parameters if necessary.")
    prodEnvOptionGroup.add_option("--jobid", metavar="<job unique id>", dest="jobid", action="store", default="-1",
                                  help="Set job unique id when running by Distribute/Local Mode.")
    prodEnvOptionGroup.add_option("-m", "--mode", metavar="<job runtime mode>",
                                  action="store", default="standalone",
                                  help="Set job runtime mode such as: standalone, local, distribute. "
                                       "Default mode is standalone.")
    prodEnvOptionGroup.add_option("-p", "--params", metavar="<parameter used in job config>",
                                  action="store", dest="params",
                                  help='Set job parameter, eg: the source tableName you want to set it by command, '
                                       'then you can use like this: -p"-DtableName=your-table-name", '
                                       'if you have mutiple parameters: -p"-DtableName=your-table-name -DcolumnName=your-column-name".'
                                       'Note: you should config in you job tableName with ${tableName}.')
    prodEnvOptionGroup.add_option("-r", "--reader", metavar="<parameter used in view job config[reader] template>",
                                  action="store", dest="reader",type="string",
                                  help='View job config[reader] template, eg: mysqlreader,streamreader')
    prodEnvOptionGroup.add_option("-w", "--writer", metavar="<parameter used in view job config[writer] template>",
                                  action="store", dest="writer",type="string",
                                  help='View job config[writer] template, eg: mysqlwriter,streamwriter')
    parser.add_option_group(prodEnvOptionGroup)

    devEnvOptionGroup = OptionGroup(parser, "Develop/Debug Options",
                                    "Developer use these options to trace more details of DataX.")
    devEnvOptionGroup.add_option("-d", "--debug", dest="remoteDebug", action="store_true",
                                 help="Set to remote debug mode.")
    devEnvOptionGroup.add_option("--loglevel", metavar="<log level>", dest="loglevel", action="store",
                                 default="info", help="Set log level such as: debug, info, all etc.")
    parser.add_option_group(devEnvOptionGroup)
    return parser

def generateJobConfigTemplate(reader, writer):
    readerRef = "Please refer to the %s document:\n     https://github.com/alibaba/DataX/blob/master/%s/doc/%s.md \n" % (reader,reader,reader)
    writerRef = "Please refer to the %s document:\n     https://github.com/alibaba/DataX/blob/master/%s/doc/%s.md \n " % (writer,writer,writer)
    print(readerRef)
    print(writerRef)
    jobGuid = 'Please save the following configuration as a json file and  use\n     python {DATAX_HOME}/bin/datax.py {JSON_FILE_NAME}.json \nto run the job.\n'
    print(jobGuid)
    jobTemplate={
      "job": {
        "setting": {
          "speed": {
            "channel": ""
          }
        },
        "content": [
          {
            "reader": {},
            "writer": {}
          }
        ]
      }
    }
    readerTemplatePath = "%s/plugin/reader/%s/plugin_job_template.json" % (DATAX_HOME,reader)
    writerTemplatePath = "%s/plugin/writer/%s/plugin_job_template.json" % (DATAX_HOME,writer)
    try:
      readerPar = readPluginTemplate(readerTemplatePath);
    except Exception as e:
       print("Read reader[%s] template error: can\'t find file %s" % (reader,readerTemplatePath))
    try:
      writerPar = readPluginTemplate(writerTemplatePath);
    except Exception as e:
      print("Read writer[%s] template error: : can\'t find file %s" % (writer,writerTemplatePath))
    jobTemplate['job']['content'][0]['reader'] = readerPar;
    jobTemplate['job']['content'][0]['writer'] = writerPar;
    print(json.dumps(jobTemplate, indent=4, sort_keys=True))

def readPluginTemplate(plugin):
    with open(plugin, 'r') as f:
            return json.load(f)

def isUrl(path):
    if not path:
        return False

    assert (isinstance(path, str))
    m = re.match(r"^http[s]?://\S+\w*", path.lower())
    if m:
        return True
    else:
        return False


def buildStartCommand(options, args):
    commandMap = {}
    tempJVMCommand = DEFAULT_JVM
    if options.jvmParameters:
        tempJVMCommand = tempJVMCommand + " " + options.jvmParameters

    if options.remoteDebug:
        tempJVMCommand = tempJVMCommand + " " + REMOTE_DEBUG_CONFIG
        print('local ip: ', getLocalIp())

    if options.loglevel:
        tempJVMCommand = tempJVMCommand + " " + ("-Dloglevel=%s" % (options.loglevel))

    if options.mode:
        commandMap["mode"] = options.mode

    # jobResource 可能是 URL，也可能是本地文件路径（相对,绝对）
    jobResource = args[0]
    print('===========jobResource===========: ',jobResource)
    if not isUrl(jobResource):
        jobResource = os.path.abspath(jobResource)
        if jobResource.lower().startswith("file://"):
            jobResource = jobResource[len("file://"):]
        try:
            fp = open(jobResource)
            CONTENT = fp.read()
            json_dic = json.loads(CONTENT)
            if 'setting' in json_dic['job'] and 'taskInfo' in json_dic['job']['setting']:
                taskInfos = json_dic['job']['setting']['taskInfo']
                global taskId
                global is_open_data_check
                global flowId
                global stepId
                global taskInstanceId
                if 'taskId' in taskInfos:
                    taskId = str(taskInfos['taskId'])
                if 'is_open_data_check' in taskInfos:
                    is_open_data_check = str(taskInfos['is_open_data_check'])
                if 'flowId' in taskInfos:
                    flowId = str(taskInfos['flowId'])
                if 'stepId' in taskInfos:
                    stepId = str(taskInfos['stepId'])
                if 'taskInstanceId' in taskInfos:
                    taskInstanceId = str(taskInfos['taskInstanceId'])
            else:
                print('json 配置中没有task信息')
                sys.exit(1)
            fp.close()
        except IOError:
            print("json文件读取失败")
    cur_time = time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
    reader_name = str(json_dic['job']['content'][0]['reader']['name'])
    witer_name = str(json_dic['job']['content'][0]['writer']['name'])
    logName = reader_name + '_' + witer_name + '_' + flowId + '_' + stepId + '_' + taskInstanceId + '_' + cur_time
    alarmLogName = flowId + "_" + stepId
    detailLogName = flowId + "_" + stepId
    dirtyLogName = flowId + "_" + stepId + "_" + taskInstanceId
    jobParams = ("-Dlog.field.separator=%s -Dlog.file.name=%s -Dalarm.log.file.name=%s -Ddetail.log.file.name=%s -Ddirty.log.file.name=%s -DIS_OPEN_DATA_CHECK=%s -DflowId=%s -DstepId=%s") % (LOG_FIELD_SEPARATOR, logName, alarmLogName, detailLogName, dirtyLogName, is_open_data_check, flowId, stepId)
    if options.params:
        jobParams = jobParams + " " + options.params

    if options.jobid:
        commandMap["jobid"] = options.jobid

    commandMap["jvm"] = tempJVMCommand
    commandMap["params"] = jobParams
    commandMap["job"] = jobResource

    return Template(ENGINE_COMMAND).substitute(**commandMap)


def printCopyright():
    print('''
DataX (%s), From Alibaba !
Copyright (C) 2010-2017, Alibaba Group. All Rights Reserved.

''' % DATAX_VERSION)
    sys.stdout.flush()


def readConf(confPath):
    config_file = confPath + '/config.yaml'
    print(config_file)
    yaml.warnings({'YAMLLoadWarning': False})
    return yaml.load(open(config_file, 'r'))


if __name__ == "__main__":
    printCopyright()
    parser = getOptionParser()
    options, args = parser.parse_args(sys.argv[1:])
    if options.reader is not None and options.writer is not None:
        generateJobConfigTemplate(options.reader,options.writer)
        sys.exit(RET_STATE['OK'])
    if len(args) != 1:
        parser.print_help()
        sys.exit(RET_STATE['FAIL'])

    startCommand = buildStartCommand(options, args)

    print("######################" + startCommand)

    child_process = subprocess.Popen(startCommand, shell=True)
    register_signal()
    (stdout, stderr) = child_process.communicate()

