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

                for claim in item.claims['P9107']:
                        for qual in claim.qualifiers['P585']:
                                time = qual.toJSON()['datavalue']['value']['time'].split('+0000000')[1].split('T')[0]
                                print('time: ', time)
                                if time in dates:
                                        idx = dates.index(time)
                                        quantity = pywikibot.WbQuantity(vaccines[idx])
                                        claim.changeTarget(quantity)
                                        print(f'Mudei - {time} - {vaccines[idx]}')

if __name__ == "__main__":
        arquivo = input('Digite o path file do arquivo que você quer inserir: ')
        insert_vaccination(arquivo)