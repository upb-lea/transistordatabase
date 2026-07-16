import transistordatabase as tdb

db = tdb.DatabaseManager()
db.set_operation_mode_json("F:/tdb_data")
db.update_from_fileexchange(overwrite=True)
