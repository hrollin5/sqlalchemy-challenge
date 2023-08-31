# Import the dependencies
import numpy as np
import datetime as dt
from pathlib import Path

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################

database_path = Path("../Resources/hawaii.sqlite")
engine = create_engine(f"sqlite:///{database_path}")


# Reflect an existing database into a new model
Base = automap_base()

# Reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station

# Create our session from Python to the DB
Session = sessionmaker(bind=engine)
session = Session()

#################################################
# Flask Setup
#################################################

app = Flask(__name__)

#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """Hawaii Climate API."""
    return (
        "Hawaii Climate API<br/><br/><br/>"
        "Available Routes:<br/>"
        "<br/>Daily precipitation for most recent year of data:<br/>"
        "/api/v1.0/precipitation<br/>"
        "<br/>List of stations:<br/>"
        "/api/v1.0/stations<br/>"
        "<br/>Daily observed temperature for most recent year of data:<br/>"
        "/api/v1.0/tobs<br/>"
        "<br/>Daily Temperature Info for Custom Date Range:<br/>"
        "/api/v1.0/<start><br/>"
        "*Enter a desired start date in YYYY-MM-DD format or "
        "enter start and end dates in YYYY-MM-DD/YYYY-MM-DD format*<br/>"
        "<br/>Aggregated Temperature in Custom Date Range:<br/>"
        "/api/v1/0/aggregate/<start><br/>"
        "*Enter a desired start date in YYYY-MM-DD format or "
        "enter start and end dates in YYYY-MM-DD/YYYY-MM-DD format*"
    )

# Create precipitation route
@app.route("/api/v1.0/precipitation")

# Define the precipitation function
def precipitation():
    # Create our session from Python to the DB
    Session = sessionmaker(bind=engine)
    session = Session()

    """Return precipitation data for the most recent year."""
    # Get most recent date
    most_recent_date = session.query(func.max(measurement.date)).scalar()
    # Convert to datetime
    most_recent_datetime = dt.datetime.strptime(most_recent_date,"%Y-%m-%d").date()
    # Find date 1 year ago from most recent date
    query_date = most_recent_datetime - dt.timedelta(days=365)
    # Perform a query to retrieve the data and precipitation
    last_year_prcp = session.query(measurement.date, measurement.prcp)\
        .filter(measurement.date >= query_date).all()

    session.close()

    # Convert into dictionary
    prcp = {date: prcp for date, prcp in last_year_prcp}
    prcp_with_heading=["Date: Precipitation in inches", prcp]
    # Return the JSON representation of the dictionary

    return jsonify(prcp_with_heading)

# Create stations route
@app.route("/api/v1.0/stations")

# Define the stations function
def stations():
    # Create our session from Python to the DB
    Session = sessionmaker(bind=engine)
    session = Session()

    """Return a list of stations."""
    # Perform a query to retrieve all station information
    stations = session.query(station.station, station.name).all()

    session.close()

    # Convert into normal list
    station_list = [{"Station ID": station, "Station Name": name} for station, name in stations]


    # Return the JSON representation of the list
    return jsonify(station_list)

# Create tobs route
@app.route("/api/v1.0/tobs")

# Define the tobs function
def tobs():
    # Create our session from Python to the DB
    Session = sessionmaker(bind=engine)
    session = Session()

    """Return a list of tobs."""
    # Find correct query date:
        # Get most recent date
    most_recent_date = session.query(func.max(measurement.date)).scalar()
        # Convert to datetime
    most_recent_datetime = dt.datetime.strptime(most_recent_date,"%Y-%m-%d").date()
        # Find date 1 year ago from most recent date
    query_date = most_recent_datetime - dt.timedelta(days=365)

    # Find most active station
    descending_stations = session.query(measurement.station, func.count(measurement.id)).\
        group_by(measurement.station).order_by(func.count(measurement.id).desc()).all()
    most_active_station = descending_stations[0][0]

    # Using the most active station and query date, perform a query to retrieve the tobs
    station_recent = session.query(measurement.date, measurement.tobs).\
        filter(measurement.station == most_active_station).\
        filter(measurement.date >= query_date)
    
    session.close()

    # Convert into dictionary
    tobs_list = ["Date: Observed Temeperature", {date: tobs for date, tobs in station_recent}]

    # Return the JSON representation of the list
    return jsonify(tobs_list)


