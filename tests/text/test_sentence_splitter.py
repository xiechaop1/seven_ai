from aivc.text.sentence_splitter import SentenceSplitter

def assert_equal(actual, expected, message=""):
    if actual != expected:
        raise AssertionError(f"{message}\nExpected: {expected}\nGot: {actual}")

def test_basic_sentence_split():
    splitter = SentenceSplitter(min_sentence_length=20)
    chunks = ["Hello.", "This is a test.", "How are you doing today?"]
    results = []
    
    for chunk in chunks:
        results.extend(splitter.add_chunk(chunk))
    results.extend(splitter.finalize())
    
    # 验证输出的句子数量和内容
    assert_equal(len(results), 2, "Should have exactly 2 results")
    assert_equal(results[0], ("Hello.", False), "First sentence should output immediately")
    assert_equal(results[1], ("This is a test.How are you doing today?", False), 
                 "Subsequent sentences should be merged until min length is reached")
    print("Basic sentence split test passed")

def test_chinese_sentence_split():
    splitter = SentenceSplitter(min_sentence_length=15)
    chunks = ["你好。", "这是测试。", "这是一个比较长的句子。"]
    results = []
    
    for chunk in chunks:
        results.extend(splitter.add_chunk(chunk))
    results.extend(splitter.finalize())
    
    # 验证输出的句子数量和内容
    assert_equal(len(results), 2, "Should have exactly 2 results")
    assert_equal(results[0], ("你好。", False), "First sentence should output immediately")
    assert_equal(results[1], ("这是测试。这是一个比较长的句子。", False), 
                 "Subsequent sentences should be merged until min length is reached")
    print("Chinese sentence split test passed")


def test_finalize():
    splitter = SentenceSplitter(min_sentence_length=20)
    results = []

    # 添加多个短句
    results.extend(splitter.add_chunk("Short1."))  # 第一句，立即输出
    results.extend(splitter.add_chunk("Short2."))  # 待处理
    results.extend(splitter.add_chunk("Short3."))  # 待处理
    final_results = splitter.finalize()

    # 验证结果数量
    assert_equal(len(results), 1, "Should have 1 result before finalize")
    assert_equal(len(final_results), 1, "Finalize should output pending sentences")

    # 验证内容
    assert_equal(results[0], ("Short1.", False), "First sentence should output immediately")
    merged_pending = "Short2.Short3."
    assert_equal(final_results[0], (merged_pending, False), "Pending sentences should be merged in finalize")
    print("Finalize test passed")

def test_increasing_length():
    splitter = SentenceSplitter(min_sentence_length=5)
    chunks = [
        "Hi.", 
        "Hello.", 
        "This is longer.",
        "This is the longest sentence in the test case!"
    ]
    
    all_results = []
    for chunk in chunks:
        all_results.extend(splitter.add_chunk(chunk))
    all_results.extend(splitter.finalize())
    
    # 验证每次输出的句子长度是否递增
    prev_len = 0
    for sent, _ in all_results:
        current_len = len(sent)
        assert current_len >= prev_len, f"Sentence length should increase: {sent}"
        prev_len = current_len
    
    print("Increasing length test passed")

def test_modified_splitting_logic():
    splitter = SentenceSplitter(min_sentence_length=10)
    chunks = [
        "这是一个非常长的第一句话，应该被强制断句，因为它超过了最小长度。",
        "第二句话来测试最小长度。",
        "第三句需要累积到一定长度才能输出。",
        "这是第四句话，继续累积。",
        "第五句话。",
    ]
    results = []

    for chunk in chunks:
        results.extend(splitter.add_chunk(chunk))
    results.extend(splitter.finalize())

    # 验证输出的句子数量和内容
    print("Number of sentences:", len(results))
    for idx, sentence in enumerate(results, 1):
        print(f"Sentence {idx}: {sentence} (Length: {len(sentence)})")

    print("Modified splitting logic test passed")

def test_refined_splitting_logic():
    splitter = SentenceSplitter(min_sentence_length=10)
    chunks = [
"""
好的,小朋友,七宝给你讲个《小兔子乖乖》的故事吧!从前,有一只小兔子,名字叫乖乖。乖乖很听妈妈的话,每天都会乖乖地吃饭、睡觉、玩耍。有一天,乖乖的妈妈要出门办事,临走前叮嘱乖乖:"乖乖,妈妈要出去一会儿,你乖乖待在家里,不要给陌生人开门哦。乖乖点点头说:"好的妈妈,我会乖乖待在家里,不给陌生人开门的。妈妈走后,乖乖一个人在家里玩玩具。这时,门外传来敲门声:"咚咚咚"。乖乖问:"谁呀?"门外传来一个陌生的声音:"我是你妈妈的朋友,给你带了好吃的,快开门吧。乖乖想了想,说:"我不认识你,不能给你开门。陌生人又说:"我是你妈妈让我来的,快开门吧。乖乖还是说:"我不认识你,不能给你开门。这时,妈妈回来了,看到陌生人,问:"你是谁?为什么敲我家的门?"陌生人支支吾吾地说:"我.我是来送东西的。妈妈说:"我们不认识你,请你离开。陌生人只好灰溜溜地走了。妈妈夸奖乖乖:"乖乖真棒!没有给陌生人开门,保护了自己。乖乖开心地笑了。小朋友,这个故事告诉我们,不要轻易给陌生人开门哦。要像乖乖一样,学会保护自己。你记住了吗?	
"""
    ]
    results = []

    for chunk in chunks:
        results.extend(splitter.add_chunk(chunk))
    results.extend(splitter.finalize())

    # 输出分割结果
    for idx, sentence in enumerate(results, 1):
        print(f"Sentence {idx}: {sentence} (Length: {len(sentence)}) (target length: {splitter.get_target_length(idx)})")

    print("Refined splitting logic test passed")


def main():
    print("Running sentence splitter tests...")
    # test_basic_sentence_split()
    # test_chinese_sentence_split()
    # test_finalize()
    # test_increasing_length() 
    # test_long_sentence_split()
    test_refined_splitting_logic()
    # test_modified_splitting_logic()
    print("All tests passed!")

if __name__ == '__main__':
    main()
