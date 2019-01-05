# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making 蓝鲸智云(BlueKing) available.
Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations under the License.
"""
import base64
import json

from blueking.component.shortcuts import get_client_by_request
from common.mymako import render_mako_context, render_json
from home_application.celery_tasks import async_task
from home_application.biz_utils import get_app_by_user
from home_application.models import OptLog


def home(request):
    """
    首页
    """

    client = get_client_by_request(request)
    client.set_bk_api_ver('v2')
    app_list = get_app_by_user(request.COOKIES['bk_token'])
    for x in app_list:
        if x.get("app_name") == u'\u8d44\u6e90\u6c60' or x.get("app_name") == 'Resource pool':
            app_list.remove(x)
            break
    return render_mako_context(request, '/home_application/home.html', {'bizList': app_list})


def get_host_by_biz(request):
    """
    根据业务获取机器
    :param request:
    :return:
    """
    biz_id = request.GET['bizID']
    os_type = request.GET['osType']
    param = {
        'bk_biz_id': biz_id,
        "condition": [
            {
                "bk_obj_id": "host",
                "condition": [{
                    'field': 'bk_os_type',
                    "operator": "$eq",
                    "value": str(os_type)
                }]
            }
        ]
    }
    client = get_client_by_request(request)
    result = client.cc.search_host(param)
    display_list = []
    if result.get('result'):
        for host_info in result.get('data').get('info'):
            temp_dict = {
                'hostName': host_info['host']['bk_host_name'],
                'ip': host_info['host']['bk_host_innerip'],
                'cloudID': host_info['host']['bk_cloud_id'][0]['bk_inst_id'],
                'bk_host_id': host_info['host']['bk_host_id']
            }
            if os_type == '1':
                temp_dict['osType'] = "linux"
            else:
                temp_dict['osType'] = "windows"
            display_list.append(temp_dict)
        return render_mako_context(request, '/home_application/table.html', {'hostList': display_list})


def change_host_password(request):
    req = json.loads(request.body)
    ip_list = req.get('hosts')
    password = req.get('password')
    os_type = req.get('osType')
    biz_id = req.get('bizID')
    create_user = request.user.username
    if not password:
        return render_json(
            {
                "result": False,
                "message": u"没有填写密码",
            })
    if not os_type:
        return render_json(
            {
                "result": False,
                "message": u"没有选择系统",
            })
    if type(ip_list) is not list or len(ip_list) == 0:
        return render_json(
            {
                "result": False,
                "message": u"没有选择机器",
            })
    if os_type == '1':
        content = "echo $1|passwd --stdin root> /dev/null 2>&1"
        script_type = 1
        account = 'root'
    else:
        content = "net user administrator $1"
        script_type = 2
        account = 'administrator'
    kwargs = {
        "bk_biz_id": biz_id,
        "script_content": base64.b64encode(content),
        "script_type": script_type,
        "script_param": base64.b64encode(password),
        "ip_list": ip_list,
        "account": account
    }
    client = get_client_by_request(request)
    result = client.job.fast_execute_script(kwargs)
    if result:
        task_inst_id = result.get('data').get('job_instance_id')
        async_task.apply_async(args=(task_inst_id, biz_id, create_user), kwargs={})
        return render_json(
            {
                "result": True,
                "message": u"任务开始执行",
            })


def get_all_log(request):
    opt_list = OptLog.objects.order_by('-opt_at')
    return render_mako_context(request, '/home_application/history.html', {'logList': opt_list})
