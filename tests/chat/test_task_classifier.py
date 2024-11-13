from aivc.chat.task_classifier import TaskClassifier,TCData

def test_task_classifier_case1():
    questions = TCData.BUILT_IN_QUESTION
    for i, question in enumerate(questions):
        task_classifier = TaskClassifier(question=question)
        task_name = task_classifier.classify()
        print(f"question:{question} task_name:{task_name}")
        assert task_name == TCData.task_classes[i].name

def test_task_classifier_case2():
    questions = {
        "你是谁": TCData.ABOUT,
        "唱歌": TCData.Songs,
        "背首唐诗？": TCData.DEFAULT,
    }
    for question, task_name in questions.items():
        task_classifier = TaskClassifier(question=question)
        assert task_classifier.classify() == task_name


if __name__ == '__main__':
    test_task_classifier_case1()
    test_task_classifier_case2()

 