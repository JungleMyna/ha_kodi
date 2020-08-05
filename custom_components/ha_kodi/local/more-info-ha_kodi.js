
class SateCardKodi extends HTMLElement {

    /*
     * 触发事件
     * type: 事件名称
     * data: 事件参数
     */
    fire(type, data) {
        const event = new Event(type, {
            bubbles: true,
            cancelable: false,
            composed: true
        });
        event.detail = data;
        this.dispatchEvent(event);
    }

    /*
     * 调用服务
     * service: 服务名称(例：light.toggle)
     * service_data：服务数据(例：{ entity_id: "light.xiao_mi_deng_pao" } )
     */
    callService(service_name, service_data = {}) {
        let arr = service_name.split('.')
        let domain = arr[0]
        let service = arr[1]
        this._hass.callService(domain, service, service_data)
    }

    // 通知
    toast(message) {
        this.fire("hass-notification", { message })
    }

    /*
     * 接收HA核心对象
     */
    set hass(hass) {
        this._hass = hass
        if (!this.isCreated) {
            this.created(hass)
        }
    }

    get stateObj() {
        return this._stateObj
    }

    // 接收当前状态对象
    set stateObj(value) {
        this._stateObj = value
        // console.log(value)
        if (this.isCreated) this.updated()
    }

    // 创建界面
    created(hass) {
        /* ***************** 基础代码 ***************** */
        const shadow = this.attachShadow({ mode: 'open' });
        // 创建面板
        const ha_card = document.createElement('div');
        ha_card.className = 'custom-card-panel'
        ha_card.innerHTML = `
        <div class="controls">
            <div>
               
            </div>
            <div>
                <ha-icon class="prev" icon="mdi:skip-previous"></ha-icon>
            </div>
            <div>
                <img src="/ha_kodi-local/1.1/moive.png" class="action" style="height:80px;width:80px;border:1px solid silver;border-radius:50%;" />
            </div>
            <div>
                <ha-icon class="next" icon="mdi:skip-next"></ha-icon>
            </div>
            <div>
                
            </div>
        </div>
        <!-- 视频进度 -->
        <div class="progress">
        <div>00:00</div>
        <div>
            <ha-paper-slider min="0" max="100" value="50" />
        </div>                 
        <div>00:00</div>
        </div>
        `
        shadow.appendChild(ha_card)
        // 创建样式
        const style = document.createElement('style')
        style.textContent = `
            .controls,
            .progress{ display:flex; text-align: center; align-items: center;}
            .controls>div,
            .progress>div{width:100%;}
            .controls ha-icon{--mdc-icon-size: 30px;cursor:pointer;}
            .action{cursor:pointer;}

            @keyframes rotate{
                from{ transform: rotate(0deg) }
                to{ transform: rotate(359deg) }
            }
            .rotate{
                animation: rotate 5s linear infinite;
            }
        `
        shadow.appendChild(style);
        // 保存核心DOM对象
        this.shadow = shadow
        this.$ = this.shadow.querySelector.bind(this.shadow)
        // 创建成功
        this.isCreated = true
        /* ***************** 附加代码 ***************** */
        let { $ } = this
        $('.prev').onclick = () => {
            this.toast("上一集")
            this.callService("media_player.media_previous_track", { entity_id: this._stateObj.entity_id })
        }
        $('.next').onclick = () => {
            this.toast("下一集")
            this.callService("media_player.media_next_track", { entity_id: this._stateObj.entity_id })
        }
        $('.action').onclick = () => {
            this.toast(this._stateObj.state == "playing" ? '暂停视频' : '播放视频')
            this.callService("media_player.media_play_pause", { entity_id: this._stateObj.entity_id })
        }

        $('.progress ha-paper-slider').onchange = () => {
            let attr = this.stateObj.attributes
            let seek_position = $('.progress ha-paper-slider').value / 100 * attr.media_duration
            this.callService("media_player.media_seek", {
                entity_id: this._stateObj.entity_id,
                seek_position
            })
            this.toast(`调整进度到${seek_position}秒`)
        }
    }

    // 更新界面数据
    updated() {
        let { $, _stateObj } = this
        // console.log(_stateObj)
        let action = $('.action')
        let attrs = _stateObj.attributes
        // if ('entity_picture' in attrs) {
        //     action.src = attrs.entity_picture
        // }
        // 如果是在播放中，则转圈圈
        if (_stateObj.state == "playing") {
            if (!action.classList.contains('rotate')) action.classList.add('rotate')
        } else {
            action.classList.remove('rotate')
        }
        $('.progress div:nth-child(1)').textContent = `${this.timeForamt(attrs.media_position / 60)}:${this.timeForamt(attrs.media_position % 60)}`
        $('.progress div:nth-child(3)').textContent = `${this.timeForamt(attrs.media_duration / 60)}:${this.timeForamt(attrs.media_duration % 60)}`
        if (attrs.media_position <= attrs.media_duration) {
            $('.progress ha-paper-slider').value = attrs.media_position / attrs.media_duration * 100
        }
    }

    timeForamt(num) {
        if (isNaN(num)) return '00'
        num = Math.floor(num)
        if (num < 10) return '0' + String(num)
        return String(num)
    }
}

