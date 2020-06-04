'''
Function extracts rain data for a single day. Will return the average rainfall in quadrants whereby
the center is defined by the user. Will also return the average rainfall against time for each quadrant.

Inputs:
    date: date of interest
        string
    easting_lim, northing_lim: easting and northing of the specified center
        int or float
    latlong: 
        Boolean
        If True, the easting_lim and northing_lim are input as lattitude and longitude.

'''
import requests
import json
# import tool
from flood_tool import geo
from math import sqrt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def historic_API(date, easting_lim, northing_lim, latlong=False):
    url = 'https://environment.data.gov.uk/flood-monitoring/archive/readings-full-' + date + '.csv'
    data_csv = pd.read_csv(url)
    df=pd.DataFrame(data=data_csv)

    df = df.groupby('parameter')
    df = df.get_group('rainfall')
    df = df.reset_index()

    if latlong == True:
        easting_lim, northing_lim = geo.get_easting_northing_from_lat_long(easting_lim, northing_lim)
    
    values = []
    dates = []
    stations = []
    northing = []
    easting = []
    station_list = []
    northeast = []
    for row in range(0, len(df)):
        historic_values = df.loc[row, 'value']
        historic_date = df.loc[row, 'dateTime']
        station = df.loc[row, 'stationReference']   
        historic_values = pd.to_numeric(historic_values, errors='coerce')

        if isinstance(historic_values, float) == False:
            continue

        if station in station_list:
            stations.append(station)
            northing.append(northing[station_list.index(station)])
            easting.append(easting[station_list.index(station)])                
        else:
            station_list.append(station)
            station_url = 'https://environment.data.gov.uk/flood-monitoring/id/stations?parameter=rainfall&stationReference=' + str(station)
            coordinates = requests.get(station_url)
            coordinates = json.loads(coordinates.text)

            north = coordinates.get('items')[0].get('northing')
            east = coordinates.get('items')[0].get('easting')

            stations.append(station)
            northing.append(north)
            easting.append(east)

        values.append(historic_values)
        dates.append(historic_date)

    historic_rain = pd.DataFrame({'dates':dates[:], 'station':stations[:], 'northing':northing[:], 'easting':easting[:], 'values':values[:]})
    historic_rain['dates'] = historic_rain['dates'].map(lambda x: x.rstrip('Z'))
    # for line in historic_rain['dates']:
    #     if ':01T' in historic_rain['dates']:
    #         historic_rain['dates'][row] = historic_rain['dates'][row].str.replace(':01T', ':00T')

    historic_rain['date'], historic_rain['time'] = historic_rain['dates'].str.split('T', 1).str
    
    # pattern = '*:01'
    # for line in historic_rain['time']:
    #     if fnmatch(line, pattern):
    #         historic_rain.dates.loc[row] = historic_rain.dates.loc[row].replace('*$.:01', ':00', regex=True)
    #         # historic_rain['dates'][index=row] = historic_rain['dates'][index=row].replace(r'*$.:01', ':00')

    historic_rain = historic_rain.drop('dates', axis=1).drop('date', axis=1).sort_values(by='time', ascending=True)

    northeast = historic_rain.loc[(historic_rain.northing > northing_lim) & (historic_rain.easting > easting_lim)]
    northeast_averageT = northeast.groupby('time')['values'].mean().reset_index()
    northeast_average = northeast['values'].mean()

    southeast = historic_rain.loc[(historic_rain.northing < northing_lim) & (historic_rain.easting > easting_lim)]
    southeast_average = southeast['values'].mean()
    southeast_averageT = southeast.groupby('time')['values'].mean().reset_index()

    northwest = historic_rain.loc[(historic_rain.northing > northing_lim) & (historic_rain.easting < easting_lim)]
    northwest_average = northwest['values'].mean()
    northwest_averageT = northwest.groupby('time')['values'].mean().reset_index()

    southwest = historic_rain.loc[(historic_rain.northing < northing_lim) & (historic_rain.easting < easting_lim)]
    southwest_average = southwest['values'].mean()
    southwest_averageT = southwest.groupby('time')['values'].mean().reset_index()


    plt.figure(1)
    plt.title('Average rain per quadrant' + date)
    scale_ls = range(4)
    index_ls = ['NE', 'SE', 'NW', 'SW']
    area_data=[northeast_average, southeast_average, northwest_average, southwest_average]
    plt.xticks(scale_ls, index_ls)
    plt.xlabel('Quadrant')
    plt.ylabel('Average Rainfall (mm)')
    plt.bar(scale_ls,area_data )
    plt.savefig('quadrant.png')
    plt.show()
    

    plt.subplots()
    plt.title('England Rainfall Against Time for ' + date)

    plt.subplot(2, 2, 1)
    plt.plot(northwest_averageT['time'], northwest_averageT['values'])
    plt.xlabel('Time')
    plt.xticks(np.arange(0, len(northwest_averageT), 4), rotation=30)
    plt.ylabel('Average Rainfall (mm)')
    plt.title('North West')

    plt.subplot(2, 2, 2)
    plt.plot(northeast_averageT['time'], northeast_averageT['values'])
    plt.xlabel('Time')
    plt.xticks(np.arange(0, len(northeast_averageT), 4), rotation=30)
    plt.ylabel('Average Rainfall (mm)')
    plt.title('North East')

    plt.subplot(223)
    plt.plot(southwest_averageT['time'], southwest_averageT['values'])
    plt.xlabel('Time')
    plt.xticks(np.arange(0, len(southwest_averageT), 4), rotation=30)
    plt.ylabel('Average Rainfall (mm)')
    plt.title('South West')
    
    plt.subplot(224)
    plt.plot(southeast_averageT['time'], southeast_averageT['values'])
    plt.xlabel('Time')
    plt.xticks(np.arange(0, len(southeast_averageT), 4), rotation=30)
    plt.ylabel('Average Rainfall (mm)')
    plt.title('South East')
    
    plt.subplots_adjust(left=0.1, bottom=0.05, top=0.9, right=0.95, hspace=0.5)
    plt.savefig('quadrant_detail.png')
    plt.show()
    


historic_API('2019-01-03', 406689, 286822)
