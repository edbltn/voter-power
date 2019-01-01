import math
from scorer import Scorer
from scipy.stats import truncnorm, binom
from scipy.misc import comb
import numpy as np
import pandas as pd
from collections import defaultdict
import os

class Country:
    def __init__(self, data_dir_name):
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),data_dir_name)
        self.official_scorer = Scorer(self.data_dir)
        self.state_codes = {}
        self.state_turnouts = {}
        self.district_turnouts = defaultdict(lambda: 0)
        self.senators = {} 
        self.representatives = {}
        self.states = []
        
        state_info_dir = self.data_dir + '/state_info'
        district_info_dir = self.data_dir + '/district_info'

        # Get state postal codes
        state_codes_df = pd.read_csv(os.path.join(state_info_dir, 'state_codes.csv'))
        for name, postal_code in zip(state_codes_df['name'], state_codes_df['postal_code']):
            self.state_codes[name] = postal_code

        # Get turnouts by state and by district
        state_results_df = pd.read_csv(os.path.join(state_info_dir, 'state_results.csv'))
        district_results_df = pd.read_csv(os.path.join(district_info_dir, 'district_results.csv'))

        turnout_key = 'Estimated or Actual 2018 Total Ballots Counted'
        for state, turnout in zip(state_results_df['State Abv'], state_results_df[turnout_key]):
            if type(state) is str and state != 'DC':
                self.state_turnouts[state] = int(turnout.replace(',','')) 
                self.state_turnouts[state + '2'] = int(turnout.replace(',','')) 

        district_codes = defaultdict(lambda: set())
        for code, turnout in zip(district_results_df['code'], district_results_df['turnout']):
            # Associate code with relevant state, e.g. 'AZ1' to 'AZ'
            district_codes[code[:2]].add(code)
            self.district_turnouts[code] += turnout 

        # Get elected officials
        senators_df = pd.read_csv(os.path.join(state_info_dir, 'senators.csv'))
        representatives_df = pd.read_csv(os.path.join(district_info_dir, 'representatives.csv'))

        for index, row in senators_df.iterrows():
            state_name = row['state']
            senator = row['name']
            party = row['party']
            state_code = self.state_codes[state_name]
            if state_code not in self.senators:
                self.senators[state_code] = (senator, party)
            else:
                self.senators[state_code + '2'] = (senator, party)

        for index, row in representatives_df.iterrows():
            state_name = row['state']
            district = row['district']
            representative = row['name']
            party = row['party']
            state_code = self.state_codes[state_name]
            self.representatives[state_code + district] = (representative, party)
        
        # Initialize states
        for name, postal_code in self.state_codes.items():
            self.states.append(State(name, postal_code, district_codes[postal_code], self))

    def simulate_house(self, bias):
        scores = np.zeros((435,2))  
        i = 0 
        for state in self.states:
            for district in state.districts.values():
                scores[i] = district.simulate_score(bias)
                i += 1
        return scores

    def simulate_senate(self, bias):
        scores = np.zeros((100,2))
        i = 0 
        for state in self.states:
            for seat in state.senate_seats.values():
                scores[i] = seat.simulate_score(bias)
                i += 1
        return scores

class State:
    def __init__(self, name, postal_code, district_codes, country): 
        self.name = name
        self.postal_code = postal_code

        state_info_dir = country.data_dir + '/state_info'
        district_info_dir = country.data_dir + '/district_info'

        self.senate_seats = {}
        for code in [postal_code, postal_code + '2']:
            self.senate_seats[code] = Race(code, 
                                           country.state_turnouts[code],
                                           country.senators[code],
                                           country.official_scorer,
                                           state_info_dir)
 
        self.districts = {}
        for code in district_codes:
            self.districts[code] = Race(code,
                                        country.district_turnouts[code],
                                        country.representatives[code],
                                        country.official_scorer,
                                        district_info_dir)