# Create start end route
@app.route('/api/v1.0/<start>/')
@app.route('/api/v1.0/<start>/<end>')

# Define stats function for start and end dates
def stats(start, end=None):
    # Create our session from Python to the DB
    Session = sessionmaker(bind=engine)
    session = Session()
 
    """Return Daily Temperature Minimum, Maximum, and Average for all dates after {start}."""
    sel = [measurement.date, func.avg(measurement.tobs), func.max(measurement.tobs),\
            func.min(measurement.tobs)]

    # Perform query with no end date
    if not end: 

        # Convert start date to datetime
        start = dt.datetime.strptime(start, "%Y-%m-%d")

        # Perform query
        results = session.query(*sel).filter(measurement.date >= start).group_by(measurement.date).all()

        session.close()

        # Convert into list of dictionaries
        from_start = [
            {
            "Date": date, "Temperature":
            {"Average": round(avg_temp, 2),
            "Maximum": max_temp,
            "Minimum": min_temp
            }}
            for date, avg_temp, max_temp, min_temp in results]

        # Return the JSON representation of the list
        return jsonify(from_start)
    
    """Daily Temperature Minimum, Maximum, and Average for dates between {start} and {end}"""
    # Convert dates to datetime
    start = dt.datetime.strptime(start, "%Y-%m-%d")
    end = dt.datetime.strptime(end, "%Y-%m-%d")

    # Perform query with end date
    results = session.query(*sel).filter(measurement.date >= start).filter(measurement.date <= end).\
        group_by(measurement.date).all()

    session.close()

    # Convert into list of dictionaries
    start_to_end = [
        {
        "Date": date, "Temperature":
        {"Average": round(avg_temp, 2),
        "Maximum": max_temp,
        "Minimum" : min_temp
        }}
        for date, avg_temp, max_temp, min_temp in results]

    # Return the JSON representation of the list
    return jsonify(start_to_end)

# Create start end aggregate route
@app.route('/api/v1.0/aggregate/<start>/')
@app.route('/api/v1.0/aggregate/<start>/<end>')

# Define aggregate function for start and end dates
def aggregate(start, end=None):
    # Create our session from Python to the DB
    Session = sessionmaker(bind=engine)
    session = Session()
 
    """Return average, maximum, and minimum temperature"""
    # Select statement
    sel = [func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)]

    # Perform query with no end date
    if not end:
        # Convert date to datetime
        start = dt.datetime.strptime(start, "%Y-%m-%d")
        
        # Perform query
        results = session.query(*sel).\
            filter(measurement.date >= start).all()
        
        # Close the session
        session.close()

        # Unravel results into a 1D array and convert to a list
        temps = list(np.ravel(results))

        # Convert to dictionary to format
        start = {"Start Date": start, "Temperature":
        {"Average": round(temps[1], 2),
        "Maximum": temps[2],
        "Minimum" : temps[0]
        }}

        # Return Results
        return jsonify(start)
    
    # Perform query with end date

    """Return average, maximum, and minimum temperature for a range of dates"""
    # Convert dates to datetime
    start = dt.datetime.strptime(start, "%Y-%m-%d")
    end = dt.datetime.strptime(end, "%Y-%m-%d")

    # Preform query
    results = session.query(*sel).\
        filter(measurement.date >= start).\
        filter(measurement.date <= end).all()
        
    session.close()

    # Unravel results into a 1D array and convert to a list
    temps = list(np.ravel(results))

    # Convert to dictionary to format
    start_to_end = {"Begin Date": start, "End Date": end, "Temperature":
        {"Average": round(temps[1], 2),
        "Maximum": temps[2],
        "Minimum" : temps[0]
        }}
    
    # Return results
    return jsonify(start_to_end)

if __name__ == '__main__':
    app.run(debug=True)


    

  
