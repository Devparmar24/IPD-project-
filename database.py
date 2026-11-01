from sqlalchemy import create_engine, Column, Integer, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# Initialize the SQLAlchemy Base
Base = declarative_base()

class FieldTelemetry(Base):
    __tablename__ = 'field_telemetry'
    
    # Primary Key & Timestamp
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Active Sensors (Required fields)
    soil_moisture = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    
    # Future RS485 Sensors (Nullable so the code doesn't break right now)
    nitrogen = Column(Float, nullable=True)
    phosphorus = Column(Float, nullable=True)
    potassium = Column(Float, nullable=True)
    soil_ph = Column(Float, nullable=True)


# Create the SQLite database file in your project directory
engine = create_engine('sqlite:///farm_telemetry.db')

# Generate the table schema
Base.metadata.create_all(engine)

# Create a session factory to use in other scripts
Session = sessionmaker(bind=engine)

if __name__ == "__main__":
    print("Database schema initialized. Ready to accept data.")