class Race:
    def __init__(self, code, turnout, winner, official_scorer, info_dir):
        self.code = code
        self.turnout = turnout
        self.winner = winner
        self.contested = False
        self.winner_projected_vote_share = 1
        self.sample_size = 0
        self.official_scorer = official_scorer
        self.winner_score = official_scorer.get_score(winner, code)
        self.challenger_score = self.winner_score

        poll_df = None
        for poll in os.listdir(info_dir):
            if poll.startswith(code):
                self.contested = True
                poll_df = pd.read_csv(os.path.join(info_dir, poll))
                self.update_margin_and_scores(poll_df)
                break

    def update_margin_and_scores(self, poll_df):
        # Function that uses to polls to determine challenger score and expected margin
        columns = list(poll_df.columns.values)
        total_vote_share = 0
        top = np.array([4, 5]) if 'MoE' in poll_df else np.array([3, 4])
        for index, row in poll_df.iterrows():

            # Use final results to determine winner
            if row['Poll'] == 'Final Results':
                results = row[4:-1] if 'MoE' in poll_df else row[3:-1]
                results_array = np.array(results)
                top = results_array.argsort()
                top += 4 if 'MoE' in poll_df else 3
                second_place = columns[top[-2]]
                # Get party
                party = second_place[-2]
                if party != 'D' and party != 'R':
                    party = 'I'
                challenger = (second_place[:-4], party)
                self.challenger_score = self.official_scorer.get_score(challenger,
                                                                       self.code)
            # Ignore RCP Average
            elif row['Poll'] == 'RCP Average':
                continue

            # Only look at polls in October or November
            elif '10/' in row['Date'] or '11/' in row['Date']:
                sample_size = int(row['Sample'][:-3])
                self.sample_size += sample_size
                total_vote_share += (50 + row[top[-1]] - row[top[-2]]) * sample_size

        if self.sample_size == 0:
            self.contested = False
        else:  
            self.winner_projected_vote_share = (total_vote_share / self.sample_size) / 100
        
    def tipping_point_probability(self):
        if not self.contested:
            return 0.0

        norm_count_rv = self.norm_vote_count_distribution() 
        p_tipping_point_func = lambda norm_count: self.decisive_vote_probability(norm_count)
        p_tipping_point = norm_count_rv.expect(p_tipping_point_func)

        return p_tipping_point
    
    def norm_vote_count_distribution(self):
        # 1. Model vote share distribution based on polls
        n = self.sample_size
        p = self.winner_projected_vote_share
        expected_value = n * p
        variance = n * p * (1 - p)
        stddev = np.sqrt(variance)
        # 2. Model projected vote count (polls only) as a truncated normal distribution:
        # - mean: n * p
        # - variance: n * p * (1 - p)
        # - bounds: between 0 and n
        # This will give a margin of error for the polls based on how many samples were drawn
        a, b = (0 - expected_value) / stddev, (n - expected_value) / stddev
        norm_count_rv = truncnorm(a, b)
        return norm_count_rv
 
    def decisive_vote_probability(self, norm_count):
        count = self.denormalize_vote_count(norm_count)
        p = count / self.sample_size
        
        # When the vote count is exactly half, or just over half, every vote is decisive
        # Compute probability of this outcome (Binomial random variable) 
        n = self.turnout
        k = np.ceil(n/2)
        return binom.pmf(k, n, p)

    def denormalize_vote_count(self, norm_count):
        # Recover projected vote share from truncated normalized count
        n = self.sample_size
        p = self.winner_projected_vote_share
        expected_value = n * p
        variance = n * p * (1 - p)
        stddev = np.sqrt(variance)
        
        count = norm_count * stddev + expected_value
        return count
    
    def simulate_score(self, bias):
        # Simulate a race score based on a given bias against republicans
        if self.contested:
            norm_count = self.norm_vote_count_distribution().rvs(1)
            count = self.denormalize_vote_count(norm_count) 
            p = count / self.sample_size

            # Bias against republicans
            if self.winner[1] == 'R':
                p -= bias
            else:
                p += bias

            # Get election result
            if p >= 0.5:
                return self.winner_score
            else:
                return self.challenger_score 
        else:
            return self.winner_score
