import os, uuid, xmltodict, aiohttp

from homeassistant.helpers.network import get_url
from homeassistant.components.http import HomeAssistantView

import logging
_LOGGER = logging.getLogger(__name__)

DOMAIN = 'ha_kodi'
VERSION = '1.0'
ROOT_PATH = '/' + DOMAIN +'-local/' + VERSION

async def async_setup(hass, config):
    # 显示插件信息
    _LOGGER.info('''
-------------------------------------------------------------------
    Kodi视频辅助插件【作者QQ：635147515】
    
    版本：''' + VERSION + '''
        
    项目地址：https://github.com/shaonianzhentan/ha_kodi
-------------------------------------------------------------------''')
    # 注册静态目录
    local = hass.config.path('custom_components/'+DOMAIN+'/local')
    if os.path.isdir(local):
        hass.http.register_static_path(ROOT_PATH, local, False)
    # 读取配置
    async def play_video(call):
        data = call.data
        _name = data['name']
        entity_id = data['entity_id']        
        await search(hass, entity_id, _name)
        print(_name)
    # 注册服务
    hass.services.async_register(DOMAIN, 'play', play_video)
    return True

async def search(hass, entity_id, keywords): 
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.shijiapi.com/api.php/provide/vod/at/xml/?wd=' + keywords) as res:
            xml_result = await res.text()
            json_result = xmltodict.parse(xml_result, encoding='utf-8')
            #print(json_result)
            video = json_result['rss']['list']['video']
            if video:
                if isinstance(video, list):
                    video = video[0]
                id = str(video['id'])
                async with session.get('https://api.shijiapi.com/api.php/provide/vod/at/xml/?ac=videolist&ids=' + id) as res:
                    xml_result = await res.text()
                    json_result = xmltodict.parse(xml_result, encoding='utf-8')
                    #print(json_result)
                    dd = json_result['rss']['list']['video']['dl']['dd']
                    obj = dd[1]
                    arr = obj['#text'].split('#')

                    # 生成文件
                    file_content = '#EXTM3U'
                    for item in arr:
                        _arr = item.split('$')
                        if len(_arr) == 2:
                            print(_arr[0])
                            print(_arr[1])
                            file_content += '\n#EXTINF:-1, ' + video['name'] + '-' + _arr[0] + '\n' + _arr[1]
                    # 写入文件
                    file_path = hass.config.path("custom_components/" + DOMAIN + "/local/") + id + '.m3u'
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(file_content)
                    print("下载成功，开始播放")
                    video_url = get_url(hass) + ROOT_PATH + '/' + id + '.m3u'
                    print(video_url)
                    await hass.services.async_call('media_player', 'play_media', {
                        'entity_id': entity_id,
                        'media_content_type': 'playlist',
                        'media_content_id': video_url
                    })