'''Interface for creating and using a reloadable database'''

import datetime
import os
import pickle
from contextlib import contextmanager

class NoDatabaseError(RuntimeError):
    '''Error used when an operation can't be done because there is no database loaded'''
    pass # pylint: disable = unnecessary-pass

# UPGRADE: make a verbosity setting so that it doesn't always print

class DatabaseInterface:
    '''Interface for interacting with a database'''
    def __init__(self, save_folder="database", database_creator=lambda: {}, most_recent_save_file="_most_recent_save.txt"):
        # folder where the database saves will be stored
        self.save_folder = save_folder
        if not os.path.isdir(save_folder):
            os.mkdir(save_folder)
            print(f"Save folder not found! A save folder named '{save_folder}' was created instead.")
        # fucntion that returns an empty database
        self.database_creator = database_creator
        # the name of the file that is used to store information about which database to load
        self.most_recent_save_file = most_recent_save_file
        self.exact_most_recent_save_file = os.path.join(self.save_folder, self.most_recent_save_file)
        self._database = None

    @contextmanager
    def load_then_save(self):
        '''Load and then save the database after exiting from the context'''
        try:
            self.load()
            yield self._database
        except Exception:
            raise
        finally:
            self.save()

    @contextmanager
    def expose_or_load_then_save(self):
        '''Exposes or loads then saves upon exiting the context manager'''
        database_exists = True
        try:
            try:
                self.expose_or_load()
            except NoDatabaseError:
                database_exists = False
                raise
            yield self._database
        finally:
            if database_exists:
                self.save()

    def load(self):
        '''Loads the database in from the file'''
        database_file = None
        try:
            with open(self.exact_most_recent_save_file, "r") as open_exact_most_recent_save_file:
                database_file = open_exact_most_recent_save_file.readline().strip()
                if not database_file:
                    raise FileNotFoundError("No file was found in the most recent save file")
                try:
                    database_file = database_file
                    with open(database_file, "rb") as open_database_file:
                        self._database = pickle.load(open_database_file)
                        print("Loaded database from {}".format(database_file))
                except FileNotFoundError:
                    raise RuntimeError("Most recent save file {} could not be found".format(repr(database_file)))
        except FileNotFoundError:
            # the most recent save file was not found, or there was no file listed inside that file
            # so, we make an empty database
            print("Database not loaded - blank database created")
            self._database = self.database_creator()

        return self._database

    def expose(self):
        '''
        If there is database already loaded, expose it
        This is useful if you don't want to accidentally overwrite unsaved information by loading.
        '''
        if self._database is None:
            raise NoDatabaseError
        else:
            return self._database

    def expose_or_load(self):
        '''Expose the database if it's there, otherwise load it up'''
        try:
            return self.expose()
        except NoDatabaseError:
            return self.load()

    def save(self, database=None):
        '''
        Save the loaded database or the given database.
        If a database is given, it will become the loaded database and overwrite it.
        '''
        if database is not None:
            self._database = database

        if self._database is None:
            raise NoDatabaseError

        try:
            formatted_date_and_time = datetime.datetime.now().strftime("%H_%M_%S_%b_%d_%Y")
        except Exception: # pylint: disable = broad-except
            print("Failed to obtain formatted date and time!")
            formatted_date_and_time = "UnknownTime"

        save_file = os.path.normpath(os.path.join(self.save_folder, "db_sv_" + formatted_date_and_time + ".pkl"))
        with open(save_file, "wb+") as open_save_file:
            # save the data to a file
            pickle.dump(self._database, open_save_file)

        with open(self.exact_most_recent_save_file, "w") as open_exact_most_recent_save_file:
            # save the name of the file where the data was stored
            open_exact_most_recent_save_file.write(save_file)

        print("Database saved at: {}".format(save_file))


if __name__ == "__main__":
    # pylint: disable = invalid-name
    database_interface = DatabaseInterface(save_folder="testing_database_interface")
    db = database_interface.load()
    print(db)
    db["wow"] = "haha"
    print(db)
    database_interface.save(db)

    with database_interface.load_then_save() as db:
        # do whatever you want with the database
        print(db)
        db["hi"] = "yay"
