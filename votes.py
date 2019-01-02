import pandas as pd
from scorer import Scorer
from sklearn.linear_model import LogisticRegression
import numpy as np

class ChamberVote:
    def __init__(self, path_to_vote_file, official_scorer):
        self.votes = []
        self.scores = []
        vote_df = pd.read_csv(path_to_vote_file)
        for index, row in vote_df.iterrows():
            if row['V1'] == 1:
                self.votes.append(1)
            else:
                self.votes.append(-1)
            
            icpsr = row['icpsr']
            score = official_scorer.get_icpsr_score(icpsr)
            self.scores.append(score)
        
        X = np.array(self.scores)
        y = np.array(self.votes)
        logreg = LogisticRegression(C=1e5, solver='lbfgs', multi_class='multinomial')
        logreg.fit(X, y)
        
        self.logreg = logreg

    def get_result(self, scores):
        return self.logreg.predict(scores).sum()

