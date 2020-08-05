import os, uuid, xmltodict, aiohttp

from homeassistant.helpers.network import get_url
from homeassistant.components.http import HomeAssistantView

import logging
_LOGGER = logging.getLogger(__name__)

from .api_video import Video
from .api_bilibili import Bilibili

ENTITY_ID = 'sensor.ha_kodi'
DOMAIN = 'ha_kodi'
VERSION = '1.1'
DOMAIN_API = '/' + DOMAIN + '-api'
ROOT_PATH = '/' + DOMAIN +'-local/' + VERSION
ATTRIBUTES = {
    'icon': 'mdi:kodi',
    'friendly_name': 'Kodi视频'
}

async def async_setup(hass, config):
    # 显示插件信息
    _LOGGER.info('''
-------------------------------------------------------------------
    Kodi视频辅助插件【作者QQ：635147515】
    
    版本：''' + VERSION + '''

    API接口：''' + DOMAIN_API + '''
        
    项目地址：https://github.com/shaonianzhentan/ha_kodi
-------------------------------------------------------------------''')
    # 注册静态目录
    local = hass.config.path('custom_components/'+DOMAIN+'/local')
    if os.path.isdir(local):
        hass.http.register_static_path(ROOT_PATH, local, False)
    
    video = Video(hass, local + '/data/', get_url(hass) + ROOT_PATH + '/')
    b = Bilibili(hass)
    hass.data[DOMAIN] = {
        'video': video,
        'b': b
    }
    # 注册服务
    hass.services.async_register(DOMAIN, 'play', video.play_video)
    # hass.services.async_register(DOMAIN, 'set_bilibili_cookie', b.set_cookie)

    hass.http.register_view(HassGateView)
    # 注册菜单栏
    hass.components.frontend.async_register_built_in_panel(
        "iframe",
        "Kodi视频",
        "mdi:kodi",
        DOMAIN,
        {"url": ROOT_PATH + "/index.html"},
        require_admin=True
    )
    hass.components.frontend.add_extra_js_url(hass, ROOT_PATH + '/more-info-ha_kodi.js')
    # hass.states.async_set(ENTITY_ID, 'kodi', attributes=ATTRIBUTES)
    return True

class HassGateView(HomeAssistantView):

    url = DOMAIN_API
    name = DOMAIN
    requires_auth = True
    
    async def post(self, request):
        hass = request.app["hass"]
        hass_data = hass.data[DOMAIN]
        video = hass_data['video']
        b = hass_data['b']
        res = await request.json()
        type = res.get('type', '')
        if type == 'download_list':
            url = res['url']
            data = await video.get_download_list(url)
            return self.json({'code':0, 'data': data, 'base_url': get_url(hass).replace(':8123', '') + '/kodi/'})
        elif type == 'search':
            data = await video.get_series(res['name'])
            return self.json({'code':0, 'data': data})
        elif type == 'kodi-search':
            data = await b.search(res['name'])
            if data is not None:
                hass.states.async_set(ENTITY_ID, 'kodi', attributes={**ATTRIBUTES, **data})
            return self.json({'code':0, 'data': data})
        elif type == 'kodi-video':
            id = res['id']
            data = await b.get_bangumi_video(id)
            if data is not None:
                set_state(hass, id)
            return self.json({'code':0, 'data': data})

        return self.json({'code':1, 'msg': '参数不正确'})

# 设置状态
def set_state(hass, value):
    state = hass.states.get(ENTITY_ID)
    if state is not None:
        hass.states.async_set(ENTITY_ID, value, attributes=state.attributes)