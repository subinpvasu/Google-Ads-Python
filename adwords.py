import sys
import uuid

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

_DEFAULT_PAGE_SIZE = 1000



client = GoogleAdsClient.load_from_storage('G:\Python\googleads-live\google-ads-python\google-ads.yaml')

#Common functions

def get_match_type(type):
    return {
        'BROAD' : client.enums.KeywordMatchTypeEnum.BROAD,
        'EXACT' : client.enums.KeywordMatchTypeEnum.EXACT,
        'PHRASE' : client.enums.KeywordMatchTypeEnum.PHRASE
    }[type]


#Keyword Historic Data
def keyword_history_idea(customer_id, location_ids, language_id, keyword_texts, page_url):

    keyword_plan_idea_service = client.get_service("KeywordPlanIdeaService")
    keyword_competition_level_enum = (
        client.enums.KeywordPlanCompetitionLevelEnum
    )
    keyword_plan_network = (
        client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH_AND_PARTNERS
    )
    location_rns = _map_locations_ids_to_resource_names(client, location_ids)
    language_rn = client.get_service(
        "LanguageConstantService"
    ).language_constant_path(language_id)

    if not (keyword_texts or page_url):
        raise ValueError(
            "At least one of keywords or page URL is required, "
            "but neither was specified."
        )

    request = client.get_type("GenerateKeywordIdeasRequest")
    request.customer_id = customer_id
    request.language = language_rn
    request.geo_target_constants = location_rns
    request.include_adult_keywords = False
    request.keyword_plan_network = keyword_plan_network

    if not keyword_texts and page_url:
        request.url_seed.url = page_url

    if keyword_texts and not page_url:
        request.keyword_seed.keywords.extend(keyword_texts)

    if keyword_texts and page_url:
        request.keyword_and_url_seed.url = page_url
        request.keyword_and_url_seed.keywords.extend(keyword_texts)
    try:
        keyword_ideas = keyword_plan_idea_service.generate_keyword_ideas(
            request=request
        )
    except GoogleAdsException as ex:
        print(
            f'Request with ID "{ex.request_id}" failed with status '
            f'"{ex.error.code().name}" and includes the following errors:'
        )
        for error in ex.failure.errors:
            print(f'\tError with message "{error.message}".')
            if error.location:
                for field_path_element in error.location.field_path_elements:
                    print(f"\t\tOn field: {field_path_element.field_name}")

    result = {}
    i = 0
    for idea in keyword_ideas:
        result[idea.text] = {
        'avg_monthly_searches' : idea.keyword_idea_metrics.avg_monthly_searches,
        'competition' : idea.keyword_idea_metrics.competition,
        'competition_index' : idea.keyword_idea_metrics.competition_index,
        'low_top_of_page_bid_micros' : idea.keyword_idea_metrics.low_top_of_page_bid_micros,
        'high_top_of_page_bid_micros' : idea.keyword_idea_metrics.high_top_of_page_bid_micros,
        'monthly_search_volumes' : idea.keyword_idea_metrics.monthly_search_volumes
        }

    return result


def map_keywords_to_string_values(client, keyword_texts):
    keyword_protos = []
    for keyword in keyword_texts:
        string_val = client.get_type("StringValue")
        string_val.value = keyword
        keyword_protos.append(string_val)
    return keyword_protos


def _map_locations_ids_to_resource_names(client, location_ids):
    build_resource_name = client.get_service(
        "GeoTargetConstantService"
    ).geo_target_constant_path
    return [build_resource_name(location_id) for location_id in location_ids]



"""
Keywords Forecast Data
"""

def add_keyword_plan(customer_id, params):
    keyword_plan = _create_keyword_plan(client, customer_id)
    keyword_plan_campaign = _create_keyword_plan_campaign(client, customer_id, keyword_plan, params)
    keyword_plan_ad_group = _create_keyword_plan_ad_group(client, customer_id, keyword_plan_campaign, params)
    _create_keyword_plan_ad_group_keywords(client, customer_id, keyword_plan_ad_group, params)
    _create_keyword_plan_negative_campaign_keywords(client, customer_id, keyword_plan_campaign, params)
    return keyword_plan

def _create_keyword_plan(client, customer_id):
    keyword_plan_service = client.get_service("KeywordPlanService")
    operation = client.get_type("KeywordPlanOperation")
    keyword_plan = operation.create

    keyword_plan.name = f"Keyword plan for traffic estimate {uuid.uuid4()}"

    forecast_interval = (
        client.enums.KeywordPlanForecastIntervalEnum.NEXT_QUARTER
    )
    keyword_plan.forecast_period.date_interval = forecast_interval

    response = keyword_plan_service.mutate_keyword_plans(
        customer_id=customer_id, operations=[operation]
    )
    resource_name = response.results[0].resource_name
    return resource_name


