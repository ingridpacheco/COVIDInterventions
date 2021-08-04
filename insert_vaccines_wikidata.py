import pywikibot
import pandas as pd
import math

# Atualizar os dados 

def insert_vaccination(arquivo):
        site = pywikibot.Site("wikidata", "wikidata")
        repo = site.data_repository()
        item = pywikibot.ItemPage(repo, u"Q84167106")
        item.get()

        # https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv
        with pd.ExcelFile(arquivo) as firstxls:
                df1 = pd.read_excel(firstxls, 0)
                vaccines = df1.get('people_vaccinated').tolist()
                dates = df1.get('date').tolist()
                for idx, vaccine_number in enumerate(vaccines):
                        if not math.isnan(vaccine_number):
                                print(f'Vaccine: {int(vaccine_number)} - Date: {dates[idx]}')
                                
                                number_vaccines = pywikibot.Claim(repo, u'P9107')
                                quantity = pywikibot.WbQuantity(int(vaccine_number))
                                number_vaccines.setTarget(quantity)
                                item.addClaim(number_vaccines, summary=u'Adding number of vaccines')

                                current_date = dates[idx]
                                date_value = current_date.split('-')
                                
                                qualifier = pywikibot.Claim(repo, u'P585')
                                date = pywikibot.WbTime(year=int(date_value[0]), month=int(date_value[1]), day=int(date_value[2]))
                                qualifier.setTarget(date)
                                number_vaccines.addQualifier(qualifier, summary=u'Adding the time')

                                statedin = pywikibot.Claim(repo, u'P854')
                                statedin.setTarget(u"https://ourworldindata.org/covid-vaccinations")

                                number_vaccines.addSources([statedin], summary=u'Adding source')
                                print(f'Vaccine {idx} added')
        print(item)

if __name__ == "__main__":
        arquivo = input('Digite o path file do arquivo que você quer inserir: ')
        insert_vaccination(arquivo)