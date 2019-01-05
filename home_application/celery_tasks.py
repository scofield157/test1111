# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making 蓝鲸智云(BlueKing) available.
Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations under the License.

celery 任务示例

本地启动celery命令: python  manage.py  celery  worker  --settings=settings
周期性任务还需要启动celery调度命令：python  manage.py  celerybeat --settings=settings
"""
import datetime
import time

from celery import task, Celery, shared_task
from celery.schedules import crontab
from celery.task import periodic_task

import settings
from blueking.component.shortcuts import get_client_by_user
from common.log import logger
from home_application.models import OptLog

app = Celery('tasks')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@shared_task
def async_task(task_inst_id, bk_biz_id, create_user):
    """
    定义一个 celery 异步任务
    """
    # logger.error(u"celery 定时任务执行成功，执行结果：{:0>2}:{:0>2}".format(x, y))
    # return x + y
    client = get_client_by_user(create_user)
    poll_job_result(task_inst_id, bk_biz_id, client, create_user)
    print(task_inst_id)


def poll_job_result(task_inst_id, bk_biz_id, client, create_user, max_retries=30,
                    sleep_time=3):
    """
    轮询ijobs任务，返回任务执行的结果，和状态码
    """

    retries = 0
    while retries <= max_retries:
        logger.info(u'【%s】waiting for job finished（%s/%s）' % (task_inst_id, retries, max_retries))
        is_finished, is_ok = get_ijob_result(task_inst_id, bk_biz_id, client,
                                             create_user)

        # 等待执行完毕
        if not is_finished:
            retries += 1
            time.sleep(sleep_time)
            continue

        # 执行成功
        if is_ok:
            logger.info(u'【%s】job execute success' % task_inst_id)
            return True

        # 执行失败
        return False

    # 执行超时
    if retries > max_retries:
        return False


def get_ijob_result(task_instance_id, bk_biz_id, client, create_user):
    """
    查询ijobs任务实例，获取ijobs任务的业务ID、步骤详情以及当前状态
    """

    # 查询作业
    task_info = client.job.get_job_instance_status({'job_instance_id': task_instance_id,
                                                    "bk_biz_id": bk_biz_id
                                                    })
    is_ok, is_finished = False, task_info.get('data').get('is_finished')

    if is_finished:
        logger.info(u'【%s】job finished.' % task_instance_id)
        task_instance = task_info.get('data').get('job_instance', {})
        status = task_instance.get('status', 0)  # 作业状态, 2=run, 3=success, 4=fail
        is_ok = (status == 3)
        get_job_log(task_instance_id, bk_biz_id, client, create_user)

        # 获取所有任务的执行情况，用一个list来装
        # err_desc = err_log.get('logContent')

        # if is_finished and not is_ok:
        #     # err_desc = task_info['blocks'][0]['stepInstances'][0]['stepIpResult'][0]['resultTypeText']
        #     err_log = get_job_log(task_instance_id, bk_biz_id)
        #     # err_desc = err_log.get('logContent')

    return is_finished, is_ok


def get_job_log(task_instance_id, bk_biz_id, client, create_user):
    """
    查询作业日志，分析结果
    """
    data = client.job.get_job_instance_log({'job_instance_id': task_instance_id,
                                            "bk_biz_id": bk_biz_id
                                            })
    results = data.get('data')[0].get('step_results')[0]
    success_ip = []
    failure_ip = []
    for ip_content in results.get("ip_logs"):
        if ip_content['exit_code'] == 0:
            success_ip.append(ip_content['ip'])
        else:
            failure_ip.append(ip_content['ip'])
    check_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result_message = "修改密码成功的服务器:" + str(success_ip) + "修改密码失败的服务器:" + str(failure_ip)
    OptLog.objects.create(
        operator=create_user,
        opt_at=check_time,
        opt_log=result_message,
    )
