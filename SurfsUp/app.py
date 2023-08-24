# Import the dependencies
import numpy as np
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect an existing database into a new model
Base = automap_base()

# Reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

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
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end>"
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
    
    return jsonify(prcp)

# Create stations route
@app.route("/api/v1.0/stations")

# Define the stations function
def stations():
    # Create our session from Python to the DB
    Session = sessionmaker(bind=engine)
    session = Session()

    """Return a list of stations."""
    # Perform a query to retrieve all station information
    stations = session.query(Station.station).all()

    session.close()

    # Convert into normal list
    station_list = list(np.ravel(stations))

    return jsonify(station_list)

# Create tobs route
@app.route("/api/v1.0/tobs")

# Define the tobs function
def tobs():
    # Create our session from Python to the DB
    Session = sessionmaker(bind=engine)
    session = Session()

    """Return a list of tobs."""

    session.close()

    # Convert into dictionary
