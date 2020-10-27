from collections import defaultdict
import numpy as np
import pandas as pd
import os
import math

class Scorer:

    def __init__(self, data_dir_name: str=None):
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),data_dir_name)
        self.scores_df = pd.read_csv(os.path.join(data_dir_name,'scores.csv'))
        self.scores_df = self.scores_df[self.scores_df.congress >= 107]

        self.mean_d_scores = defaultdict(lambda: np.zeros(2))
        self.mean_r_scores = defaultdict(lambda: np.zeros(2))
        self.mean_scores = defaultdict(lambda: np.zeros(2))

        self.official_scores = {}
        self.init_scores()

    def init_scores(self):
        d_total = defaultdict(lambda: 0)
        r_total = defaultdict(lambda: 0)
        total = defaultdict(lambda: 0)
        for index, row in self.scores_df.iterrows():
            # Make sure score is valid
            score = np.array([float(row['nominate_dim1']), float(row['nominate_dim2'])])
            if math.isnan(score[0]) or math.isnan(score[1]):
                continue

            # Get state and party information
            state = row['state_abbrev']
            party = 'I'
            if row['party_code'] == 200:
                party = 'R'
            elif row['party_code'] == 100:
                party = 'D'

            # Update member score
            if row['congress'] >= 102:
                official_id = row['bioname'].split(',')[0].lower() + '_' + state + '_' + party
                self.official_scores[official_id] = score
                self.official_scores[row['icpsr']] = score
            else:
                continue

            # Update estimate scores
            if row['party_code'] == 200:
                r_total[state] += 1
                delta = score - self.mean_r_scores[state]
                self.mean_r_scores[state] += delta / r_total[state]
            elif row['party_code'] == 100:
                d_total[state] += 1
                delta = score - self.mean_d_scores[state]
                self.mean_d_scores[state] += delta / d_total[state]

            total[state] += 1
            delta = score - self.mean_scores[state]
            self.mean_scores[state] += delta / total[state]

    def get_score(self, politician, code):
        name, party = politician
        names = name.split(' ')
        state = code[:2]
        # Look for each combination of last name tokens in order
        for i in reversed(range(len(names))):
            official_id = ' '.join(names[i:]).lower() + '_' + state + '_' + party
            if official_id.startswith('trump'):
                # Per https://projects.fivethirtyeight.com/congress-trump-score/, Rick Scott is the "Trumpiest Senator"
                official_id = 'scott_FL_R'
            elif official_id.startswith('biden'):
                official_id = 'biden_DE_D'
            if official_id in self.official_scores:
                return self.official_scores[official_id]

        if party == 'R':
            return self.mean_r_scores[state]
        elif party == 'D':
            return self.mean_d_scores[state]
        else:
            return self.mean_scores[state]

    def get_icpsr_score(self, icpsr):
        return self.official_scores[icpsr]
