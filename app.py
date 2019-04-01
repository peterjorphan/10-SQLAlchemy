#####################################################################################################
# Step 1 - Database Setup (copied from climate_starter.ipynb)
#####################################################################################################
import numpy as np
import pandas as pd
import datetime as dt

# Python SQL toolkit and Object Relational Mapper
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

engine = create_engine("sqlite:///Resources/hawaii.sqlite", connect_args={'check_same_thread':False})
conn = engine.connect()
Base = automap_base()
Base.prepare(engine, reflect=True)
# Base.classes.keys()
Measurement = Base.classes.measurement
Station = Base.classes.station
session = Session(bind=engine)

# Design a query to retrieve the last 12 months of precipitation data and plot the results
last_date = session.query(func.max(Measurement.date)).first()[0]
year_date = str((dt.datetime.strptime(last_date, '%Y-%m-%d') - dt.timedelta(days=365)).date())
query_yr = session.query(Measurement.date, Measurement.prcp).\
        order_by(Measurement.date).\
        filter(Measurement.date >= year_date)
df = pd.read_sql(query_yr.statement, conn, index_col='date')
df = df.sort_index()
df = df.rename(columns={'prcp':'Precipitation'})
# df.plot(x_compat=True)

# Design a query to show how many stations are available in this dataset?
AvailableStations = session.query(Measurement.station).group_by(Measurement.station).count()

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
    
    return session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()

print(calc_temps('2012-02-28', '2012-03-05'))

#####################################################################################################
# Step 2 - Climate App
#####################################################################################################

# List of stations
StationList = session.query(Station.station, Station.name).all()

# query for the dates and temperature observations from a year from the last data point.
temp = session.query(Measurement.date, Measurement.tobs).filter(Measurement.date >= year_date).all()


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
    return jsonify(StationList)

@app.route("/api/v1.0/tobs")
def tobs():
    print("Server received request for 'Temperature' page...")

    # Return a JSON list of Temperature Observations (tobs) for the previous year
    return jsonify(temp)

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