def _create_keyword_plan_campaign(client, customer_id, keyword_plan, params):
    keyword_plan_campaign_service = client.get_service(
        "KeywordPlanCampaignService"
    )
    operation = client.get_type("KeywordPlanCampaignOperation")
    keyword_plan_campaign = operation.create

    keyword_plan_campaign.name = f"Keyword plan campaign {uuid.uuid4()}"
    keyword_plan_campaign.cpc_bid_micros = params['keyword_plan_campaign_bid']
    keyword_plan_campaign.keyword_plan = keyword_plan

    network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
    keyword_plan_campaign.keyword_plan_network = network

    geo_target = client.get_type("KeywordPlanGeoTarget")
    geo_target.geo_target_constant = "geoTargetConstants/2840"
    keyword_plan_campaign.geo_targets.append(geo_target)

    language = "languageConstants/1000"
    keyword_plan_campaign.language_constants.append(language)

    response = keyword_plan_campaign_service.mutate_keyword_plan_campaigns(
        customer_id=customer_id, operations=[operation]
    )
    resource_name = response.results[0].resource_name
    return resource_name


def _create_keyword_plan_ad_group(client, customer_id, keyword_plan_campaign, params):
    operation = client.get_type("KeywordPlanAdGroupOperation")
    keyword_plan_ad_group = operation.create

    keyword_plan_ad_group.name = f"Keyword plan ad group {uuid.uuid4()}"
    keyword_plan_ad_group.cpc_bid_micros = params['keyword_plan_ad_group_bid']
    keyword_plan_ad_group.keyword_plan_campaign = keyword_plan_campaign

    keyword_plan_ad_group_service = client.get_service(
        "KeywordPlanAdGroupService"
    )
    response = keyword_plan_ad_group_service.mutate_keyword_plan_ad_groups(
        customer_id=customer_id, operations=[operation]
    )

    resource_name = response.results[0].resource_name

    return resource_name


def _create_keyword_plan_ad_group_keywords(client, customer_id, plan_ad_group, params):
    keyword_plan_ad_group_keyword_service = client.get_service("KeywordPlanAdGroupKeywordService")
    keyword_plan_service = client.get_service("KeywordPlanService")
    operations = []

    for i,kwd in params['keywords'].items():
        operation = client.get_type("KeywordPlanAdGroupKeywordOperation")
        keyword_plan_ad_group_keyword = operation.create
        keyword_plan_ad_group_keyword.text = kwd['text']
        keyword_plan_ad_group_keyword.cpc_bid_micros = kwd['cpc_bid_micros']
        keyword_plan_ad_group_keyword.match_type = (get_match_type(kwd['match_type']))
        keyword_plan_ad_group_keyword.keyword_plan_ad_group = plan_ad_group
        operations.append(operation)

    response = keyword_plan_ad_group_keyword_service.mutate_keyword_plan_ad_group_keywords(
        customer_id=customer_id, operations=operations
    )


def _create_keyword_plan_negative_campaign_keywords(client, customer_id, plan_campaign, params):
    keyword_plan_negative_keyword_service = client.get_service("KeywordPlanCampaignKeywordService")
    operation = client.get_type("KeywordPlanCampaignKeywordOperation")

    for i, kwd in params['ex_kwd'].items():
        keyword_plan_campaign_keyword = operation.create
        keyword_plan_campaign_keyword.text = kwd['text']
        keyword_plan_campaign_keyword.match_type = (get_match_type(kwd['match_type']))
        keyword_plan_campaign_keyword.keyword_plan_campaign = plan_campaign
        keyword_plan_campaign_keyword.negative = True

    response = keyword_plan_negative_keyword_service.mutate_keyword_plan_campaign_keywords(
        customer_id=customer_id, operations=[operation]
    )

def keyword_forecast(customer_id, plan):
    keyword_plan_service = client.get_service("KeywordPlanService")
    response = keyword_plan_service.generate_forecast_metrics(keyword_plan=plan)

    result = {}

    for i, forecast in enumerate(response.keyword_forecasts):
        res = forecast.keyword_plan_ad_group_keyword.split("/")
        id = res[-1]
        metrics = forecast.keyword_forecast
        click_val = metrics.clicks
        imp_val = metrics.impressions
        cpc_val = metrics.average_cpc
        clicks = f"{click_val:.2f}" if click_val else "0"
        impressions = f"{imp_val:.2f}" if imp_val else "0"
        cpc = f"{cpc_val:.2f}" if cpc_val else "0"
        result[get_keyword_text(customer_id, id)] = {
        'clicks' : clicks,
        'impressions' : impressions,
        'cpc' : cpc
        }
    return result


def get_keyword_text(customer_id, keyid):
    ga_service = client.get_service("GoogleAdsService")
    result = ''
    query = """
        SELECT keyword_plan_ad_group_keyword.text, keyword_plan_ad_group_keyword.match_type, keyword_plan_ad_group_keyword.id, keyword_plan.forecast_period FROM keyword_plan_ad_group_keyword
        """
    query += f" WHERE keyword_plan_ad_group_keyword.id = {keyid}"

    search_request = client.get_type("SearchGoogleAdsRequest")
    search_request.customer_id = customer_id
    search_request.query = query
    search_request.page_size = _DEFAULT_PAGE_SIZE

    results = ga_service.search(request=search_request)

    for row in results:
        result = row.keyword_plan_ad_group_keyword.text

    return result

def get_forecast_metrics(customer_id, params):
    plan = add_keyword_plan(customer_id, params)
    cast = keyword_forecast(customer_id, plan)
    return cast
