from scorer import Scorer
import pandas as pd
from collections import defaultdict
import os

class Country:
    def __init__(self, data_dir_name):
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),data_dir_name)
        state_info_dir = data_dir + '/state_info'
        district_info_dir = data_dir + '/district_info'

        # Get scorer
        official_scorer = Scorer(data_dir_name)

        # Get state postal codes
        state_codes_df = pd.read_csv(os.path.join(state_info_dir, 'state_codes.csv'))
        state_codes = {}
        for name, postal_code in zip(state_codes_df['name'], state_codes_df['postal_code']):
            state_codes[name] = postal_code

        # Get turnouts by state and by district
        state_results_df = pd.read_csv(os.path.join(state_info_dir, 'state_results.csv'))
        district_results_df = pd.read_csv(os.path.join(district_info_dir, 'district_results.csv'))

        state_turnouts = {}
        turnout_key = 'Estimated or Actual 2018 Total Ballots Counted'
        for state, turnout in zip(state_results_df['State Abv'], state_results_df[turnout_key]):
            if type(state) is str and state != 'DC':
                state_turnouts[state] = int(turnout.replace(',','')) 
                state_turnouts[state + '2'] = int(turnout.replace(',','')) 

        district_codes = defaultdict(lambda: set())
        district_turnouts = defaultdict(lambda: 0)
        for code, turnout in zip(district_results_df['code'], district_results_df['turnout']):
            # Associate code with relevant state, e.g. 'AZ1' to 'AZ'
            district_codes[code[:2]].add(code)
            district_turnouts[code] += turnout 

        # Get elected officials
        senators_df = pd.read_csv(os.path.join(state_info_dir, 'senators.csv'))
        representatives_df = pd.read_csv(os.path.join(district_info_dir, 'representatives.csv'))

        senators = {} 
        for index, row in senators_df.iterrows():
            state_name = row['state']
            senator = row['name']
            party = row['party']
            state_code = state_codes[state_name]
            if state_code not in senators:
                senators[state_code] = (senator, party)
            else:
                senators[state_code + '2'] = (senator, party)

        representatives = {}
        for index, row in representatives_df.iterrows():
            state_name = row['state']
            district = row['district']
            representative = row['name']
            party = row['party']
            state_code = state_codes[state_name]
            representatives[state_code + district] = representative
        
        # Initialize states
        self.states = []
        for name, postal_code in state_codes.items():
            self.states.append(State(name, postal_code, district_codes[postal_code], 
                                     state_turnouts, district_turnouts, 
                                     senators, representatives,
                                     data_dir))
         
class State:
    def __init__(self, name, postal_code, district_codes, 
                 state_turnouts, district_turnouts,
                 senators, representatives,
                 data_dir):
        self.name = name
        self.postal_code = postal_code

        state_info_dir = data_dir + '/state_info'
        district_info_dir = data_dir + '/district_info'

        self.senate_seats = {}
        for code in [postal_code, postal_code + '2']:
            self.senate_seats[code] = Race(code, 
                                           state_turnouts[code], senators[code],
                                           state_info_dir)
        
        self.districts = {}
        for code in district_codes:
            self.districts[code] = Race(code, district_turnouts[code],
                    representatives[code],
                    district_info_dir)
 
class Race:
    def __init__(self, code, turnout, winner, info_dir):
        self.code = code
        self.turnout = turnout
        self.winner = winner
        self.contested = False
        self.candidates = None

        for poll in os.listdir(info_dir):
            if poll.startswith(code):
                self.contested = True
                poll_df = pd.read_csv(os.path.join(info_dir, poll))


class District: 
    def __init__(self, code, polls):
        self.code = code
