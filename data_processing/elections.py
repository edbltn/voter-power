import numpy as np
import pandas as pd
import re

from collections import defaultdict
from scipy.stats import truncnorm, binom

from scorer import Scorer
from definitions import *

class Country:
    def __init__(self, data_dir_name):
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),data_dir_name)
        self.official_scorer = Scorer(self.data_dir)
        self.state_codes = {}
        self.state_turnouts = {}
        self.district_turnouts = defaultdict(lambda: 0)
        self.ec_turnouts = defaultdict(lambda: 0)
        self.ec_values = defaultdict(lambda: 0)
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
        state_results_df = pd.read_csv(os.path.join(state_info_dir, '2018_state_results.csv'))
        ec_values_df = pd.read_csv(os.path.join(state_info_dir, 'ec_values.csv'))
        district_results_df = pd.read_csv(os.path.join(district_info_dir, '2018_district_results.csv'))

        turnout_key = 'Estimated or Actual 2018 Total Ballots Counted'
        for state, turnout in zip(state_results_df['State Abv'], state_results_df[turnout_key]):
            if type(state) is str:
                self.state_turnouts[state] = int(turnout.replace(',', ''))
                if state != 'DC':
                    self.state_turnouts[state + '2'] = int(turnout.replace(',', ''))

        for i, row in ec_values_df.iterrows():
            state = row['US State']
            code = self.state_codes[state]
            self.ec_values[code] = row['Electoral Votes']

        district_codes = defaultdict(lambda: set())
        for code, turnout in zip(district_results_df['code'], district_results_df['turnout']):
            # Associate code with relevant state, e.g. 'AZ1' to 'AZ'
            district_codes[code[:2]].add(code)
            self.district_turnouts[code] += turnout
            if code.startswith('NE') or code.startswith('ME'):
                self.state_turnouts[code.replace('E', 'ECD')] = turnout

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

        self.infer_polling()

    def _infer_polling(self, race, status, projected_vote_shares, sample_sizes):

        similar_vote_shares = projected_vote_shares[status]
        weights = sample_sizes[status]

        # Only if not "safe"
        if similar_vote_shares:
            gop_projected_vote_share = sum(np.array(similar_vote_shares) * np.array(weights)) / sum(weights)
            race.sample_size = np.mean(sample_sizes[status])
        else:
            return

        underdog_party = 'D' if status.endswith('gop') else 'R'
        incumbent_party = race.incumbent[1]
        if incumbent_party == 'R':
            challenger_party = 'D'
        elif incumbent_party == 'D':
            challenger_party = 'R'
        else:
            challenger_party = underdog_party

        if challenger_party == 'R':
            race.incumbent_projected_vote_share = 1 - gop_projected_vote_share
        else:
            race.incumbent_projected_vote_share = gop_projected_vote_share

        race.challenger_score = self.official_scorer.get_score(('_', challenger_party), race.code)
        race.challenger_party = challenger_party
        race.contested = True

    def infer_polling(self):
        """
        Infer polling data for states that are missing it.

        :return:
        """
        projected_vote_shares = defaultdict(lambda: [])
        sample_sizes = defaultdict(lambda: [])
        statuses = {}
        for election, races in RACE_STATUS.items():
            for status, codes in races.items():
                info_dir = self.data_dir + '/' + INFO_DIRS[election]
                for code in codes:
                    if not election.endswith('2018'):
                        statuses[election + code] = status
                    # Create a dummy race to get an average, if possible
                    race = Race(
                        code=code,
                        turnout=self.state_turnouts,
                        # Had to use dummy incumbent
                        incumbent=('_', 'R'),
                        official_scorer=self.official_scorer,
                        info_dir=info_dir
                    )
                    if race.contested:
                        projected_vote_shares[status].append(race.incumbent_projected_vote_share)
                        sample_sizes[status].append(race.sample_size)

        for state in self.states:
            for district in state.districts.values():
                if district.contested or ('house' + district.code not in statuses):
                    continue
                self._infer_polling(district, statuses['house' + district.code], projected_vote_shares, sample_sizes)
            for senate_seat in state.senate_seats.values():
                if senate_seat.contested or ('senate' + senate_seat.code not in statuses):
                    continue
                self._infer_polling(senate_seat, statuses['senate' + senate_seat.code], projected_vote_shares, sample_sizes)
            for electors in state.electoral_college.values():
                if electors.contested or ('ec' + electors.code not in statuses):
                    continue
                self._infer_polling(electors, statuses['ec' + electors.code], projected_vote_shares, sample_sizes)

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

    def simulate_government(self, bias, vote):
        results = []

        for state in self.states:
            for electors in state.electoral_college.values():
                margin, party = electors.simulate_party(bias, vote)
                results.append({
                    'chamber': 'ec',
                    'state': state.name,
                    'code': electors.code,
                    'party': party,
                    'value': electors.value,
                    'margin': margin
                })
            for district in state.districts.values():
                margin, party = district.simulate_party(bias, vote)
                results.append({
                    'chamber': 'house',
                    'state': state.name,
                    'code': district.code,
                    'party': party,
                    'value': district.value,
                    'margin': margin
                })
            for seat in state.senate_seats.values():
                margin, party = seat.simulate_party(bias, vote)
                results.append({
                    'chamber': 'senate',
                    'state': state.name,
                    'code': seat.code,
                    'party': party,
                    'value': seat.value,
                    'margin': margin
                })

        return pd.DataFrame(results)



