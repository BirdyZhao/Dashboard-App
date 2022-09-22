# -*- coding: utf-8 -*-
"""
Created on Thu Sep  1 13:50:58 2022

@author:BO ZHAO
"""
import pandas as pd
import streamlit as st
import altair as alt
from urllib.error import URLError
import pgeocode
import numpy as np
import pydeck as pdk
import knackpy
import datetime
import time 
import plotly.express as px

st.title('Reach Success Dashboard')

@st.cache
def get_data():
    data = knackpy.get(app_id="5fa9ddc2a23bbc001575a2e5", api_key="ee61146f-3fbc-46b8-ac8b-e76433898192", obj="object_1")
 #app.containers
    data = pd.DataFrame(data)
    a = data['field_21_raw']
    for i in range(0,len(a)):
        if a[i] != '':
            a[i] = a[i]['zip']
            
    df = pd.DataFrame({'Client Name':data['field_1'],
                    'Gender':data['field_14'],
                    'Race':data['field_15'],
                    'Date Enrolled':data['field_16'],
                    'Education':data['field_17'],
                    'Address : Zip':a,
                    'Program':data['field_28']})
    return df
    
try:
    df = get_data()
#get multiselects    
    with st.sidebar:
        programs = st.sidebar.multiselect("Please choose at least one programs", set(df['Program']), ["Community","Youth",'Reentry'])
        genders = st.sidebar.multiselect("Please choose at least one genders", set(df['Gender']), ["Female",'Male'])
        races = st.sidebar.multiselect('Please choose at least one races', set(df['Race']),['Mixed Race',
                                                                                            'Black or African American',
                                                                                            'White',
                                                                                            'Hispanic or Latino',
                                                                                            'Native Hawaiian or other Pacific Islander',
                                                                                            'Asian'])
#get selected data frame
    dt = df.loc[df['Gender'].isin(genders),:]
    dt = dt.loc[df['Program'].isin(programs),:]
    dt = dt.loc[df['Race'].isin(races),:]

#get statistics
    gender_stat = pd.crosstab(dt.Program, dt.Gender)
    
    race_stat = pd.crosstab(dt.Program, dt.Race)
    
#title and table

    table1,table2 = st.columns(2)
    with table1:
        st.write("Number of clients",pd.crosstab(dt.Program, dt.Gender,margins=True))
    with table2:
        ct1 = pd.crosstab(df.Program, df.Gender,margins=True)
        ca1 = np.array(ct1)
        crossall = np.array(ct1.loc[:,'All']).reshape(-1,1)
        cp = ca1/crossall
        cp = pd.DataFrame(cp)
        cp.index = ct1.index
        cp.columns = ct1.columns
        
        f = lambda x: '%.2f%%'% (x*100)
        
        cp['Female'] = cp['Female'].apply(f)
        cp['Male'] = cp['Male'].apply(f)
        cp['Other'] = cp['Other'].apply(f)
        cp['All'] = cp['All'].apply(f)
        st.write('Gender Ratio Table',cp)
    gender_stat = gender_stat.T.reset_index()
#get chart
    gender_data = pd.melt(gender_stat, id_vars=["Gender"]).rename(
        columns={"Gender": "Gender", "value": "Number of clients"})
    genderchart = (
            alt.Chart(gender_data)
            .mark_bar().encode(
                alt.X('Gender', type='nominal'),
                alt.Y('Number of clients', type='quantitative'),
                alt.Color('Program', type='nominal'),
                column='Program:N'
                #alt.Column('Program',type='nominal')
            ).properties(width=200,height=200)  
        )
    text = alt.Chart(gender_data).mark_text(dx=-15, dy=3, color='black').encode(
        alt.X('Gender', type='nominal'),
        alt.Y('Number of clients', type='quantitative'),
        text=alt.Text('Number of clients:Q', format='.0f')
)    
    st.altair_chart(genderchart, use_container_width=False)
