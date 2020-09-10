from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base

_engine = create_engine('postgresql://localhost:5432/rip_api')
Session = sessionmaker(bind=_engine)
Base.metadata.create_all(_engine)
