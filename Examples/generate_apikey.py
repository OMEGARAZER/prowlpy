"""Example to generate an API Key for a Prowl user."""

import prowlpy

# it is recomended to use something like environs to avoid hardcoding keys
providerkey = "0987654321098765432109876543210987654321"
prowl = prowlpy.Prowl(providerkey=providerkey)
token_response = prowl.retrieve_token()
print(token_response["url"])

input("Press enter after following the steps at the link.")

apikey_response = prowl.retrieve_apikey(token=token_response["token"])
print(apikey_response["apikey"])
