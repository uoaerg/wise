import csv
import os


trueCount = 0
falseCount = 0
with open('./logs/motiondata.csv', 'rb') as f:
    reader = csv.reader(f)
    for row  in reader:
    	#print (row[1],row[7])
    	if row[7] == "True":
    		trueCount+=1
    	elif row[7] == "False":
    		falseCount+=1
    	else:
    		pass
print("False=:  ",falseCount)
print("TRUE=:  ", trueCount) 
    	
