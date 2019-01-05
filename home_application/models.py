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

from django.db import models


class OptLog(models.Model):
    """操作记录信息"""
    operator = models.CharField(u'操作用户', max_length=128)
    opt_at = models.CharField(u'操作时间', max_length=100)
    opt_log = models.CharField(u'日志信息', max_length=1000)

    class Meta:
        verbose_name = '操作记录信息'
        verbose_name_plural = '操作记录信息'
