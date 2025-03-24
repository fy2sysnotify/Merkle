import mysql.connector
import os

db = mysql.connector.connect(
    host="localhost",
    user=os.getenv('MySQLRootUser'),
    passwd=os.getenv('MySQLRootPassword'),
    database='OdsReportsForGrafana'
)

cursor = db.cursor()

# cursor.execute('TRUNCATE TABLE ZwillingODSUsage')

# cursor.execute("CREATE TABLE IsobarWebODSUsage(recordID int PRIMARY KEY NOT NULL AUTO_INCREMENT, TimeStamp datetime NOT NULL, SandboxID VARCHAR(255) NOT NULL, Realm VARCHAR(20) NOT NULL, Instance VARCHAR(255) NOT NULL, State VARCHAR(20) NOT NULL, CreatedAt VARCHAR(40) NOT NULL, CreatedBy VARCHAR(255) NOT NULL, MinutesUpSinceCreated int NOT NULL, MinutesDownSinceCreated int NOT NULL, TotalCredits VARCHAR(255) NOT NULL, MinutesUpInLast24Hours int NOT NULL, MinutesDownInLast24Hours int NOT NULL, ThisODSCreditsSince01032021 VARCHAR(255) NOT NULL, TotalCreditsInRealmSince01032021 VARCHAR(255) NOT NULL, PersonalNotes VARCHAR(255))")
# cursor.execute('DESCRIBE IsobarWebODSUsage')

# cursor.execute("CREATE TABLE ZwillingODSUsage(recordID int PRIMARY KEY NOT NULL AUTO_INCREMENT, TimeStamp datetime NOT NULL, SandboxID VARCHAR(255) NOT NULL, Realm VARCHAR(20) NOT NULL, Instance VARCHAR(255) NOT NULL, State VARCHAR(20) NOT NULL, CreatedAt VARCHAR(40) NOT NULL, CreatedBy VARCHAR(255) NOT NULL, MinutesUpSinceCreated int NOT NULL, MinutesDownSinceCreated int NOT NULL, TotalCredits VARCHAR(255) NOT NULL, MinutesUpInLast24Hours int NOT NULL, MinutesDownInLast24Hours int NOT NULL, ThisODSCreditsSince01012021 VARCHAR(255) NOT NULL, TotalCreditsInRealmSince01012021 VARCHAR(255) NOT NULL, PersonalNotes VARCHAR(255))")
# cursor.execute('DESCRIBE ZwillingODSUsage')

# cursor.execute("CREATE TABLE MestergronnODSUsage(recordID int PRIMARY KEY NOT NULL AUTO_INCREMENT, TimeStamp datetime NOT NULL, SandboxID VARCHAR(255) NOT NULL, Realm VARCHAR(20) NOT NULL, Instance VARCHAR(255) NOT NULL, State VARCHAR(20) NOT NULL, CreatedAt VARCHAR(40) NOT NULL, CreatedBy VARCHAR(255) NOT NULL, MinutesUpSinceCreated int NOT NULL, MinutesDownSinceCreated int NOT NULL, TotalCredits VARCHAR(255) NOT NULL, MinutesUpInLast24Hours int NOT NULL, MinutesDownInLast24Hours int NOT NULL, ThisODSCreditsSince01012021 VARCHAR(255) NOT NULL, TotalCreditsInRealmSince01012021 VARCHAR(255) NOT NULL, PersonalNotes VARCHAR(255))")
# cursor.execute('DESCRIBE MestergronnODSUsage')
# for i in cursor:
#     print(i)