class State:
    def __init__(self, name, postal_code, district_codes, country): 
        self.name = name
        self.postal_code = postal_code
        self.district_codes = district_codes
        self.country = country

        self.state_info_dir = country.data_dir + '/state_info'
        self.district_info_dir = country.data_dir + '/district_info'
        self.ec_info_dir = country.data_dir + '/ec_info'

        self.ec_value = country.ec_values[postal_code]
        self.cd_codes = []
        if postal_code in ('ME', 'NE'):
            self.cd_codes = [f"{postal_code}CD{i+1}" for i in range(self.ec_value - 2)]

        incumbent = ('Trump', 'R') if postal_code not in RACE_STATUS['ec']['safe_dem'] else ('Biden', 'D')
        self.electoral_college = {
            code: Race(
                code=code,
                turnout=country.state_turnouts[code],
                incumbent=incumbent,
                official_scorer=country.official_scorer,
                info_dir=self.ec_info_dir,
                value=self.ec_value - len(self.cd_codes) if len(code) == 2 else 1
            )
            for code in self.cd_codes + [postal_code]
        }

        self.senate_seats = {}
        self.districts = {}

        if postal_code != 'DC':
            self.init_congress()

    def init_congress(self):
        for code in [self.postal_code, self.postal_code + '2']:
            self.senate_seats[code] = Race(
                code=code,
                turnout=self.country.state_turnouts[code],
                incumbent=self.country.senators[code],
                official_scorer=self.country.official_scorer,
                info_dir=self.state_info_dir
            )

        for code in self.district_codes:
            self.districts[code] = Race(
                code=code,
                turnout=self.country.district_turnouts[code],
                incumbent=self.country.representatives[code],
                official_scorer=self.country.official_scorer,
                info_dir=self.state_info_dir
            )