#races
#tables
    st.write("Number of clients", pd.crosstab(dt.Program, dt.Race,margins=True))
    ct2 = pd.crosstab(df.Program, df.Race ,margins=True)
    ca2 = np.array(ct2)
    crossall2 = np.array(ct2.loc[:,'All']).reshape(-1,1)
    cp2 = ca2/crossall2
    cp2 = pd.DataFrame(cp2)
    cp2.index = ct2.index
    cp2.columns = ct2.columns
    #transfer to percentage
    
    cp2['Mixed Race'] = cp2['Mixed Race'].apply(f)
    cp2['Black or African American'] = cp2['Black or African American'].apply(f)
    cp2['White'] = cp2['White'].apply(f)
    cp2['Hispanic or Latino'] = cp2['Hispanic or Latino'].apply(f)
    cp2['Native Hawaiian or other Pacific Islander'] = cp2['Native Hawaiian or other Pacific Islander'].apply(f)
    cp2['Asian'] = cp2['Asian'].apply(f)
    cp2['All'] = cp2['All'].apply(f)
    
    st.write('Race Ratio Table',cp2)
 #bar plots   
    race_stat = race_stat.T.reset_index()
    race_data = pd.melt(race_stat, id_vars=["Race"]).rename(
        columns={"Race": "Race", "value": "Number of clients"})
    racechart = (
            alt.Chart(race_data)
            .mark_bar().encode(
                alt.X('Race', type='nominal'),
                alt.Y('Number of clients', type='quantitative'),
                alt.Color('Program', type='nominal'),
                column='Program:N'
                #alt.Column('Program',type='nominal')
            ).properties(width=200,height=200)
        )
    st.altair_chart(racechart, use_container_width=False)
    
#checkbox
    if st.checkbox('Show detailed clients'):
        st.dataframe(dt)
        
#pie charts
#data prepare
    ct2 = ct2.T
    ct2 = ct2.drop('All',axis =0)
    ct2 = ct2.reset_index()
# draw pie charts    
    fig1 = px.pie(ct2, values='All', names='Race',title='Races of all programs')
    st.plotly_chart(fig1,use_container_width=True)
    fig2 = px.pie(ct2, values='Community', names='Race',title='Community Clients')
    st.plotly_chart(fig2,use_container_width=True)
    fig3 = px.pie(ct2, values='Reentry', names='Race',title='Reentry Clients')
    st.plotly_chart(fig3,use_container_width=True)
    fig4 = px.pie(ct2, values='Youth', names='Race',title='Youth Clients')
    st.plotly_chart(fig4,use_container_width=True)


#map
#turn zipcode to lat longt
#data prepare
    zip_data = df[pd.notnull(df['Address : Zip'])]
    nomi = pgeocode.Nominatim('us')
    zip_data['lat'] = list(nomi.query_postal_code(list(zip_data['Address : Zip'])).latitude)
    zip_data['lon']= list(nomi.query_postal_code(list(zip_data['Address : Zip'])).longitude)
    zip_data = zip_data[pd.notnull(zip_data['lat'])]
    zip_data = zip_data[pd.notnull(zip_data['lon'])]
    yth_zip = zip_data.loc[zip_data['Program'] == 'Youth']
    com_zip = zip_data.loc[zip_data['Program'] == 'Community']
    rty_zip = zip_data.loc[zip_data['Program'] == 'Reentry']
#map data table with all clients
    
 #map with all clients
    col1, col2= st.columns(2)
    with col1:
        st.write('All Clients Geographical Location')
