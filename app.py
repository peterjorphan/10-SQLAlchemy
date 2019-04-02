#####################################################################################################
# Step 1 - Database Setup (saved from climate_starter.ipynb) - Step 2 at line 310
#####################################################################################################

#!/usr/bin/env python
# coding: utf-8

# In[1]:


# get_ipython().run_line_magic('matplotlib', 'inline')
from matplotlib import style
style.use('fivethirtyeight')
import matplotlib.pyplot as plt


# In[2]:


import numpy as np
import pandas as pd


# In[3]:


import datetime as dt


# # Reflect Tables into SQLAlchemy ORM

# In[4]:


# Python SQL toolkit and Object Relational Mapper
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func


# In[5]:


engine = create_engine("sqlite:///Resources/hawaii.sqlite", connect_args={'check_same_thread':False})
conn = engine.connect()


# In[6]:


# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)


# In[7]:


# We can view all of the classes that automap found
Base.classes.keys()


# In[8]:


# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station


# In[9]:


# Create our session (link) from Python to the DB
session = Session(bind=engine)


# # Exploratory Climate Analysis

# In[10]:


# Design a query to retrieve the last 12 months of precipitation data and plot the results

# Calculate the date 1 year ago from the last data point in the database
last_date = session.query(func.max(Measurement.date)).first()[0]
year_date = str((dt.datetime.strptime(last_date, '%Y-%m-%d') - dt.timedelta(days=365)).date())


# Perform a query to retrieve the data and precipitation scores
query_yr = session.query(Measurement.date, Measurement.prcp).            order_by(Measurement.date).            filter(Measurement.date >= year_date)


# Save the query results as a Pandas DataFrame and set the index to the date column
df = pd.read_sql(query_yr.statement, conn, index_col='date')

# Sort the dataframe by date
df = df.sort_index()
df = df.rename(columns={'prcp':'Precipitation'})

# Use Pandas Plotting with Matplotlib to plot the data
df.plot(x_compat=True)


# In[11]:


# Use Pandas to calcualte the summary statistics for the precipitation data
df.describe()


# In[12]:


# Design a query to show how many stations are available in this dataset?
AvailableStations = session.query(Measurement.station).group_by(Measurement.station).count()
AvailableStations


# In[13]:


# What are the most active stations? (i.e. what stations have the most rows)?
# List the stations and the counts in descending order.
ActiveStations = session.query(Measurement.station, func.count(Measurement.station)).                                group_by(Measurement.station).                                order_by(func.count(Measurement.date).desc()).all()
ActiveStations


# In[14]:


# The station with the most observations is the first on the list:
MostActive = ActiveStations[0][0]
MostActive


# In[15]:


# Using the station id from the previous query, calculate the lowest temperature recorded, 
# highest temperature recorded, and average temperature most active station?

MostActiveStats = session.query(func.min(Measurement.tobs), 
                                func.max(Measurement.tobs),
                                func.avg(Measurement.tobs)).\
                                filter_by(station=MostActive).all()
MostActiveStats


# In[16]:


# Choose the station with the highest number of temperature observations.

# Need to count again in case there are null values in the tobs column:
StationMostT = session.query(Measurement.station, func.count(Measurement.tobs)).                                group_by(Measurement.station).                                order_by(func.count(Measurement.date).desc()).all()[0][0]

# Query the last 12 months of temperature observation data for this station and plot the results as a histogram

t = session.query(Measurement.tobs).    filter(Measurement.date >= year_date, Measurement.station==StationMostT)

t_df = pd.read_sql(t.statement, conn)

t_df.plot(kind='hist')


# In[17]:


# This function called `calc_temps` will accept start date and end date in the format '%Y-%m-%d' 
# and return the minimum, average, and maximum temperatures for that range of dates
def calc_temps(start_date, end_date):
    """TMIN, TAVG, and TMAX for a list of dates.
    
    Args:
        start_date (string): A date string in the format %Y-%m-%d
        end_date (string): A date string in the format %Y-%m-%d
        
    Returns:
        TMIN, TAVE, and TMAX
    """
    
    return session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).        filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()

# function usage example
print(calc_temps('2012-02-28', '2012-03-05'))


# In[18]:


# Use your previous function `calc_temps` to calculate the tmin, tavg, and tmax 
# for your trip using the previous year's data for those same dates.
StartDate = '2019-04-15'
EndDate = '2019-04-25'

# Since the last date in the dataset is in 2017, selection was done 2yr back:
PreviousStart = '2017-04-15'
PreviousEnd = '2017-04-25'
tstats = calc_temps(PreviousStart, PreviousEnd)
print(tstats)