class Race:
    def __init__(self, code, turnout, incumbent, official_scorer, info_dir, value=1):
        """
        Races represent the state of an individual election.
        You need to set the incumbent at init time, so the default score can be recorded in "uncontested" or safe races
        :param code:
        :param turnout:
        :param incumbent:
        :param official_scorer:
        :param info_dir:
        :param value:
        """
        self.code = code
        self.turnout = turnout
        self.incumbent = incumbent
        self.contested = False
        self.incumbent_projected_vote_share = 1
        self.sample_size = 0
        self.official_scorer = official_scorer
        self.incumbent_score = official_scorer.get_score(incumbent, code)
        self.challenger_score = None
        self.challenger_party = 'D' if incumbent[1] == 'R' else 'R'
        self.value = value

        for poll in os.listdir(info_dir):
            if poll.startswith(code + '_'):
                self.contested = True
                poll_df = pd.read_csv(os.path.join(info_dir, poll))
                self.update_margin_and_scores(poll_df)
                break

    def update_margin_and_scores(self, poll_df):
        """
        Now we have a little more information - calculate the totals for the incumbent party, and the challenger party
        :param poll_df:
        :return:
        """
        columns = list(poll_df.columns.values)
        candidates = columns[4:-1] if ('MoE' in poll_df) else columns[3:-1]
        incumbent_party = self.incumbent[1]

        self.incumbent_score = None
        for candidate in candidates:
            party = candidate[-2]
            if party != 'D' and party != 'R':
                party = 'I'
            if self.challenger_score is None and party != incumbent_party:
                challenger_tuple = (candidate[:-4], party)
                self.challenger_score = self.official_scorer.get_score(challenger_tuple, self.code)
                self.challenger_party = party
            if self.incumbent_score is None and party == incumbent_party:
                incumbent_tuple = (candidate[:-4], party)
                self.incumbent = incumbent_tuple
                self.incumbent_score = self.official_scorer.get_score(incumbent_tuple, self.code)

        if self.incumbent_score is None:
            self.incumbent_score = self.official_scorer.get_score(self.incumbent, self.code)
        if self.challenger_score is None:
            self.challenger_score = self.official_scorer.get_score(('_', self.challenger_party), self.code)

        total_margin = 0
        rows_considered = 0
        for index, row in poll_df.iterrows():
            if 'Average' in row['Poll'] or 'Results' in row['Poll']:
                # Ignore RCP Average and Final Results
                continue
            elif rows_considered > 3 or ('10/' not in row['Date'] and '11/' not in row['Date']):
                # Only look at polls in October or November
                break

            rows_considered += 1
            try:
                sample_size = int(row['Sample'][:-3])
            except:
                sample_size = 1
            # Assuming voters make a largely rational shift on Election Day
            results = [float(row[c]) if c[-2] == incumbent_party else -float(row[c])
                       for c in candidates
                       if re.match(r'\d+', str(row[c]))]
            margin = sum(results)
            self.sample_size += sample_size
            total_margin += margin * sample_size

        if self.sample_size == 0:
            self.contested = False
        else:  
            self.incumbent_projected_vote_share = 0.5 + (total_margin / self.sample_size) / (2 * 100)
        
    def tipping_point_probability(self):
        # Get the probability that a voter will change the outcome of this election
        if not self.contested:
            return 0.0

        norm_count_rv = self.norm_vote_count_distribution() 
        p_tipping_point_func = lambda norm_count: self.decisive_vote_probability(norm_count)
        p_tipping_point = norm_count_rv.expect(p_tipping_point_func)

        return p_tipping_point
    
    def norm_vote_count_distribution(self):
        # 1. Model vote share distribution based on polls
        n = self.sample_size
        p = self.incumbent_projected_vote_share
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
        p = self.incumbent_projected_vote_share
        expected_value = n * p
        variance = n * p * (1 - p)
        stddev = np.sqrt(variance)
        
        count = norm_count * stddev + expected_value
        return count

    def simulate_party(self, bias, vote):
        # Simulate a race score based on a given bias against republicans
        if self.contested:
            norm_count = self.norm_vote_count_distribution().rvs(1)
            count = self.denormalize_vote_count(norm_count)
            p = count / self.sample_size

            # Bias against republicans
            if self.incumbent[1] == 'R':
                p -= bias
            else:
                p += bias

            # Get election result
            margin = np.abs(p - 0.5)[0]
            if p >= 0.5:
                if self.incumbent[1] == 'I':
                    party = 'R' if vote.get_result(self.incumbent_score.reshape(1, -1)) > 0 else 'D'
                else:
                    party = self.incumbent[1]
            else:
                if self.challenger_party == 'I':
                    party = 'R' if vote.get_result(self.challenger_score.reshape(1, -1)) > 0 else 'D'
                else:
                    party = self.challenger_party
        else:
            margin = 1
            if self.incumbent[1] == 'I':
                party = 'R' if vote.get_result(self.incumbent_score.reshape(1, -1)) > 0 else 'D'
            else:
                party = self.incumbent[1]

        return margin, party

    def simulate_score(self, bias):
        # Simulate a race score based on a given bias against republicans
        if self.contested:
            norm_count = self.norm_vote_count_distribution().rvs(1)
            count = self.denormalize_vote_count(norm_count) 
            p = count / self.sample_size

            # Bias against republicans
            if self.incumbent[1] == 'R':
                p -= bias
            else:
                p += bias

            # Get election result
            if p >= 0.5:
                return self.incumbent_score
            else:
                return self.challenger_score 
        else:
            return self.incumbent_score

if __name__ == '__main__':
    country = Country('../data')
    senate_seat_probabilities = {}

    district_probabilities = {}
    for state in country.states:
        for district in state.districts.values():
            p = district.tipping_point_probability()
            district_probabilities[district.code] = p

    senate_seat_probabilities = {}
    for state in country.states:
        for seat in state.senate_seats.values():
            p = seat.tipping_point_probability()
            if not seat.code.endswith('2'):
                senate_seat_probabilities[state.name] = p
            else:
                senate_seat_probabilities[state.name] += p

    election_bias = np.random.normal(0, 0.01)
    senate_scores = country.simulate_senate(election_bias)

    from data_processing.votes import ChamberVote

    vote = ChamberVote('../data/votes/obamacare_senate.csv',
                       country.official_scorer)

    house_scores = country.simulate_house(election_bias)
    vote.get_result(house_scores)

    election_bias = -0.02
    make_up = country.simulate_government(election_bias, vote)
    print(make_up)