#draw maps
    #all data map
        st.pydeck_chart(pdk.Deck(
            map_style=None,
            initial_view_state=pdk.ViewState(
                latitude= 41.505493,
                longitude= -81.681290,
                zoom=9,
                pitch=50,
                ),
            layers=[pdk.Layer(
                'HexagonLayer',
                zip_data,
                get_position=["lon","lat"],
                radius=1000,
                elevation_scale=10,
                elevation_range=[0, 300],
                pickable=True,
                extruded=True,
                auto_highlight=True,
                coverage=1
                )
                ]))
        if st.checkbox('Show detailed data',key=1):
            zip_all = zip_data.groupby(['Address : Zip']).count()['Client Name'].reset_index()
            zip_all.rename(columns={'Client Name':'Number of clients'})
            st.dataframe(zip_all)
     #map with Youth clients    
        st.write('Youth Clients Geographical Location')
        st.pydeck_chart(pdk.Deck(
            map_style=None,
            initial_view_state=pdk.ViewState(
                latitude= 41.505493,
                longitude= -81.681290,
                zoom=9,
                pitch=50,
                ),
            layers=[pdk.Layer(
                'HexagonLayer',
                yth_zip,
                get_position=["lon","lat"],
                radius=1000,
                elevation_scale=10,
                elevation_range=[0, 300],
                pickable=True,
                extruded=True,
                auto_highlight=True,
                coverage=1
                )
                ]))
        if st.checkbox('Show detailed data',key=2):
            yth_zip = yth_zip.groupby(['Address : Zip']).count()['Client Name'].reset_index()
            yth_zip.rename(columns={'Client Name':'Number of clients'})
            st.dataframe(yth_zip)
    with col2:
        st.write('Community Clients Geographical Location')
        st.pydeck_chart(pdk.Deck(
            map_style=None,
            initial_view_state=pdk.ViewState(
                latitude= 41.505493,
                longitude= -81.681290,
                zoom=9,
                pitch=50,
                ),
            layers=[pdk.Layer(
                'HexagonLayer',
                com_zip,
                get_position=["lon","lat"],
                radius=1000,
                elevation_scale=10,
                elevation_range=[0, 300],
                pickable=True,
                extruded=True,
                auto_highlight=True,
                coverage=1
                )
                ]))
        if st.checkbox('Show detailed data',key = 3):
            com_zip = com_zip.groupby(['Address : Zip']).count()['Client Name'].reset_index()
            com_zip.rename(columns={'Client Name':'Number of clients'})
            st.dataframe(com_zip)
            
        st.write('Reentry Clients Geographical Location')
        st.pydeck_chart(pdk.Deck(
            map_style=None,
            initial_view_state=pdk.ViewState(
                latitude= 41.505493,
                longitude= -81.681290,
                zoom=9,
                pitch=50,
                ),
            layers=[pdk.Layer(
                'HexagonLayer',
                rty_zip,
                get_position=["lon","lat"],
                radius=1000,
                elevation_scale=10,
                elevation_range=[0, 300],
                pickable=True,
                extruded=True,
                auto_highlight=True,
                coverage=1
                )
                ]))
        if st.checkbox('Show detailed data',key=4):
            rty_zip = rty_zip.groupby(['Address : Zip']).count()['Client Name'].reset_index()
            rty_zip.rename(columns={'Client Name':'Number of clients'})
            st.dataframe(rty_zip)


#time animation registration date
    st.write('Clients growth line')
    st.sidebar.write('Clients growth line (at the page bottom)')
#generate days
    regs_data = pd.DataFrame({'Client Name':df['Client Name'],
                              'Date':pd.to_datetime(df['Date Enrolled'])})
    regs_data['Date'] = regs_data['Date'].dt.date
    d_counts = regs_data.groupby('Date').count().reset_index()
    
    all_days_date = []
    all_days_Regs = []
    d=0
    for j in range((max(regs_data['Date'])-min(regs_data['Date'])).days+1):
        date_record = min(regs_data['Date']) + datetime.timedelta(days = j)
        all_days_date.append(date_record)
        if all_days_date[j] == d_counts['Date'][d]:
            all_days_Regs.append(d_counts['Client Name'][d])
            d = d+1
        else:
            all_days_Regs.append(0)
    all_days_Sum = all_days_Regs     
    for i in range(len(all_days_date)-1):
        all_days_Sum[i+1] = all_days_Sum[i] + all_days_Regs[i+1]
        
    all_days = pd.DataFrame({'Date':all_days_date,
                             'Registered Clients':all_days_Sum})
    all_days['Date'] =all_days['Date'].apply(lambda x:x.strftime('%F'))
    all_days = all_days.set_index('Date')
 #plot animated line chart   
    if st.sidebar.button('Start'):
        progress_bar = st.sidebar.progress(0)
        status_text = st.sidebar.empty()
        last_rows = all_days[0:(len(all_days_Regs)%20)]
        chart = st.line_chart(data = last_rows)

        for i in range(1, 101):
            new_rows = all_days[((len(all_days_Regs)%20)+20*(i-1)):((len(all_days_Regs)%20)+20*i)]
            status_text.text("%i%% Complete" % i)
            chart.add_rows(new_rows)
            progress_bar.progress(i)
            last_rows = new_rows
            time.sleep(0.08)
        progress_bar.empty()
        st.sidebar.button("Re-run")
    
# Streamlit widgets automatically run the script from top to bottom. Since
# this button is not connected to any other logic, it just causes a plain
# rerun.
    


except URLError as e:
    st.error(
        """
        **This demo requires internet access.**
        Connection error: %s
    """
        % e.reason
    )
    
