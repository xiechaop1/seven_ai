
# API接口

| 项目 | 说明  |
|:------------- |:---------------| 
| 协议      | websocket |   
| 地址      | ws://114.55.90.104:9001/ws |   

# 语音聊天

### 请求数据格式

| 参数 | 说明  | 数据格式|缺省值|是否必填|
|:------------- |:---------------| :---------------|  :---------------| :---------------| 
| version      | 版本号 |   字符串| 1.0|是 | 
| method      | 请求方法 |  字符串 | voice-chat| 是 | 
| conversation_id      | 会话id，websocket建联时赋值，websocket重连时更换 |  字符串 | get_conversation_id()函数生成| 是 | 
| message_id      | 消息id，发送一次消息更新一次 |  字符串 | get_message_id()函数生成| 是 | 
| token      | 认证字段，待定 |  字符串 | 待定| 是 | 
| timestamp      | 时间戳 |  字符串 | get_rfc3339_with_timezone()函数生成| 是 | 
| data      | 数据 |  VCReqData数据结构 | 见VCReqData定义| 是 | 

####  VCReqData结构
| 参数 | 说明  | 数据格式|缺省值|是否必填|
|:------------- |:---------------| :---------------|  :---------------| :---------------| 
| content_type      | 数据格式 |   字符串|audio\|image\|text |是 | 
| content      | 数据 |   字符串|audio或image采用base64编码,text明码 |是 | 
| tts_audio_format      | 数据 |   字符串|pcm / ogg_opus / mp3，默认为 pcm |否 | 

#### 请求示例
```
{
  "version": "1.0",
  "method": "voice-chat",
  "conversation_id": "04025a30-2ec4-44cb-918b-d7e7298563f5",
  "message_id": "20241031-013946-4611e877-c5de-4773-91bd-b57e459a0e4b",
  "token": "20241031-013946-f674310c-0c7f-440e-901a-075c6c28b552",
  "timestamp": "2024-10-31T09:49:09.761387+08:00",
  "data": {
    "content_type": "audio",
    "content": "JQIkA4MBxv+p/xT/Sv3U/Ir/yQLtBOgDqv9O/Hz7oP0QAZAC9gKeAngAXf5o/Fr9NgGlA/kCOADx/Tb+P/96/7b/OgFdAzUCwv1Z+iv7jADABaYFfwFH/E36T/wj/2EBRQM0BMwCm/4C+xv7JP4OAWwDPQRXAg==",
    "tts_audio_format":"ogg_opus"
  }
}
```

### 响应数据格式

**注：单次请求一般是有多个返回，收到后按序播放即可**

| 参数 | 说明  | 数据格式|缺省值|是否必填|
|:------------- |:---------------| :---------------|  :---------------| :---------------| 
| version      | 版本号 |   字符串| 1.0|是 | 
| method      | 请求方法 |  字符串 | voice-chat| 是 | 
| conversation_id      | 会话id |  字符串 | 回传请求字段| 是 | 
| message_id      | 消息id |  字符串 | 回传请求字段| 是 | 
| code      | 返回码，0表示成功，其他表示失败 |  字符串 | 0| 是 | 
| message      | 返回成功或者错误消息 |  字符串 | success| 是 | 
| data      | 数据 |  VCRespData数据结构 | 见VCRespData定义| 是 | 

#### VCRespData结构
| 参数 | 说明  | 数据格式|值|是否必填|
|:------------- |:---------------| :---------------|  :---------------| :---------------| 
| action      | 行动指令 |   字符串| take_photo|否 | 
| text      | 文字内容 |   字符串| |否 | 
| audio_data      | 音频数据 |   字符串|base64编码 |否 | 
| audio_format      | 数据格式 |   字符串|pcm或mp3 |否 | 
| sample_rate      | 采样率 |   int|16000 |否 | 
| channels      | 声道 |   int|1 |否 | 
| sample_format      | 格式 |   字符串|S16LE |否 | 
| bitrate      | 码率 |   int|256000 |否 | 
| stream_seq      | 流顺序号，-1表示流已经结束 |   int|0 |是 | 

#### 响应示例
```
{
  "version": "1.0",
  "method": "voice-chat",
  "conversation_id": "04025a30-2ec4-44cb-918b-d7e7298563f5",
  "message_id": "20241031-013946-4611e877-c5de-4773-91bd-b57e459a0e4b",
  "code": 0,
  "message": "success",
  "data": {
    "action": "take_photo",
    "text": "好的，我看一下",
    "sample_rate": 16000,
    "channels": 1,
    "sample_format": "S16LE",
    "bitrate": 256000,
    "audio_data": "AAAAAAAP//AAD8////9//1/ywAMQAPAAwA+v/9/xUACAABAPf/8f/z//b/",
    "audio_format": "pcm",
    "stream_seq":1
  }
}
```

#### 数据格式定义
```
class VCMethod(str, Enum):
    VOICE_CHAT = "voice-chat"
    TEXT_CHAT = "text-chat"
    PING = "ping"

class ContentType(str, Enum):
    AUDIO = "audio"
    IMAGE = "image"
    TEXT = "text"

class VCReqData(BaseModel):
    content_type: Optional[str] = ContentType.AUDIO.value  # audio|image|text
    content: Optional[str] = "" # audio|image base64 encoded data
    tts_audio_format: Optional[str] = "pcm" # pcm|ogg_opus|mp3

DataT = TypeVar("DataT")

class Req(BaseModel, Generic[DataT]):
    version: str = "1.0"
    method: VCMethod 
    conversation_id: str
    message_id: str
    token: Optional[str] = ""
    timestamp: Optional[str] = ""
    data: Optional[DataT] = None

class VCRespData(BaseModel):
    action: Optional[str] = None
    text: Optional[str] = ""
    audio_format: Optional[str] = "pcm"
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    sample_format: Optional[str] = None
    bitrate: Optional[int] = None
    audio_data: Optional[str] = None
    stream_seq: int = 0

class Resp(BaseModel, Generic[DataT]):
    version: Optional[str] = ""
    method: Optional[VCMethod] = ""
    conversation_id: Optional[str] = ""
    message_id: Optional[str] = ""
    code: int = 0
    message: str = "success"
    data: Optional[DataT] = None

```

#### id生成
```
import uuid
from datetime import datetime

def get_id() -> str:
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')[:-3]
    return f"{timestamp}-{uuid.uuid4().hex}"

def get_conversation_id() -> str:
    return uuid.uuid4().hex

def get_message_id() -> str:
    return get_id()
```

#### 时间戳生成
```
from datetime import datetime
import pytz
def get_rfc3339_with_timezone():
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(tz).isoformat()
```


# 心跳

### 请求数据格式

| 参数 | 说明  | 数据格式|缺省值|是否必填|
|:------------- |:---------------| :---------------|  :---------------| :---------------| 
| version      | 版本号 |   字符串| 1.0|是 | 
| method      | 请求方法 |  字符串 | ping| 是 | 

#### 请求示例
```
{
  "version": "1.0",
  "method": "ping"
}
```

### 响应数据格式
| 参数 | 说明  | 数据格式|缺省值|是否必填|
|:------------- |:---------------| :---------------|  :---------------| :---------------| 
| version      | 版本号 |   字符串| 1.0|是 | 
| method      | 请求方法 |  字符串 | pong| 是 | 

#### 响应示例
```
{
  "version": "1.0",
  "method": "pong"
}
```
