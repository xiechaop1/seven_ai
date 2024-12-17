class MeaninglessWords:
    def __init__(self):
        self.responses = [
            "嗯。",
            "啊。", 
            "行。",
            "七宝。",
            "停止。",
            "嗯嗯。",
            "这个。",
            "不是。",
            "就是。",
            "细胞。"
        ]
    
    def is_meaningless(self, text):
        return text in self.responses
