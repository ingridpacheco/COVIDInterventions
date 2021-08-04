from SPARQLWrapper import SPARQLWrapper, JSON

population_countries = []
start_vaccination_countries = []

types = [
        'case_identification',
        'environmental_measures',
        'healthcare',
        'resource_allocation',
        'returning_to_normal_life',
        'risk_communication',
        'social_distancing',
        'count_travel_restriction'
    ]

def initialize_intervention_dict():
    interventions_values = {}
    for intervention_type in types:
        interventions_values[intervention_type] = {
            'start_date': 0,
            'end_date': 0,
            'end_value': 0,
            'highest_date': 0,
            'highest_value': 0,
        }
    return interventions_values

def get_type(result):
    max_type = ''
    max_value = 0
    min_type = ''
    min_value = 0

    for intervention_type in types:
        if int(result[intervention_type]['value']) > int(max_value):
            max_type = intervention_type
            max_value = result[intervention_type]['value']
        if int(result[intervention_type]['value']) <= int(min_value):
            print(f'Country: {result["s"]["value"]} - Menor tipo: {intervention_type} - Valor: {result[intervention_type]["value"]}')
            min_type = intervention_type
            min_value = result[intervention_type]['value']
    
    print('\n')
    
    return max_type, max_value, min_type, min_value