/* *********************** 状态面板 **************************** */
class MoreInfoKodi extends HTMLElement {

    /*
     * 触发事件
     * type: 事件名称
     * data: 事件参数
     */
    fire(type, data) {
        const event = new Event(type, {
            bubbles: true,
            cancelable: false,
            composed: true
        });
        event.detail = data;
        this.dispatchEvent(event);
    }

    /*
     * 调用服务
     * service: 服务名称(例：light.toggle)
     * service_data：服务数据(例：{ entity_id: "light.xiao_mi_deng_pao" } )
     */
    callService(service_name, service_data = {}) {
        let arr = service_name.split('.')
        let domain = arr[0]
        let service = arr[1]
        this._hass.callService(domain, service, service_data)
    }

    // 通知
    toast(message) {
        this.fire("hass-notification", { message })
    }

    http(url, params) {
        return this._hass.fetchWithAuth(url, {
            method: 'POST',
            headers: { 'content-type': 'application/json; charset=utf-8' },
            body: JSON.stringify(params)
        }).then(res => res.json())
    }

    /*
     * 接收HA核心对象
     */
    set hass(hass) {
        this._hass = hass
        if (!this.isCreated) {
            this.created(hass)
        }
    }

    get stateObj() {
        return this._stateObj
    }

    // 接收当前状态对象
    set stateObj(value) {
        this._stateObj = value
        // console.log(value)
        if (this.isCreated) this.updated()
    }

    kodiCall(method, params) {
        this.callService('kodi.call_method', {
            entity_id: this._stateObj.entity_id,
            method,
            ...params
        })
    }

    clipboard(text) {
        let id = 'unique-id-clipboard-copyText'
        let copyText = document.getElementById(id)
        if (!copyText) {
            copyText = document.createElement('input')
            copyText.id = id
            copyText.style = 'position:absolute;left:-9999px'
            document.body.appendChild(copyText)
        }
        copyText.value = text
        copyText.select()
        copyText.setSelectionRange(0, copyText.value.length)
        document.execCommand('copy')

        this.toast('复制成功');
    }

    // 创建界面
    created(hass) {
        /* ***************** 基础代码 ***************** */
        const shadow = this.attachShadow({ mode: 'open' });
        // 创建面板
        const ha_card = document.createElement('div');
        ha_card.className = 'custom-card-panel'
        ha_card.innerHTML = `
            <input type="text" placeholder="请输入视频名称" class="txtInput" />
            <ul id="list"></ul>
        `
        shadow.appendChild(ha_card)
        // 创建样式
        const style = document.createElement('style')
        style.textContent = `
            .custom-card-panel{}
            .txtInput{width:100%;padding:8px 10px;box-sizing: border-box;}
            #list{margin: 10px 0; padding: 0;}
            #list li{list-style: none; padding: 10px 5px; border-bottom: 1px solid #eee; display: flex; align-items: center;}
            #list li span{width:100%;}
            #list li ha-icon{float:right}
            .active{color:var(--primary-color);}
        `
        shadow.appendChild(style);
        // 保存核心DOM对象
        this.shadow = shadow
        this.$ = this.shadow.querySelector.bind(this.shadow)
        // 创建成功
        this.isCreated = true
        /* ***************** 附加代码 ***************** */
        let { $ } = this
        let txtInput = $('.txtInput')
        txtInput.onkeyup = (event) => {
            if (event.keyCode == 13) {
                let name = txtInput.value.trim()
                if (name) {
                    console.log(name)
                    this.callService('ha_kodi.play', {
                        entity_id: this._stateObj.entity_id,
                        name
                    })
                    this.toast('正在搜索影片，请耐心等待')
                }
                txtInput.value = ''
            }
        }
        hass.connection.subscribeEvents((res) => {
            // console.log(res)
            $('#list').innerHTML = ''
            let fragment = document.createDocumentFragment()
            res.data.result.items.forEach((ele, index) => {
                let li = document.createElement('li')
                let span = document.createElement('span')
                span.textContent = ele.label
                span.onclick = () => {
                    this.clipboard(ele.file)                    
                }
                if (this._stateObj.attributes.media_title == ele.label) {
                    span.classList.add('active')
                    li.appendChild(span)
                } else {
                    li.appendChild(span)
                    let ironIcon = document.createElement('ha-icon')
                    ironIcon.setAttribute('icon', 'mdi:play-circle-outline')
                    ironIcon.onclick = () => {
                        console.log(index)
                        this.kodiCall('Player.Open', {
                            item: {
                                playlistid: 1,
                                position: index
                            }
                        })
                        this.toast(`开始播放${ele.label}`)
                    }
                    li.appendChild(ironIcon)
                }
                fragment.appendChild(li)
            })
            $('#list').appendChild(fragment)
        }, 'kodi_call_method_result')

    }

    // 更新界面数据
    updated() {
        // let { $, _stateObj, _hass } = this
        // let { entity_id } = _stateObj
        // console.log(this._hass)
        // 获取当前播放列表
        this.kodiCall('Playlist.GetItems', {
            playlistid: 1,
            properties: ['file'],
            limits: {
                start: 0
            }
        })
    }
}

// 定义DOM对象元素
customElements.define('more-info-kodi', MoreInfoKodi);
customElements.define('state-card-kodi', SateCardKodi);