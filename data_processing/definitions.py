INFO_DIRS = {
    'ec': 'ec_info',
    'house': 'district_info',
    'house_2018': 'district_info_2018',
    'senate': 'state_info',
    'senate_2018': 'state_info_2018'
}

RACE_STATUS = {
    'ec': {
        'safe_dem': {'MA', 'DE', 'NY', 'CA', 'DC', 'HI', 'MD', 'VT'},
        'likely_dem': {'MECD1', 'IL', 'NJ', 'WA', 'RI', 'CT'},
        'leans_dem': {'MI', 'NM', 'NH', 'OR', 'CO', 'ME', 'VA'},
        'toss_up': {'TX', 'NECD2', 'MECD2', 'OH', 'NC', 'PA', 'NV', 'GA', 'MN', 'AZ', 'FL', 'IA'},
        'leans_gop': {'IN', 'MO', 'MT', 'SC'},
        'likely_gop': {'UT', 'AK', 'LA', 'KS', 'MS', 'AR'},
        'safe_gop': {'SD', 'TN', 'AL', 'KY', 'ID', 'NE', 'ND', 'OK', 'WV', 'WY'}
    },
    'house': {
        'likely_dem': {'PA7', 'FL27', 'AZ2', 'NY19', 'CA45', 'KS3', 'CA7', 'IL6', 'WA8', 'IL17', 'NJ5', 'FL13', 'NY3', 'NV4', 'NJ11', 'NY18', 'FL7'},
         'leans_dem': {'NH1', 'NH2', 'NJ3', 'MI8', 'NJ7', 'NV3', 'WI3', 'IL14', 'CA48', 'TX32', 'AZ1', 'MN2', 'CA10', 'MI11', 'TX7'},
         'toss_up': {'CO3', 'NJ2', 'VA7', 'GA6', 'NE2', 'CA25', 'IN5', 'TX21', 'ME2', 'GA7', 'IA2', 'PA1', 'NY2', 'PA10', 'OK5', 'MO2', 'SC1', 'TX24', 'PA8', 'TX23', 'VA2', 'TX10', 'FL26', 'IA1', 'NY22', 'IL13', 'CA39', 'NM2', 'IA3', 'UT4', 'TX22', 'MI3', 'MN7', 'NY11', 'PA17', 'FL15'},
         'leans_gop': {'NY24', 'IA4', 'MI6', 'AR2', 'MN1', 'OH12', 'VA5', 'KY6', 'KS2', 'MTAL', 'FL16', 'WA3', 'NY1', 'AZ6'},
         'likely_gop': {'AKAL', 'MN8', 'OH1', 'CA50', 'TX31', 'CA8', 'NY27', 'CA1', 'NC9', 'CA4', 'NC8', 'CA22'}
    },
    'house_2018': {
        'likely_dem': {'AZ9', 'CA24', 'FL13', 'IA2', 'NH2', 'NJ2', 'NJ5', 'NM1', 'NY3', 'NY18', 'PA5', 'PA6', 'PA8', 'PA17', 'WI3'},
        'leans_dem': {'AZ2', 'CA7', 'CA49', 'CO6', 'FL7', 'IA1', 'KS3', 'MN2', 'MN3', 'NH1', 'NJ7', 'NJ11', 'OR5', 'PA7', 'VA10'},
        'toss_up': {'AKAL', 'AZ1', 'CA10', 'CA25', 'CA39', 'CA45', 'CA48', 'FL15', 'FL26', 'FL27', 'GA6', 'IA3', 'IL6', 'IL14', 'KS2', 'KY6', 'ME2', 'MI8', 'MI11', 'MN1', 'MN7', 'MTAL', 'NC9', 'NJ3', 'NM2', 'NV3', 'NV4', 'NY19', 'NY22', 'PA1', 'PA10', 'PA16', 'TX7', 'TX32', 'UT4', 'VA5'},
        'leans_gop': {'CA50', 'FL16', 'FL18', 'GA7', 'IA4', 'IL12', 'IL13', 'MI6', 'MI7', 'MN8', 'NC2', 'NC13', 'NE2', 'NY1', 'NY11', 'NY27', 'OH1', 'OH12', 'SC1', 'TX23', 'VA2', 'WA3', 'WA5', 'WI1', 'WV3'},
        'likely_gop': {'AR2', 'AZ6', 'AZ8', 'CA4', 'CA21', 'CA22', 'CO3', 'FL6', 'FL25', 'IN2', 'MO2', 'NC8', 'NY2', 'NY24', 'OH10', 'OH14', 'OK5', 'PA14', 'TX21', 'TX22'}
    },
    'senate': {
        'likely_dem': {'NJ', 'VA'},
        'leans_dem': {'NH', 'CO', 'NM'},
        'toss_up': {'MN', 'MI', 'ME', 'NC', 'GA', 'MT', 'SC', 'IA'},
        'leans_gop': {'TX', 'MS', 'KS', 'AK', 'GA2'},
        'likely_gop': {'AL', 'KY', 'TN'}
    },
    'senate_2018': {
        'likely_dem': {'PA'},
        'leans_dem': {'MI', 'MN2', 'NJ', 'WI', 'OH'},
        'toss_up': {'AZ', 'FL', 'IN', 'MO', 'MT', 'NV', 'WV', 'TN'},
        'leans_gop': {'ND', 'TX'},
        'likely_gop': {'MS2'}
    }
}


