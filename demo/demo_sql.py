import datetime
import os
from pathlib import Path

import yaml
from mps_database import PathMatcher, sql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# https://www.youtube.com/watch?v=51RpDZKShiw
# https://www.slideshare.net/jamdatadude/introduction-to-sqlalchemy-orm


def connect():
    if 1:
        uri = "sqlite:///test_db.db"
    if 0:
        # uri = [DB_TYPE]+[DB_CONNECTOR]://[USERNAME]:[PASSWORD]@[HOST]:[PORT]/[DB_NAME]
        # uri = "postgresql://scott:tiger@localhost:5432/mydatabase"
        # uri = "postgresql://henriknf:simula@localhost:5432/mps_database"
        DB_USER = "henriknf"
        DB_PASS = "simula"
        IP = "localhost"
        DB_PORT = "5432"
        DB_NAME = "mps_database"
        uri = f"postgresql://{DB_USER}:{DB_PASS}@{IP}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(uri, echo=True)
    return engine


def _get_x_by_name(name, cls, session):

    query = session.query(cls).filter(getattr(cls, "name") == name)
    if query.count() > 0:
        return query.one()
    else:
        x = cls(name=name)
        session.add(x)
        return x


def get_cell_line_by_name(cell_line: str, session):
    return _get_x_by_name(cell_line, sql.CellLine, session)


def get_experiment_by_name(experiment: str, session):
    return _get_x_by_name(experiment, sql.Experiment, session)


def folder_to_datetime(folder):
    date = folder.split("_")[0]

    if len(date) == 6:
        year = int(f"20{date[:2]}")
        month = int(date[2:4])
        day = int(date[4:])
    else:
        # TODO: Hanlde this exception
        assert len(date) == 8
        year = int(date[:4])
        month = int(date[4:6])
        day = int(date[6:])
    return datetime.date(year, month, day)


def pipeline():

    main_inputdir = Path("../tests/test_data/data")
    folder = "190820_Ver_Alf_SCVI273_direct"
    folder_path = main_inputdir.joinpath(folder)
    config_filename = Path("../config_files/190820_Ver_Alf_SCVI273_direct.yaml")
    with open(config_filename, "r") as f:
        config = yaml.load(f)

    cell_line_name = config.get("cell_line", "SCVI273")
    experiment_name = config.get("experiemnt", folder)

    pathmatcher = PathMatcher(config, root=folder_path)

    print(folder_path)

    engine = connect()
    sql.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    # Session = sessionmaker()
    # Session.configure(bind=engine)
    session = Session()

    # Each folder is a separate experiment
    experiment = get_experiment_by_name(experiment_name, session)
    experiment.operator = "Berenice"
    experiment.date = folder_to_datetime(folder)
    session.add(experiment)
    # Each experiment is one a separate cell line
    cell_line = get_cell_line_by_name(cell_line_name, session)

    drugs = dict(session.query(sql.Drug.name, sql.Drug).all())
    # lst = []
    for root, dirs, files in os.walk(folder_path):
        for f in files:
            path = Path(root).joinpath(f)

            if path.suffix == ".nd2":

                mps_data = pathmatcher(path)
                data = mps_data.sql_data()

                drug_name = data.pop("drug", None)
                if drug_name is not None:
                    if drug_name in drugs:
                        drug = drugs.get(drug_name)

                    else:
                        # We need to create a new drug
                        drug = sql.Drug(name=drug_name)
                        session.add(drug)
                        drugs[drug_name] = drug

                db_data = sql.MPSData(**data)
                if drug_name is not None:
                    db_data.drug = drug
                db_data.experiment = experiment
                db_data.cell_line = cell_line

                # Check if data allready is in the table
                query = session.query(sql.MPSData).filter(
                    sql.MPSData.path == path.relative_to(folder_path).as_posix()
                )
                if query.count() > 0:
                    # We might want to update the record later
                    # item = query.first()
                    # item = query.one()  # raise error if more than one
                    # Update
                    continue

                # lst.append(db_data)
                session.add(db_data)

    # session.bulk_save_objects(lst)
    session.commit()


if __name__ == "__main__":
    # main()
    pipeline()
