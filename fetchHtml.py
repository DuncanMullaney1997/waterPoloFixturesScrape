from bs4 import BeautifulSoup
import html
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from functools import cache
from ics import Calendar, Event
from datetime import datetime, timedelta

ts=str(datetime.fromtimestamp(datetime.timestamp(datetime.now())))[:16].replace(' ','_').replace(':','-')

OUTPUT_ICS = "DWPC_Fixtures_26-27_"+ts+".ics"
OUTPUT_PDF = "DWPC_Fixtures_26-27_"+ts+".pdf"
HTML_ORGNL = "view-source_https___irelandwaterpolo.ie_fixtures_#.html"
FOCUS_TEAM = 'Drogheda WPC'

def create_fixtures():
    
    # if original html/decoded file does not exist, create it:
    if not os.path.isfile('decoded.html'):

        with open(HTML_ORGNL, encoding="utf-8") as f:
            source = f.read()

        decoded = html.unescape(source)

        with open("decoded.html","w",encoding="utf-8") as f:
            f.write(decoded)

    with open('decoded.html',encoding='utf-8') as g:
        soup = BeautifulSoup(g,"html.parser")

    fixtures = []

    current_fixture = {}

    wanted_attrs = {
        "data-date",
        "data-time",
        "data-hometeam",
        "data-awayteam",
        "data-venue",
        "data-compname",
        "data-referee",
        "data-comment",
    }

    for attr in soup.find_all("span", class_="html-attribute-name"):

        attr_name = attr.get_text(strip=True)

        if attr_name not in wanted_attrs:
            continue

        value_span = attr.find_next(
            "span",
            class_="html-attribute-value"
        )

        if not value_span:
            continue

        value = value_span.get_text(strip=True)

        # start a new fixture when a new date is provided
        if attr_name == "data-date" and current_fixture:

            fixtures.append(current_fixture)
            current_fixture = {}

        current_fixture[attr_name] = value

    # append final fixture
    if current_fixture:
        fixtures.append(current_fixture)

    df = pd.DataFrame(fixtures)
    pd.set_option('display.max_columns',None)

    # filter to only Drogheda's games
    filter_ = (df['data-hometeam']==FOCUS_TEAM) | (df['data-awayteam']==FOCUS_TEAM)
    df = df.loc[filter_]

    # create a column called "versus" for the opposition team (to replace both home and away columns, aiding;
    #    clarity, 
    # printing 
    # and noise reduction)

    def filter__(row):
        if row['data-hometeam']==FOCUS_TEAM: 
            return row['data-awayteam']
        return row['data-hometeam']

    df['versus'] = df.apply(filter__, axis=1)

    # delete home team, away team and comment columns
    df = df.drop(['data-hometeam','data-awayteam','data-comment','data-referee'], axis=1)

    # create row number column
    # df['GAME NUMBER'] = np.arange(len(df))+1
    df['GAME NUMBER'] = df.reset_index().index+1

    # re-order
    df = df.iloc[:,[5,0,1,4,2,3]]

    # rename columns
    df=df.rename(
        columns={
            # "#":'GAME NUMBER'
            "data-date":'DATE'
            ,"data-time":'TIME'
            ,'versus':'VS'
            ,"data-venue":'VENUE'
            ,"data-compname":'COMPETITION'
            # ,"data-referee":'REFEREE'
            # ,"data-comment":'COMMENT'
            })

    # add Leinster Fixtures to this dataframe
    

    return df




def create_pdf(fixtures):

    """takes a pandas dataframe argument and creates a pdf file from it 
    (useful for validation purposes and as an intended alternative output)"""

    fig, ax = plt.subplots(figsize=(20,10))
    # fig.text(.5,.5, '_',fontsize=10)
    # ax.axis('tight')
    ax.set_title(f'Fixtures for {FOCUS_TEAM}')
    ax.axis('off')
    the_table = ax.table(cellText=fixtures.values,colLabels=fixtures.columns,loc='center')

    pp = PdfPages(OUTPUT_PDF)
    pp.savefig(
            fig
            , bbox_inches='tight'
               )
    pp.close()
    print()




def create_calendar(fixtures):

    """takes a dataframe called fixtures and generates an ics file"""

    cal = Calendar()

    for _ , fixture in fixtures.iterrows():

        kickoff = datetime.strptime(
            f"{fixture['DATE']} {fixture['TIME']}",
            "%d %b %Y %H:%M"
        )

        event = Event()
        event.name = f"{fixture['COMPETITION']} - {fixture['VS']}"
        event.begin = kickoff

        # Assume 1-hour match duration
        event.end = kickoff + timedelta(hours=1)

        event.location = fixture["VENUE"]

        # event.description = (
        #     f"Competition: {fixture['COMPETITION']}\n"
            # f"Home: {FOCUS_TEAM}\n"
            # f"Away: {fixture['data-awayteam']}\n"
            # f"Venue: {fixture['data-venue']}"
        # )

        cal.events.add(event)

    return cal





# @cache
def main():

    fixtures = create_fixtures()

    create_pdf(fixtures)

    print(f"\nPDF file created: {OUTPUT_PDF}")

    # quit()

    calendar = create_calendar(fixtures)

    with open(OUTPUT_ICS, "w", encoding="utf-8") as f:
        f.writelines(calendar)

    print(f"\nICS file created: {OUTPUT_ICS}")

if __name__ == '__main__':
    print(main())



# create Calendar object instant
# for each row in sheet
#     create Event
#     add date, time, vs, venue, comp
#     cal.events.add(event)
#     next loop

# return calendar