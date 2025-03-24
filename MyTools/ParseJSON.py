import json

data = '''
{
  "name" : "Пешо",
  "phone" : {
    "type" : "intl",
    "number" : "+359 888 888 888"
    },
    "email" : {
      "hide" : "yes"
    }
}'''

info = json.loads(data)
print('Name:', info["name"])
print('Hide:', info["email"]["hide"])
print('Number:', info["phone"]["number"])