# In[19]:


# Plot the results from your previous query as a bar chart. 
# Use "Trip Avg Temp" as your Title
# Use the average temperature for the y value
# Use the peak-to-peak (tmax-tmin) value as the y error bar (yerr)

tstats_df = pd.DataFrame(tstats, columns=['min', 'avg', 'max'])

tstats_df['avg'].plot(kind='bar',
                      yerr = tstats_df['max']-tstats_df['min'],
                      title = "Trip Avg Temp", 
                      figsize=(3,8)
                     )
plt.show()


# In[20]:


# Calculate the total amount of rainfall per weather station for your trip dates using the previous year's matching dates.
# Sort this in descending order by precipitation amount and list the station, name, latitude, longitude, and elevation

rainfall = session.query(Station.station, 
                         Station.name, 
                         Station.latitude, 
                         Station.longitude, 
                         Station.elevation,
                         func.sum(Measurement.prcp)).\
                        filter(Measurement.station == Station.station).\
                        filter(Measurement.date >= PreviousStart, Measurement.date <= PreviousEnd).\
                        group_by(Measurement.station).\
                        order_by(func.sum(Measurement.prcp).desc()).\
                        all()


rainfall


# ## Optional Challenge Assignment

# In[21]:


# Create a query that will calculate the daily normals 
# (i.e. the averages for tmin, tmax, and tavg for all historic data matching a specific month and day)

def daily_normals(date):
    """Daily Normals.
    
    Args:
        date (str): A date string in the format '%m-%d'
        
    Returns:
        A list of tuples containing the daily normals, tmin, tavg, and tmax
    
    """
    
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]
    return session.query(*sel).filter(func.strftime("%m-%d", Measurement.date) == date).all()
    
daily_normals("01-01")


# In[46]:


# calculate the daily normals for your trip
# push each tuple of calculations into a list called `normals`

# Set the start and end date of the trip 
start = dt.datetime.strptime(StartDate, "%Y-%m-%d").date()
end = dt.datetime.strptime(EndDate, "%Y-%m-%d").date()

# Use the start and end date to create a range of dates
date_range = [start + dt.timedelta(days=i) for i in range((end-start).days+1)]

# Stip off the year and save a list of %m-%d strings
date_list = [i.strftime("%m-%d") for i in date_range]

# Loop through the list of %m-%d strings and calculate the normals for each date
normals = [daily_normals(i)[0] for i in date_list]
normals


# In[51]:


# Load the previous query results into a Pandas DataFrame and add the `trip_dates` range as the `date` index
normals_df = pd.DataFrame(normals, columns=['tmin', 'tavg', 'tmax'], index=date_range)
normals_df


# In[56]:


# Plot the daily normals as an area plot with `stacked=False`
normals_df.plot(kind='area', stacked=False)


# In[ ]:

#####################################################################################################
# Step 2 - Climate App
#####################################################################################################

from flask import Flask, jsonify
app = Flask(__name__)

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        "Available Routes:<br/>"
        "/api/v1.0/precipitation<br/>"
        "/api/v1.0/stations<br/>"
        "/api/v1.0/tobs<br/>"
        "/api/v1.0/&ltstart><br/>"
        "/api/v1.0/&ltstart>/&ltend><br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    print("Server received request for 'Precipitation' page...")

    # Convert the query results to a Dictionary using date as the key and prcp as the value
    df_dict = df.to_dict()['Precipitation']
    
    # Return the JSON representation of your dictionary.
    return jsonify(df_dict)

@app.route("/api/v1.0/stations")
def stations():
    print("Server received request for 'Stations' page...")
    
    # Return a JSON list of stations from the dataset.
    return jsonify(session.query(Station.station, Station.name).all())

@app.route("/api/v1.0/tobs")
def tobs():
    print("Server received request for 'Temperature' page...")

    # Return a JSON list of Temperature Observations (tobs) for the previous year
    return jsonify(session.query(Measurement.date, Measurement.tobs).filter(Measurement.date >= year_date).all())

@app.route("/api/v1.0/<start>")
def start(start):
    print("Server received request for 'Start' page...")
    
    # Calculate the TMIN, TAVG, and TMAX for all dates greater than and equal to the start date.
    return jsonify(calc_temps(start, last_date))

@app.route("/api/v1.0/<start>/<end>")
def startend(start, end):
    print("Server received request for 'Start/End' page...")

    # Calculate the TMIN, TAVG, and TMAX for dates between the start and end date inclusive.
    return jsonify(calc_temps(start, end))

if __name__ == '__main__':
    app.run(debug=True)
