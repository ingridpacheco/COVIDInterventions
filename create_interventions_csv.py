import pandas as pd
from datetime import datetime
from datetime import timedelta

count_case_identification = 0
count_environmental_measures = 0
count_healthcare = 0
count_resource_allocation = 0
count_returning_to_normal_life = 0
count_risk_communication = 0
count_social_distancing = 0
count_travel_restriction = 0

f = open("COVID_interventions_vaccination_data2.ttl", "w")

country_instances = {
    'Brazil': 'wd:Q86597695',
    'United Kingdom': 'wd:Q84167106',
}

def initialize_variables():
    global count_case_identification, count_environmental_measures, count_healthcare, count_resource_allocation, count_returning_to_normal_life, count_risk_communication, count_social_distancing, count_travel_restriction
    count_case_identification = 0
    count_environmental_measures = 0
    count_healthcare = 0
    count_resource_allocation = 0
    count_returning_to_normal_life = 0
    count_risk_communication = 0
    count_social_distancing = 0
    count_travel_restriction = 0

def initialize_rdf():
    f.write("@prefix wd: <http://www.wikidata.org/entity/> .\n")
    f.write("@prefix ex: <https://example.org/> .\n")
    f.write("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n")
    f.write("@prefix pq: <http://www.wikidata.org/prop/qualifier/> .\n")
    f.write("@prefix wikibase: <http://wikiba.se/ontology#> .\n")

def insert_rdf_line(current_day, count_interventions, count_new_cases, country):
    country_parser = country.replace(' ', '_')
    date_hour = str(current_day).split(' ')
    date_hour = date_hour[0] + "T" + date_hour[1] + "Z"
    f.write(f"{country_instances[country]} ex:number_interventions ex:{country_parser}_interventions_{date_hour} .\n")
    f.write(f"ex:{country_parser}_interventions_{date_hour} ex:number_of_new_cases \"{count_new_cases}\"^^xsd:decimal ;\n")
    f.write(f"ex:total_interventions \"{count_interventions}\"^^xsd:decimal ;\n")
    f.write(f"ex:total_case_identification \"{count_case_identification}\"^^xsd:decimal ;\n")
    f.write(f"ex:total_environmental_measures \"{count_environmental_measures}\"^^xsd:decimal ;\n")
    f.write(f"ex:total_healthcare \"{count_healthcare}\"^^xsd:decimal ;\n")
    f.write(f"ex:total_resource_allocation \"{count_resource_allocation}\"^^xsd:decimal ;\n")
    f.write(f"ex:total_returning_to_normal_life \"{count_returning_to_normal_life}\"^^xsd:decimal ;\n")
    f.write(f"ex:total_risk_communication \"{count_risk_communication}\"^^xsd:decimal ;\n")
    f.write(f"ex:total_social_distancing \"{count_social_distancing}\"^^xsd:decimal ;\n")
    f.write(f"ex:total_count_travel_restriction \"{count_travel_restriction}\"^^xsd:decimal ;\n")
    f.write(f"pq:P585 \"{date_hour}\"^^xsd:dateTime . \n")

def add_intervention(intervention_type):
    if intervention_type == "Travel restriction":
        global count_travel_restriction
        count_travel_restriction += 1
    elif intervention_type == "Social distancing":
        global count_social_distancing
        count_social_distancing += 1
    elif intervention_type == "Risk communication":
        global count_risk_communication
        count_risk_communication += 1
    elif intervention_type == "Returning to normal life":
        global count_returning_to_normal_life
        count_returning_to_normal_life += 1
    elif intervention_type == "Resource allocation":
        global count_resource_allocation
        count_resource_allocation += 1
    elif intervention_type == "Healthcare and public health capacity":
        global count_healthcare
        count_healthcare += 1
    elif intervention_type == "Environmental measures":
        global count_environmental_measures
        count_environmental_measures += 1
    elif intervention_type == "Case identification, contact tracing and related measures":
        global count_case_identification
        count_case_identification += 1

def create_interventions_csv(intervention_file, covid_file):
        initialize_rdf()

        with pd.ExcelFile(intervention_file) as intervention_list:
                df1 = pd.read_excel(intervention_list, 0)
                country = df1.get('Country').tolist()
                dates = df1.get('Date').tolist()
                intervention_type = df1.get('Measure_L1').tolist()

                with pd.ExcelFile(covid_file) as covid_data:
                    df2 = pd.read_excel(covid_data, 0)
                    covid_country = df2.get('location').tolist()
                    covid_date = df2.get('date').tolist()
                    new_cases = df2.get('new_cases').tolist()

                    first_day = min(dates[0], covid_date[0])
                    end_day = max(dates[len(dates) - 1], covid_date[len(covid_date) - 1])
                    first_day = pd.to_datetime(first_day, format='%Y-%m-%d')
                    end_day = pd.to_datetime(end_day, format='%Y-%m-%d')
                    range_dates = list(pd.date_range(first_day,end_day,freq='d'))

                    for current_country in ['Brazil', 'United Kingdom']:
                        initialize_variables()
                        count_interventions = 0
                        count_new_cases = 0
                        count_people_vaccinated = 0
                        f.write(f'{country_instances[current_country]} a wikibase:Item .\n')
                        for date in range_dates:
                            current_day = date.strftime("%Y-%m-%d")
                            if current_day in dates and country[dates.index(current_day)] == current_country:
                                while current_day in dates and country[dates.index(current_day)] == current_country:
                                    current_intervention_type = intervention_type[0]
                                    add_intervention(current_intervention_type)
                                    dates.remove(current_day)
                                    country.remove(current_country)
                                    intervention_type.remove(current_intervention_type)
                                    count_interventions += 1
                            if current_day in covid_date and covid_country[covid_date.index(current_day)] == current_country:
                                count_new_cases = new_cases[0]
                                covid_date.remove(current_day)
                                covid_country.remove(current_country)
                                new_cases.remove(count_new_cases)
                            insert_rdf_line(date, count_interventions, count_new_cases, current_country)
                            print(f"{current_country} - {date} added")
        
        f.close()

if __name__ == "__main__":
        intervention_file = input('Digite o path file do arquivo de intervenções que você quer inserir: ')
        covid_file = input('Digite o path file do arquivo de covid que você quer inserir: ')

        create_interventions_csv(intervention_file, covid_file)