def analyze_new_cases():

    sparql = SPARQLWrapper("http://192.168.1.81:7200/repositories/COVID_Interventions")
    sparql.setQuery("""
        PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX ex: <https://example.org/>

        SELECT ?s ?new_cases ?number_interventions ?pointInTime WHERE {
            ?s a wikibase:Item ;
                ex:number_interventions ?interventions.
                ?interventions ex:number_of_new_cases ?new_cases;
                            ex:total_interventions ?number_interventions;
                            pq:P585 ?pointInTime.
        }
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    country = results["results"]["bindings"][0]['s']['value']

    data = []

    country_data = {}

    number_interventions = 0
    max_new_cases = 0
    date = 0
    for idx, result in enumerate(results["results"]["bindings"]):
        if idx == len(results["results"]["bindings"]) - 1:
            country_data['country'] = country
            country_data['date'] = date
            country_data['number_interventions'] = number_interventions
            country_data['max_new_cases'] = max_new_cases
            data.append(country_data)
        if result['s']['value'] != country:
            country_data['country'] = country
            country_data['date'] = date
            country_data['number_interventions'] = number_interventions
            country_data['max_new_cases'] = max_new_cases
            data.append(country_data)
            country_data = {}
            country = result['s']['value']
            max_new_cases = 0
            date = 0
            number_interventions = 0
        if float(result['new_cases']['value']) > float(max_new_cases):
            max_new_cases = result['new_cases']['value']
            number_interventions = result['number_interventions']['value']
            date = result['pointInTime']['value']

    sparql.setQuery("""
        PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX p: <http://www.wikidata.org/prop/>
        PREFIX ps: <http://www.wikidata.org/prop/statement/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX wd: <http://www.wikidata.org/entity/>

        SELECT  ?s ?label ?number_vaccines ?number_cases ?vaccine_time ?cases_time WHERE {
        SERVICE <https://query.wikidata.org/sparql>
            {
                { 
                    ?s rdfs:label ?label;
                        p:P9107 ?vaccines;
                        p:P1603 ?cases.
                    ?vaccines ps:P9107 ?number_vaccines;
                            pq:P585 ?vaccine_time.
                    ?cases ps:P1603 ?number_cases;
                            pq:P585 ?cases_time.
                    FILTER(langMatches(lang(?label),"en"))
                    FILTER(?s = """ + f'wd:{data[0]["country"].split("/entity/")[1]}' + """)
                    FILTER(?vaccine_time = """ + f'\"{data[0]["date"]}\"^^xsd:dateTime' + """ && ?cases_time = """ + f'\"{data[0]["date"]}\"^^xsd:dateTime' + """)
                }
                UNION { 
                    ?s rdfs:label ?label;
                        p:P9107 ?vaccines;
                        p:P1603 ?cases.
                    ?vaccines ps:P9107 ?number_vaccines;
                            pq:P585 ?vaccine_time.
                    ?cases ps:P1603 ?number_cases;
                            pq:P585 ?cases_time.
                    FILTER(langMatches(lang(?label),"en"))
                    FILTER(?s = """ + f'wd:{data[1]["country"].split("/entity/")[1]}' + """)
                    FILTER(?vaccine_time = """ + f'\"{data[0]["date"]}\"^^xsd:dateTime' + """ && ?cases_time = """ + f'\"{data[0]["date"]}\"^^xsd:dateTime ' + 
                    """|| ?vaccine_time = """ + f'\"{data[1]["date"]}\"^^xsd:dateTime' + """ && ?cases_time = """ + f'\"{data[1]["date"]}\"^^xsd:dateTime ' + """)
                }
            }
        } ORDER BY DESC(?number_vaccines)
    """)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    for result in results["results"]["bindings"]:
        for idx, cd in enumerate(data):
            if cd['country'] == result["s"]["value"]:
                if data[idx]['date'] != result['cases_time']['value']:
                    data[idx]['number_vaccines_other'] = result['number_vaccines']['value']
                    data[idx]['number_cases_other'] = result['number_cases']['value']
                    data[idx]['date_other'] = result['cases_time']['value']
                else:
                    data[idx]['label'] = result['label']['value']
                    data[idx]['number_vaccines'] = result['number_vaccines']['value']
                    data[idx]['number_cases'] = result['number_cases']['value']

    for idx, cd in enumerate(data):
        sparql.setQuery("""
            PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
            PREFIX wikibase: <http://wikiba.se/ontology#>
            PREFIX p: <http://www.wikidata.org/prop/>
            PREFIX ps: <http://www.wikidata.org/prop/statement/>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            PREFIX wd: <http://www.wikidata.org/entity/>

            SELECT ?s ?numberPopulation WHERE {
            SERVICE <https://query.wikidata.org/sparql>
                {
                    ?s rdfs:label ?label;
                    wdt:P17 ?country;
                    FILTER(?s = """ + f'wd:{cd["country"].split("/entity/")[1]}' + """)
                    FILTER(langMatches(lang(?label),"en"))
                }
            SERVICE <https://query.wikidata.org/sparql>
                {
                    ?country p:P1082 ?population.
                    ?population ps:P1082 ?numberPopulation;
                                pq:P585 ?pointInTime.
                    FILTER(?pointInTime < """ + f'\"{cd["date"]}"^^xsd:dateTime)'+ """
                }
            } ORDER BY DESC(?pointInTime) LIMIT 1
        """)

        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        global population_countries

        for result in results["results"]["bindings"]:
            number_population = result['numberPopulation']['value']
            data[idx]['number_population'] = number_population
            population_countries.append(number_population)
            vaccine_population = 100 * int(cd['number_vaccines']) / int(cd['number_population'])
            cases_population = 100 * int(cd['number_cases']) / int(cd['number_population'])
            data[idx]['vaccine_population'] = vaccine_population
            data[idx]['cases_population'] = cases_population
            if cd.get('date_other') is not None:
                vaccine_population_other = 100 * int(cd['number_vaccines_other']) / int(cd['number_population'])
                cases_population_other = 100 * int(cd['number_cases_other']) / int(cd['number_population'])
                data[idx]['vaccine_population_other'] = vaccine_population_other
                data[idx]['cases_population_other'] = cases_population_other

        for key in cd:
            print(f'{key}: {cd[key]}')
        print('\n')

def analyse_max_interventions():

    sparql = SPARQLWrapper("http://192.168.1.81:7200/repositories/COVID_Interventions")
    sparql.setQuery("""
        PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX ex: <https://example.org/>

        SELECT * WHERE {
            ?s a wikibase:Item ;
                ex:number_interventions ?interventions.
                ?interventions ex:total_interventions ?number_interventions;
                            ex:number_of_new_cases ?new_cases;
                            ex:total_case_identification ?case_identification;
                            ex:total_environmental_measures ?environmental_measures;
                            ex:total_healthcare ?healthcare;
                            ex:total_resource_allocation ?resource_allocation;
                            ex:total_returning_to_normal_life ?returning_to_normal_life;
                            ex:total_risk_communication ?risk_communication;
                            ex:total_social_distancing ?social_distancing;
                            ex:total_count_travel_restriction ?count_travel_restriction;
                            pq:P585 ?pointInTime.
        }
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    data = []

    country_data = {}

    country = results["results"]["bindings"][0]['s']['value']

    total_interventions = 0
    relative_interventions = 0
    new_cases = 0
    date = 0
    max_type = ''
    max_value = 0
    min_type = ''
    min_value = 0
    idx_max_interventions = 0
    for idx,result in enumerate(results["results"]["bindings"]):
        if idx == len(results["results"]["bindings"]) - 1:
            country_data['country'] = country
            country_data['date'] = date
            country_data['number_interventions'] = total_interventions
            country_data['relative_interventions'] = relative_interventions
            country_data['new_cases'] = new_cases
            country_data['idx_max_interventions'] = idx_max_interventions
            data.append(country_data)
        if result['s']['value'] != country:
            country_data['country'] = country
            country_data['date'] = date
            country_data['number_interventions'] = total_interventions
            country_data['relative_interventions'] = relative_interventions
            country_data['new_cases'] = new_cases
            country_data['idx_max_interventions'] = idx_max_interventions
            data.append(country_data)
            country_data = {}
            country = result['s']['value']
            total_interventions = 0
            relative_interventions = 0
            date = 0
            new_cases = 0
        if int(result['number_interventions']['value']) > int(total_interventions):
            total_interventions = result['number_interventions']['value']
            relative_interventions = int(total_interventions) - int(result['returning_to_normal_life']['value'])
            new_cases = result['new_cases']['value']
            date = result['pointInTime']['value']
            idx_max_interventions = idx
    
    for idx,cd in enumerate(data):
        max_type, max_value, min_type, min_value = get_type(results["results"]["bindings"][cd['idx_max_interventions']])
        data[idx]['max_type'] = max_type
        data[idx]['max_value'] = max_value
        data[idx]['min_type'] = min_type
        data[idx]['min_value'] = min_value

    sparql.setQuery("""
        PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX p: <http://www.wikidata.org/prop/>
        PREFIX ps: <http://www.wikidata.org/prop/statement/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX wd: <http://www.wikidata.org/entity/>

        SELECT ?s ?number_cases ?pointInTime WHERE {
            ?s a wikibase:Item ;
        SERVICE <https://query.wikidata.org/sparql>
            {
                ?s rdfs:label ?label;
                    p:P1603 ?cases.
                ?cases ps:P1603 ?number_cases;
                        pq:P585 ?pointInTime.
                FILTER(?s = """ + f'wd:{data[0]["country"].split("/entity/")[1]}' + """ && ?pointInTime = """ + f'\"{data[0]["date"]}\"^^xsd:dateTime ' + 
                    """|| ?s = """ + f'wd:{data[1]["country"].split("/entity/")[1]}' + """ && ?pointInTime = """ + f'\"{data[1]["date"]}\"^^xsd:dateTime ' + """)
                FILTER(langMatches(lang(?label),"en"))
            }
        }
    """)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    for idx,result in enumerate(results["results"]["bindings"]):
        data[idx]['number_cases'] = result['number_cases']['value']
    
    for cd in data:
        for key in cd:
            print(f'{key}: {cd[key]}')
        print('\n')

def analyze_intervention_cases():

    sparql = SPARQLWrapper("http://192.168.1.81:7200/repositories/COVID_Interventions")
    sparql.setQuery("""
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?s WHERE {
            ?s a wikibase:Item .
        }
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    data = []
    country_data = {}

    for result in results["results"]["bindings"]:
        country_data['country'] = result["s"]["value"]
        data.append(country_data)
        country_data = {}

    for idx, cd in enumerate(data):
        sparql = SPARQLWrapper("http://192.168.1.81:7200/repositories/COVID_Interventions")
        sparql.setQuery("""
            PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
            PREFIX wikibase: <http://wikiba.se/ontology#>
            PREFIX ex: <https://example.org/>
            PREFIX p: <http://www.wikidata.org/prop/>
            PREFIX ps: <http://www.wikidata.org/prop/statement/>
            PREFIX wd: <http://www.wikidata.org/entity/>

            SELECT ?s ?number_interventions ?number_cases ?pointInTime WHERE {
                ?s a wikibase:Item ;
                    ex:number_interventions ?interventions.
                    ?interventions ex:total_interventions ?number_interventions;
                                pq:P585 ?pointInTime.
                FILTER(?number_interventions > 0)
                SERVICE <https://query.wikidata.org/sparql>
                {
                    ?s rdfs:label ?label.
                    OPTIONAL {
                        ?s p:P1603 ?cases.
                        ?cases ps:P1603 ?number_cases;
                            pq:P585 ?pointInTime.}
                    FILTER(langMatches(lang(?label),"en"))
                    FILTER(?s = """ + f'wd:{cd["country"].split("/entity/")[1]}' + """)
                }
            } ORDER BY ?pointInTime LIMIT 1
        """)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        start_interventions = 0
        number_cases = 0

        for result in results["results"]["bindings"]:
            data[idx]['start_interventions'] = result['pointInTime']['value']
            if 'number_cases' in result:
                data[idx]['number_cases'] = result['number_cases']['value']

    for idx, cd in enumerate(data):
        sparql = SPARQLWrapper("http://192.168.1.81:7200/repositories/COVID_Interventions")
        sparql.setQuery("""
            PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
            PREFIX wikibase: <http://wikiba.se/ontology#>
            PREFIX ex: <https://example.org/>
            PREFIX p: <http://www.wikidata.org/prop/>
            PREFIX ps: <http://www.wikidata.org/prop/statement/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX wd: <http://www.wikidata.org/entity/>

            SELECT ?number_vaccines ?vaccine_number_cases ?pointInTime WHERE {
                SERVICE <https://query.wikidata.org/sparql>
                { """ + f'wd:{cd["country"].split("/entity/")[1]}' + """ rdfs:label ?label;
                        p:P9107 ?vaccines.
                    ?vaccines ps:P9107 ?number_vaccines;
                                pq:P585 ?pointInTime.
                    OPTIONAL { """ + f'wd:{cd["country"].split("/entity/")[1]}' + """ p:P1603 ?cases.
            			?cases ps:P1603 ?vaccine_number_cases;
                            pq:P585 ?pointInTime. }
                    FILTER(langMatches(lang(?label),"en"))
                }
            } ORDER BY ?pointInTime LIMIT 1
        """)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        global start_vaccination_countries

        for result in results["results"]["bindings"]:
            if 'vaccine_number_cases' in result:
                data[idx]['vaccine_number_cases'] = result['vaccine_number_cases']['value']
            data[idx]['start_vaccination'] = result['pointInTime']['value']
            start_vaccination_countries.append(result['pointInTime']['value'])

    sparql = SPARQLWrapper("http://192.168.1.81:7200/repositories/COVID_Interventions")
    sparql.setQuery("""
        PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX ex: <https://example.org/>
        PREFIX p: <http://www.wikidata.org/prop/>
        PREFIX ps: <http://www.wikidata.org/prop/statement/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX wd: <http://www.wikidata.org/entity/>

        SELECT ?s (AVG(?new_cases) as ?avg_new_cases) (SUM(?new_cases) as ?total_new_cases) (MAX(?new_cases) as ?max_new_cases) WHERE {
            ?s a wikibase:Item ;
                ex:number_interventions ?interventions.
            ?interventions ex:number_of_new_cases ?new_cases;
                pq:P585 ?pointInTime.
                FILTER(?s = """ + f'wd:{data[0]["country"].split("/entity/")[1]}' + """ && ?pointInTime > """ +
                f'\"{data[0]["start_interventions"]}\"^^xsd:dateTime ' + """ && ?pointInTime < """ + f'\"{data[0]["start_vaccination"]}\"^^xsd:dateTime' +
                """ || ?s = """ + f'wd:{data[1]["country"].split("/entity/")[1]}' + """ && ?pointInTime > """ +
                f'\"{data[1]["start_interventions"]}\"^^xsd:dateTime ' + """ && ?pointInTime < """ + f'\"{data[1]["start_vaccination"]}\"^^xsd:dateTime' + """ )
        } GROUP BY ?s
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    avg_new_cases = 0
    max_new_cases = 0
    total_new_cases = 0

    for result in results["results"]["bindings"]:
        for idx,cd in enumerate(data):
            if cd['country'] == result['s']['value']:
                data[idx]['avg_new_cases'] = result['avg_new_cases']['value']
                data[idx]['max_new_cases'] = result['max_new_cases']['value']
                data[idx]['total_new_cases'] = result['total_new_cases']['value']
                data[idx]['avg_per_population'] = 100 * float(result['total_new_cases']['value']) / float(population_countries[idx])

    # Max Date - 07-01-2021 (Brazil)

    for cd in data:
        for key in cd:
            print(f'{key}: {cd[key]}')
        print('\n')

def analyze_vaccination():

    sparql = SPARQLWrapper("http://192.168.1.81:7200/repositories/COVID_Interventions")
    sparql.setQuery("""
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?s WHERE {
            ?s a wikibase:Item .
        }
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    data = []
    country_data = {}

    for result in results["results"]["bindings"]:
        country_data['country'] = result["s"]["value"]
        data.append(country_data)
        country_data = {}

    sparql = SPARQLWrapper("http://192.168.1.81:7200/repositories/COVID_Interventions")

    sparql.setQuery("""PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX ex: <https://example.org/>
        PREFIX p: <http://www.wikidata.org/prop/>
        PREFIX ps: <http://www.wikidata.org/prop/statement/>
        PREFIX wd: <http://www.wikidata.org/entity/>

        SELECT ?s (AVG(?new_cases) as ?avg_new_cases) (SUM(?new_cases) as ?total_new_cases) (max(?new_cases) as ?max_new_cases) WHERE {
            ?s a wikibase:Item ;
                ex:number_interventions ?interventions.
            ?interventions ex:number_of_new_cases ?new_cases;
                            pq:P585 ?pointInTime.
            SERVICE <https://query.wikidata.org/sparql>
            {
                ?s rdfs:label ?label;
                    p:P9107 ?vaccines.
                ?vaccines ps:P9107 ?number_vaccines;
                            pq:P585 ?pointInTime.
                FILTER(langMatches(lang(?label),"en"))
                FILTER(?s = """ + f'wd:{data[0]["country"].split("/entity/")[1]}' + """ && ?pointInTime > """ +
                f'\"{start_vaccination_countries[0]}\"^^xsd:dateTime ' +
                """ || ?s = """ + f'wd:{data[1]["country"].split("/entity/")[1]}' + """ && ?pointInTime > """ +
                f'\"{start_vaccination_countries[1]}\"^^xsd:dateTime )' +
            """}
        } GROUP BY ?s"""
    )
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    avg_new_cases = 0
    max_new_cases = 0
    total_new_cases = 0

    for result in results["results"]["bindings"]:
        for idx,cd in enumerate(data):
            if cd['country'] == result['s']['value']:
                data[idx]['avg_new_cases'] = result['avg_new_cases']['value']
                data[idx]['max_new_cases'] = result['max_new_cases']['value']
                data[idx]['total_new_cases'] = result['total_new_cases']['value']
                data[idx]['avg_per_population'] = 100 * float(result['total_new_cases']['value']) / float(population_countries[idx])

    # Max Date - 23-06-2021 (Brazil)

    for cd in data:
        for key in cd:
            print(f'{key}: {cd[key]}')
        print('\n')

def analyze_intervention():

    sparql = SPARQLWrapper("http://192.168.1.81:7200/repositories/COVID_Interventions")
    sparql.setQuery("""
        PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX ex: <https://example.org/>

        SELECT * WHERE {
            ?s a wikibase:Item ;
                ex:number_interventions ?interventions.
                ?interventions ex:total_interventions ?number_interventions;
                            ex:number_of_new_cases ?new_cases;
                            ex:total_case_identification ?case_identification;
                            ex:total_environmental_measures ?environmental_measures;
                            ex:total_healthcare ?healthcare;
                            ex:total_resource_allocation ?resource_allocation;
                            ex:total_returning_to_normal_life ?returning_to_normal_life;
                            ex:total_risk_communication ?risk_communication;
                            ex:total_social_distancing ?social_distancing;
                            ex:total_count_travel_restriction ?count_travel_restriction;
                            pq:P585 ?pointInTime.
        }
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    country = results["results"]["bindings"][0]['s']['value']

    data = []

    country_data = {}

    interventions = initialize_intervention_dict()

    number_interventions = 0
    max_new_cases = 0
    date = 0
    for idx, result in enumerate(results["results"]["bindings"]):
        if idx == len(results["results"]["bindings"]) - 1:
            country_data['country'] = country
            country_data['interventions'] = interventions
            data.append(country_data)
        if result['s']['value'] != country:
            country_data['country'] = country
            country_data['interventions'] = interventions
            data.append(country_data)
            country_data = {}
            country = result['s']['value']
            interventions = initialize_intervention_dict()
        for intervention_type in types:
            if interventions[intervention_type]['start_date'] == 0 and int(result[intervention_type]['value']) > 0:
                interventions[intervention_type]['start_date'] = result['pointInTime']['value']
            dif_value = int(result[intervention_type]['value']) - int(interventions[intervention_type]['end_value'])
            if dif_value > int(interventions[intervention_type]['highest_value']):
                interventions[intervention_type]['highest_value'] = result[intervention_type]['value']
                interventions[intervention_type]['highest_date'] = result['pointInTime']['value']
            if int(result[intervention_type]['value']) > int(interventions[intervention_type]['end_value']):
                interventions[intervention_type]['end_value'] = result[intervention_type]['value']
                interventions[intervention_type]['end_date'] = result['pointInTime']['value']

    for idx_data, cd in enumerate(data):
        for intervention_type in cd['interventions']:
            if cd['interventions'][intervention_type]['end_date'] != 0:

                sparql = SPARQLWrapper("http://192.168.1.81:7200/repositories/COVID_Interventions")
                sparql.setQuery("""
                    PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
                    PREFIX wikibase: <http://wikiba.se/ontology#>
                    PREFIX ex: <https://example.org/>
                    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                    PREFIX wd: <http://www.wikidata.org/entity/>

                    SELECT (AVG(?new_cases) as ?avg_new_cases) (MAX(?new_cases) as ?max_new_cases) (SUM(?new_cases) as ?sum_cases) (COUNT(?new_cases) as ?count_cases) WHERE { """ +
                        f'wd:{cd["country"].split("/entity/")[1]}' + """ a wikibase:Item ;
                            ex:number_interventions ?interventions.
                            ?interventions ex:total_interventions ?number_interventions;
                                        ex:number_of_new_cases ?new_cases;
                                        pq:P585 ?pointInTime.
                        FILTER(?pointInTime > """ + f'\"{cd["interventions"][intervention_type]["end_date"]}\"^^xsd:dateTime' """)
                    }
                """)
                sparql.setReturnFormat(JSON)
                results = sparql.query().convert()

                for result in results["results"]["bindings"]:
                    if result.get('avg_new_cases') is not None:
                        data[idx_data]['interventions'][intervention_type]['avg_cases_after_end'] = result["avg_new_cases"]["value"]
                    if result.get('max_new_cases') is not None:
                        data[idx_data]['interventions'][intervention_type]['max_cases_after_end'] = result["max_new_cases"]["value"]
                    if result.get('sum_cases') is not None:
                        data[idx_data]['interventions'][intervention_type]['sum_cases_after_end'] = result["sum_cases"]["value"]
                    if result.get('count_cases') is not None:
                        data[idx_data]['interventions'][intervention_type]['count_cases_after_end'] = result["count_cases"]["value"]

                if cd['interventions'][intervention_type]['start_date'] != 0:

                    sparql = SPARQLWrapper("http://192.168.1.81:7200/repositories/COVID_Interventions")
                    sparql.setQuery("""
                        PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
                        PREFIX wikibase: <http://wikiba.se/ontology#>
                        PREFIX ex: <https://example.org/>
                        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                        PREFIX wd: <http://www.wikidata.org/entity/>

                        SELECT (AVG(?new_cases) as ?avg_new_cases) (MAX(?new_cases) as ?max_new_cases) (SUM(?new_cases) as ?sum_cases) (COUNT(?new_cases) as ?count_cases) WHERE { """ +
                            f'wd:{cd["country"].split("/entity/")[1]}' + """ a wikibase:Item ;
                                ex:number_interventions ?interventions.
                                ?interventions ex:total_interventions ?number_interventions;
                                            ex:number_of_new_cases ?new_cases;
                                            pq:P585 ?pointInTime.
                            FILTER(?pointInTime > """ + f'\"{cd["interventions"][intervention_type]["start_date"]}\"^^xsd:dateTime' + """ && ?pointInTime < """ +
                            f'\"{cd["interventions"][intervention_type]["end_date"]}\"^^xsd:dateTime' """)
                        }
                    """)
                    sparql.setReturnFormat(JSON)
                    results = sparql.query().convert()

                    for idx,result in enumerate(results["results"]["bindings"]):
                        if result.get('avg_new_cases') is not None:
                            data[idx_data]['interventions'][intervention_type]['avg_cases_between'] = result["avg_new_cases"]["value"]
                        if result.get('max_new_cases') is not None:
                            data[idx_data]['interventions'][intervention_type]['max_cases_between'] = result["max_new_cases"]["value"]
                        if result.get('sum_cases') is not None:
                            data[idx_data]['interventions'][intervention_type]['sum_cases_between'] = result["sum_cases"]["value"]
                        if result.get('count_cases') is not None:
                            data[idx_data]['interventions'][intervention_type]['count_cases_between'] = result["count_cases"]["value"]

    for cd in data:
        for key in cd:
            print(f'{key}: {cd[key]}')
        print('\n')

if __name__ == "__main__":
    analyze_new_cases()
    analyse_max_interventions()
    analyze_intervention_cases()
    analyze_vaccination()
    analyze_intervention()