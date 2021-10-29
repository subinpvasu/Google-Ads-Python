import adwords as GA

"""
Return type is dictionary.
"""


"""
Keyword History data
"""

_DEFAULT_LOCATION_IDS = ["1023191"]
_DEFAULT_LANGUAGE_ID = "1000"
customer_id = '3308294378'
keyword_texts = ['cheap flights', 'fast cargo']
page_url = ''

history = GA.keyword_history_idea(customer_id, _DEFAULT_LOCATION_IDS, _DEFAULT_LANGUAGE_ID, keyword_texts, page_url)

"""
Keyword Forecast Data

"""

customer_id = '6076703147'
keywords = {
    0 : {
        'text' : 'luxury flights ',
        'cpc_bid_micros' : 2000000,
        'match_type' : 'BROAD'
    },
    1 : {
        'text' : 'cheap cargo',
        'cpc_bid_micros' : 1500000,
        'match_type' : 'EXACT'
    }
}
ex_keywords = {
    0 : {
        'text' : 'business class facility',
        'match_type' : 'BROAD'
    }
}
params = {
'keyword_plan_campaign_bid' : 1000000,
'keyword_plan_ad_group_bid' : 2500000,
'keywords': keywords,
'ex_kwd' : ex_keywords
}

#forecast = GA.get_forecast_metrics(customer_id, params)
print(history)
