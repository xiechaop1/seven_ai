from typing import List
from aivc.common.task_class import TCData
from aivc.model.embed.embed import EmbedModel
from aivc.config.config import L
import time
import numpy as np

class TaskClassifier:
    def __init__(self,
                question:str=""):
        self.question = question 

    def classify(self, threshold=0.8):
        all_similar_words = []
        task_indices = []
        for task in TCData().task_classes:
            task_indices.append(len(all_similar_words))
            all_similar_words.extend(task.similar_words)
        
        start_time = time.time()
        scores = EmbedModel().score(self.question, all_similar_words)
        L.debug(f"score cost time:{int((time.time()-start_time)*1000)}ms")
        
        max_score = 0
        max_task_name = TCData.DEFAULT
        
        for i, task in enumerate(TCData().task_classes):
            start_index = task_indices[i]
            end_index = task_indices[i + 1] if i < len(task_indices) - 1 else len(scores)
            task_max_score = max(scores[start_index:end_index])
            
            if task_max_score > max_score:
                max_score = task_max_score
                max_task_name = task.name

        if max_score > threshold:
            index = int(np.where(scores == max_score)[0][0])
            L.debug(f"result question:{self.question} task_name:{max_task_name} score:{max_score} similar_words:{all_similar_words[index]}")
            return max_task_name
        else:
            return TCData.DEFAULT

    def get_keywords(self,task_name:str) -> List[str]:
        keywords = []
        for task in TCData().task_classes:
            if task.name == task_name:
                keywords = task.keywords
        return keywords