# -*- coding: utf-8 -*-
import json

import requests
from django.utils.translation import ugettext as _
from django.utils import  translation
from django.core.cache import cache

from common.log import logger
from conf.default import APP_ID, APP_TOKEN, BK_PAAS_HOST


def get_data_by_api(url, request_data, method='GET', headers=True):
    """
    @summary:组装接口
    """
    language_header = {
        'blueking-language': translation.get_language()
    }
    HEADERS = {
        'Content-type': 'application/json'
    }
    request_info = "url: {url}: request_data: {request_data}".format(
        url=url, request_data=str(request_data)
    )
    logger.info(request_info)
    try:
        if method == 'POST':
            request_data = json.loads(request_data)
            request_data.update({'app_code': APP_ID, 'app_secret': APP_TOKEN})
            request_data = json.dumps(request_data)
            if headers:
                HEADERS.update(language_header)
                data = requests.post(url, request_data, headers=HEADERS, timeout=300)
            else:
                data = requests.post(url, request_data, headers=language_header)
            logger.info("url: {url}, request_data: {request_data}, response: {response}".format(
                url=url, request_data=str(request_data), response=json.loads(data.text)
            ))
            cache.set(request_info, data, 30)
            return data
        else:
            # GET 请求缓存数据
            request_cache = cache.get(request_info)
            if request_cache:
                return request_cache

            url = BK_PAAS_HOST + url
            request_data.update({'app_code': APP_ID, 'app_secret': APP_TOKEN})
            result = requests.get(url, request_data, headers=language_header, timeout=300)
            data = json.loads(result.text)['data']
            logger.info("url: {url}, request_data: {request_data}, response: {response}".format(
                url=url, request_data=str(request_data), response=json.loads(result.text)
            ))
            if data is None:
                data = []
            cache.set(request_info, data, 30)
            return data
    except Exception as e:
        logger.error(
            _(u'获取API{url}信息失败：{request_data}, 异常：{exception} ').format(
                url=url, request_data=request_data, exception=e)
        )
        return []


def get_app_by_user(bk_token):
    """
    @summary:查询用户有权限的业务
    """
    cache_name = "%s_apps" % bk_token
    data = cache.get(cache_name)
    if not data:
        data = get_data_by_api('/api/c/compapi/cc/get_app_by_user/',
                               {'bk_token': bk_token})

        cache.set(cache_name, data, 60)
    app_list = []
    for app in data:
        try:
            app_list.append({
                "app_name": app['ApplicationName'],
                "app_id": app['ApplicationID'],
                "time_zone": app['TimeZone']
            })
        except KeyError:
            app_list.append({
                "app_name": app['ApplicationName'],
                "app_id": app['ApplicationID'],
                "time_zone": 'Asia/Shanghai'
            })
    return app_list




