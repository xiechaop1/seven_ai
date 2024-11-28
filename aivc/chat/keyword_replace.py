class KeywordReplacer:
    def __init__(self):
        self.replace_dict = {
            "DeepSeek开发的人工智能模型": "七宝",
            "DeepSeek": "第七生命"
        }
    
    def replace(self, text):
        result = text
        for key, value in self.replace_dict.items():
            result = result.replace(key, value)
        return result