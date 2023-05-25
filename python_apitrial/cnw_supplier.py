import json
import requests
import pandas as pd



df = pd.read_csv('/data/anna.csv', delimiter=';')

mylist = df.values.tolist()

appSession = requests.Session()



url = "https://192.168.250.36:50000/b1s/v1/Login"



payload = { "CompanyDB" :"JKUSOLOTEST" ,
			"UserName" : "manager" ,
			"Password" : "12345"
			}

response = appSession.post(url, json=payload,verify=False)

print(response.text)

url = "https://192.168.250.36:50000/b1s/v1/BusinessPartners"
payload = {
			"ItemCode": "i002",
			"ItemName": "Item1",
			"ItemType": "itItems"
			}

response = appSession.post(url,json=payload,verify=False)

print(response.text)




url = "https://192.168.250.36:50000/b1s/v1/Logout"


response = appSession.post(url,verify=False)




ihttp  = "https://localhost:50000/b1s/v1/BusinessPartners"

payload = {
                "CardCode": "c001",
                "CardName": "c001",
                "CardType": "C"
            }

data =  requests.get(ihttp)

print(data)
