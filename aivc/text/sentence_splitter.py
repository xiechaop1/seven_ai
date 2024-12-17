import re

class SentenceSplitter:
    def __init__(self, min_sentence_length: int = 10):
        self.min_sentence_length = min_sentence_length
        self.sentence_end_re = re.compile(
            r'(?<![(\[])(.*?)([.?!。？！，：,:]|\.{3,}|\n)(?![")\]])'
        )
        self.valid_sentence_re = re.compile(r'[A-Za-z\u4e00-\u9fff]')
        self.buffer = ''
        self.pending = []  # 存储待处理的句子
        self.input_sentence_number = 0  # 输入句子序号
        self.output_sentence_number = 0  # 输出句子序号

    def get_target_length(self, sentence_number: int) -> int:
        """获取当前输出句子序号对应的目标长度"""
        if sentence_number == 1:
            return self.min_sentence_length
        elif sentence_number in (2, 3, 4):
            return int(self.min_sentence_length)
        else:
            return int(self.min_sentence_length * (sentence_number - 4) * 2)

    def add_chunk(self, chunk: str) -> str:
        if not chunk:
            return []

        self.buffer += chunk
        result = []

        while True:
            match = self.sentence_end_re.search(self.buffer)
            if not match:
                break

            sentence = (match.group(1) + match.group(2)).strip()
            self.buffer = self.buffer[match.end():]

            if not sentence.strip() or not self.valid_sentence_re.search(sentence):
                continue

            self.input_sentence_number += 1

            # 获取当前目标长度
            target_length = self.get_target_length(self.output_sentence_number + 1)
            # print(f"number: {self.input_sentence_number}, output sentence number: {self.output_sentence_number + 1}, target length: {target_length} sentence: {sentence} self.pending: {self.pending}")

            # 第一句直接输出
            if self.output_sentence_number == 0:
                result.append(sentence)
                self.output_sentence_number += 1
                continue

            # 当前句子自身就超过目标长度的2倍，需要强制切分
            if len(sentence) > target_length * 2:
                # 只取第一个目标长度的片段
                first_part = sentence[:target_length]
                remaining_part = sentence[target_length:]
                result.append(first_part)
                self.output_sentence_number += 1
                
                # 剩余部分加入pending
                if remaining_part:
                    self.pending.append(remaining_part)
                continue

            # 添加到pending并检查长度
            self.pending.append(sentence)
            pending_length = sum(len(s) for s in self.pending)

            # 如果达到目标长度，输出
            if pending_length >= target_length:
                merged = ''.join(self.pending)
                result.append(merged)
                self.output_sentence_number += 1
                self.pending.clear()

        return result

    def finalize(self) -> str:
        result = []
        remaining = self.buffer.strip()

        # 确保所有pending内容都被输出
        if self.pending or (remaining and self.valid_sentence_re.search(remaining)):
            if remaining:
                self.pending.append(remaining)
                self.buffer = ''

            merged = ''.join(self.pending)
            result.append(merged)
            self.output_sentence_number += 1
            self.pending.clear()

        return result