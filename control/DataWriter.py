import csv
import os


class DataWriter():

    def __init__(self, aFile, aDescriptionList):
        if self.__fileExists(aFile):
            self.__file = open(aFile, 'a')
            self.__CSVWriter = csv.writer(self.__file)
        else:
            self.__file = open(aFile, 'a')
            self.__CSVWriter = csv.writer(self.__file)
            self.__CSVWriter.writerow(aDescriptionList)
            self.__flushFileToDisk()

    def writeData(self, aDataList):
        self.__CSVWriter.writerow(aDataList)
        self.__flushFileToDisk()

    def __flushFileToDisk(self):
        self.__file.flush()
        os.fsync(self.__file.fileno())

    def __fileExists(self, aFile):
        return os.path.exists(aFile)
