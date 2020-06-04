'''
Depending on location (postcode's lattitude and longitude), finds stations in proximity and 
extracts rainfall data in mm. Combining to risk bands, determines whether a flood warning 
should be issued. Specifically, there is no flood warning when flood risk is equal to zero 
'Yellow Warning, Medium Risk' is issued when flood risk is 'Very Low' and rainfall is greater than 3 mm/15 mins
'Yellow Warning, Medium Risk' is issued when flood risk is 'Low' and rainfall is greater 2 mm/15mins
'Yellow Warning, Medium Risk' is issued when flood risk is 'Medium' and rainfall is between 2 and 3 mm/15mins
'Red Warning, High Risk' is issued when flood risk is 'Medium' and rainfall is greater than 3 mm/15 mins
'Yellow Warning, Medium Risk' is issued when flood risk is 'High' and rainfall is smaller than 2 mm/15 mins
'Red Warning, High Risk' is issued when flood risk is 'High' and rainfall is greater than 2 mm/15 mins
'''
import requests
import json
from flood_tool import Tool
from flood_tool import geo
from math import sqrt
import numpy as np
import csv

with open('./flood_tool/resources/api_postcodes.csv', 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        postcodes = row

tool = Tool('./flood_tool/resources/postcodes.csv', './flood_tool/resources/flood_probability.csv', './flood_tool/resources/property_value.csv')
lat_long = tool.get_lat_long(postcodes)

E_N = np.array(geo.get_easting_northing_from_lat_long(lat_long[:, 0], lat_long[:,1]))
url = 'https://environment.data.gov.uk/flood-monitoring/id/stations?parameter=rainfall'

resp = requests.get(url)
data = json.loads(resp.text)
coord = data.get('items')


for i in range(3):
    station = ''
    a = []
    lat = lat_long[i, 0]
    long =lat_long[i, 1]

    prox_url = 'https://environment.data.gov.uk/flood-monitoring/id/stations?parameter=rainfall' + '&lat=' + str(lat) + '&long=' + str(long) + '&dist=10000'
    prox = requests.get(prox_url)
    prox_data = json.loads(prox.text)
    prox_stations = prox_data.get('items')
    length = len(prox_data.get('items'))
    for j in range(0, length, 1):
        if coord[j].get('northing') == None:
            continue
        if coord[j].get('easting') == None:
            continue

        else:
            northing = int(coord[j]['northing'])
            easting = int(coord[j]['easting'])
            distance = np.sqrt(np.abs((easting - E_N[0, i])**2 + (northing - E_N[1, i])**2))  
            a.append(distance)
            index_min = min(range(len(a)), key=a.__getitem__)
    station_reference = coord[index_min]['notation']
    station = 'https://environment.data.gov.uk/flood-monitoring/id/measures?parameter=rainfall' + '&stationReference=' + station_reference
    print(station)
    station_data = requests.get(station)
    station_data = json.loads(station_data.text)
    if station_data.get('items')[0].get('latestReading') == None:
        print('Station', station_reference, 'has no value. Assume 0 rain.')
    else:
        station_value = station_data.get('items')[0].get('latestReading').get('value')
        print('Station', station_reference, ':', station_value, 'mm of rain.')

        flood_risk = tool.get_annual_flood_risk(postcodes, tool.get_easting_northing_flood_probability(E_N[0], E_N[1]))
        
        risk = flood_risk[i]
        if risk == 'Zero':
            print('No Risk')
        elif risk == 'Very Low':
            if station_value < 3:
                print('No Risk')
            elif 3 < station_value:
                print('Yellow Warning, Medium Risk')
        elif risk == 'Low':
            if station_value <= 2:
                print('No Risk')
            elif 2 < station_value < 3:
                print('Yellow Warning, Medium Risk')
            elif 3 <= station_value:
                print('Yellow Waring, Medium Risk')
        elif risk == 'Medium':
            if station_value < 2:
                print('No Risk')
            elif 2 < station_value < 3:
                print('Yellow Warning, Medium Risk')
            elif 3 <= station_value:
                print('Red Warning, High Risk')
        elif risk == 'High':
            if station_value < 2:
                print('Yellow Warning, Medium Risk')
            elif 2 <= station_value:
                print('Red warning, High Risk')
