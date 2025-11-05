import pandas as pd

# dataframe with city, price area and coordinates
data = [
    ['NO1', 'Oslo', 10.7522, 59.9139],
    ['NO2', 'Kristiansand', 8.0000, 58.1467],
    ['NO3', 'Trondheim', 10.3951, 63.4305],
    ['NO4', 'Tromsø', 18.9553, 69.6496],
    ['NO5', 'Bergen', 5.3221, 60.39299],
]

city_data_df = pd.DataFrame(data, columns=['PriceArea', 'City', 'Longitude', 'Latitude'])
