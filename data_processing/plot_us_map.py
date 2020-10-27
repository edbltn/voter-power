import copy
import matplotlib as mpl
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap as Basemap
from matplotlib.colors import rgb2hex
from matplotlib.patches import Polygon

def plot_districts(data, min, max):
    assert len(data) in (435, 436) # 435 + DC (!)
    # 
    plt.figure(figsize=(20,15))
    m = Basemap(llcrnrlon=-119,llcrnrlat=22,urcrnrlon=-64,urcrnrlat=49,
            projection='lcc',lat_1=33,lat_2=45,lon_0=-95)
    # draw state boundaries.
    # data from U.S Census Bureau
    # http://www.census.gov/geo/www/cob/st2000.html
    shp_info = m.readshapefile('../shapefiles/us-116th-congressional-districts','states',drawbounds=False)
    state_codes = pd.read_csv('../data/state_info/state_codes.csv')

    # choose a color for each state based on population density.
    colors={}
    district_names=[]
    cmap = copy.copy(mpl.cm.get_cmap("Reds_r"))
    cmap.set_under(color='grey')
    vmin = min; vmax = max # set range
    for shapedict in m.states_info:
        state_number = int(shapedict['STATE'])
        state_info = state_codes.loc[state_codes['number'] == state_number]
        
        # skip non-states.
        district_name = 'skip'
        if not state_info.empty:
            state_code = state_info.postal_code.item()
            district_basename = shapedict['BASENAME']
            if district_basename.endswith('(at Large)'):
                district_name = f'{state_code}AL'
            elif not district_basename.endswith('not defined'):
                district_number = int(district_basename)
                district_name = f'{state_code}{district_number}'
            if district_name != 'skip':
                val = data[district_name]
            else:
                val = 0
            # calling colormap with value between 0 and 1 returns
            # rgba value.  Invert color range (hot colors are high
            # population), take sqrt root to spread out colors more.
            colors[district_name] = cmap(1.-np.sqrt((val-vmin)/(vmax-vmin)))[:3]
        district_names.append(district_name)
    
    # cycle through state names, color each one.
    ax = plt.gca() # get current axes instance
    ax.set_facecolor('aliceblue')

    for nshape,seg in enumerate(m.states):
        # skip DC and Puerto Rico.
        if district_names[nshape] != 'skip':
        # Offset Alaska and Hawaii to the lower-left corner.
            if district_names[nshape].startswith('AK'):
            # Alaska is too big. Scale it down to 23% first, then translate it.
                seg = list(map(lambda x: (0.4 * x[0] + 750000, 0.4 * x[1] - 1800000), seg))
            if district_names[nshape].startswith('HI'):
                seg = list(map(lambda x: (x[0] + 5200000, x[1] - 1600000), seg))

            color = rgb2hex(colors[district_names[nshape]])
            poly = Polygon(seg,facecolor=color,edgecolor='grey')
            ax.add_patch(poly)

    plt.ylim(-500000,3300000)
    plt.xlim(-500000,5000000)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    plt.title('Districts by Estimated Monetary Value of One Vote')
    plt.show()

def plot_states(data, min, max):
    assert len(data) in (50, 51)
    # Lambert Conformal map of lower 48 states.
    plt.figure(figsize=(20,15))
    m = Basemap(llcrnrlon=-119,llcrnrlat=22,urcrnrlon=-64,urcrnrlat=49,
            projection='lcc',lat_1=33,lat_2=45,lon_0=-95)
    # draw state boundaries.
    # data from U.S Census Bureau
    # http://www.census.gov/geo/www/cob/st2000.html
    shp_info = m.readshapefile('../shapefiles/st99_d00','states',drawbounds=False)

    # choose a color for each state based on population density.
    colors={}
    statenames=[]
    cmap = copy.copy(mpl.cm.get_cmap("Reds_r"))
    cmap.set_under(color='grey')
    vmin = min; vmax = max # set range.
    for shapedict in m.states_info:
        statename = shapedict['NAME']
        # skip DC and Puerto Rico.
        if statename not in ['District of Columbia','Puerto Rico']:
            val = data[statename]
            # calling colormap with value between 0 and 1 returns
            # rgba value.  Invert color range (hot colors are high
            # population), take sqrt root to spread out colors more.
            colors[statename] = cmap(1.-np.sqrt((val-vmin)/(vmax-vmin)))[:3]
        statenames.append(statename)
    # cycle through state names, color each one.
    ax = plt.gca() # get current axes instance
    ax.set_facecolor('aliceblue')

    for nshape,seg in enumerate(m.states):
        # skip DC and Puerto Rico.
        if statenames[nshape] not in ['Puerto Rico', 'District of Columbia']:
        # Offset Alaska and Hawaii to the lower-left corner.
            if statenames[nshape] == 'Alaska':
            # Alaska is too big. Scale it down to 40% first, then translate it.
                seg = list(map(lambda x: (0.4*x[0] + 750000, 0.4*x[1]-1800000), seg))
            if statenames[nshape] == 'Hawaii':
                seg = list(map(lambda x: (x[0] + 5200000, x[1]-1600000), seg))

            color = rgb2hex(colors[statenames[nshape]])
            poly = Polygon(seg,facecolor=color,edgecolor='grey')
            ax.add_patch(poly)

    plt.ylim(-500000,3300000)
    plt.xlim(-500000,5000000)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    plt.title('States by Estimated Monetary Value of One Vote')
    plt.show()

