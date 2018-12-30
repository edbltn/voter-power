import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap as Basemap
from matplotlib.colors import rgb2hex
from matplotlib.patches import Polygon

def plot_districts(data, min, max):
    assert len(data) == 435 
    print('hi')

def plot_states(data, min, max):
    assert len(data) == 50 
    # Lambert Conformal map of lower 48 states.
    plt.figure(figsize=(20,15))
    m = Basemap(llcrnrlon=-119,llcrnrlat=22,urcrnrlon=-64,urcrnrlat=49,
            projection='lcc',lat_1=33,lat_2=45,lon_0=-95)
    # draw state boundaries.
    # data from U.S Census Bureau
    # http://www.census.gov/geo/www/cob/st2000.html
    shp_info = m.readshapefile('data/st99_d00','states',drawbounds=True)

    # choose a color for each state based on population density.
    colors={}
    statenames=[]
    cmap = plt.cm.hot
    cmap.set_under(color='lightgrey')
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
            poly = Polygon(seg,facecolor=color,edgecolor='black')
            ax.add_patch(poly)

    plt.ylim(-500000,3300000)
    plt.xlim(-500000,5000000)
    plt.title('States by Estimated Cost of One Vote')
    plt.show()

