# Import python packages
from snowflake.snowpark import Session
import pandas as pd
import requests
import snowflake.connector
from urllib.error import URLError
import streamlit as st
from snowflake.snowpark.context import get_active_session
from datetime import date, timedelta,datetime
from streamlit_option_menu import option_menu
import numpy as np


st.set_page_config(
    page_title="Saama's Global Hackthon",
    page_icon=":wave:",
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:
    selected=option_menu(
        menu_title="Main Menu",
        options=["Home","Data Browser","About Us"],
        icons=["house","database-add","person-lines-fill"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "icon": {"color": "black", "font-size": "18px"}, 
            "nav-link": {"font-size": "18px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#1E96DE"},}
    )

def create_session():
    return Session.builder.configs(st.secrets["snowflake"]).create()
session = create_session()

col1, col2,col3 = st.columns((3))

with col1:
    st.image('saama_logo.jpg',width = 150)

with col2:
    st.header("Saama Thunder's")

with col3:
    st.header("Hackathon 2024")

#show blue line
st.markdown("""<hr style="height:2px;border:none;color:#1E96DE;background-color:#1E96DE;" /> """, unsafe_allow_html=True)

if selected == 'Home':
    # Write directly to the app
    st.title("Simple Data Management Application using Snowflake, Streamlit, SnowPark")
    subject = "The task involves developing a user-friendly data management application utilizing Snowflake, Streamlit, and Snowpark. Users can select a Snowflake data stage, view files within an Internal/External(S3 bucket) and preview file contents. The app allows users to select specific columns for data profiling, and then select and insert one or more rows of data into a database."
    st.markdown("""
    <style>
    .big-font {
        font-size:20px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="big-font">The task involves developing a user-friendly data management application utilizing Snowflake, Streamlit, and Snowpark. Users can select a Snowflake data stage, view files within an Internal/External(S3 bucket) and preview file contents. The app allows users to select specific columns for data profiling, and then select and insert one or more rows of data into a database</p>', unsafe_allow_html=True)

if selected == 'Data Browser':
    bottom_menu_1 = st.columns((4,1,1))
    with bottom_menu_1[0]:
        st.button("Help",help="""1. Stage raw files on AWS S3 (preferably structured or semi-structured) using AWS Platform \n 2. Build a Streamlit Data to support the following: \n a) List Snowflake Data Stages and choose a stage\n b) List files on the S3 bucket (show file properties)\n c) Select a File and Preview the contents of the file in a tabular / grid format\n d) Allow the user to choose a column & profile the data (Streamlit <> Python, Pandas), show results\n e) Allow user to select one or more or all rows & ingest the data in a database table (Snowflake > Python Pandas > Ingest)""")
    with st.container(border=True):
        status = st.radio("Select One Stage: ", ('Internal Satge', 'External Stage(S3)'),index=None)

    # conditional statement to print 
    if (status == 'Internal Satge'):
        st.success("You have selected Internal Stage")
    elif (status=='External Stage(S3)'):
        st.success("You have selected External Stage(S3)")
    else:
        st.info("You haven't selected anything")

    #con=st.connection("snowflake")
    #df=con.query("select 1 from dual")
    if (status == 'Internal Satge'):
    #   session = get_active_session()
        st.subheader("There are no files in Internal Stage")

    if(status=='External Stage(S3)'):
        #session = get_active_session()
        with st.container(border=True):
            st.subheader("External Stage Files:")
            sql = "LIST @STORE_DB.ATLAS.AWS_S3_STG;"
            df_collect = session.sql(sql).collect()
            df = pd.DataFrame(df_collect)
            #TO display the headers in bold
            st.write(df)
            #st.markdown(df.to_html(escape=False),unsafe_allow_html=True)
            #st.dataframe(data=df,use_container_width=True)

        #files = st.selectbox("Please select any one file from the below list",(df))

        sql_filename = "select distinct METADATA$FILENAME from @STORE_DB.ATLAS.AWS_S3_STG"
        df_filename = session.sql(sql_filename).collect()
        files = st.selectbox("Please select any one file from the below options and press the preview button :",(df_filename), index=None)

        #Write directly to the app
        if 'clicked' not in st.session_state:
            st.session_state.clicked = False

        def click_button():
            st.session_state.clicked = True
                
        st.button('PREVIEW', on_click = click_button)
            
            #Preview code
        if st.session_state.clicked:
            # The message and nested widget will remain on the page
            st.write(f"You have selected {files} file and following are the content of the file: ")
            #extract the table name from file name
            table_name = files.replace(' ','')[:-4].upper()

            #sql_pull=f" SELECT $1,$2,$3,$4,$5,$6,$7,$8 FROM @AWS_S3_STG/{files};"
            sql_truncate = f"TRUNCATE TABLE STORE_DB.ATLAS.{table_name};"
            session.sql(sql_truncate).collect()
            sql_copy = f"COPY INTO STORE_DB.ATLAS.{table_name} FROM @STORE_DB.ATLAS.AWS_S3_STG/{files} FILE_FORMAT=F1"
            session.sql(sql_copy).collect()
            sql_select = f"select * from STORE_DB.ATLAS.{table_name}"
            df_sql_select = session.sql(sql_select).collect()
            dataframe_select = pd.DataFrame(df_sql_select)
            #st.write(dataframe_select)
            #st.markdown(dataframe_select.to_html(escape=False),unsafe_allow_html=True)

            # Show data
            #@st.cache_data(show_spinner=False)
            def split_frame(input_df, rows):
                df3 = [input_df.loc[i : i + rows - 1, :] for i in range(0, len(input_df), rows)]
                return df3
                
            pagination = st.container()

            bottom_menu = st.columns((4,1,1))
            with bottom_menu[2]:
                batch_size = st.selectbox("Page Size", options=[10, 20, 50])
            with bottom_menu[1]:
                total_pages = (
                                int(len(dataframe_select) / batch_size) if int(len(dataframe_select) / batch_size) > 0 else 1
                            )
                current_page = st.number_input(
                                                "Page", min_value=1, max_value=total_pages, step=1
                                            )
            with bottom_menu[0]:
                    st.markdown(f"Page **{current_page}** of **{total_pages}** ")

            pages = split_frame(dataframe_select, batch_size)
            pagination.dataframe(data=pages[current_page - 1], use_container_width=True)
            
            #Column Names
            sql_columns = f"select column_name from information_schema.columns where table_name = '{table_name}' and table_schema = 'ATLAS';"
            df_sql_columns = session.sql(sql_columns).collect()
            df_columns = pd.DataFrame(df_sql_columns)

            st.markdown("""<hr style="height:2px;border:none;color:#1E96DE;background-color:#1E96DE;" /> """, unsafe_allow_html=True)

            #Data Profiling
            st.subheader("Data Profiling")
            with st.expander("Expand to see the data profiling"):
                #Checkbox
                #Function to create checkbox
                st.caption('Please select any columns from the sidebar :')
                def checkbox_container(data):
                    #select_column_box = st.text_input('Please select any column')
                    cols = st.columns(5)
                    if cols[0].button('Select All', type = 'primary'):
                        for i in data['COLUMN_NAME']:
                            st.session_state['dynamic_checkbox_' + i] = True
                        st.experimental_rerun()
                    if cols[1].button('UnSelect All',type='primary'):
                        for i in data['COLUMN_NAME']:
                            st.session_state['dynamic_checkbox_' + i] = False
                        st.experimental_rerun()
                    st.caption("Column Names :")
                    for i in data['COLUMN_NAME']:
                        st.checkbox(i, key='dynamic_checkbox_' + i)

                #Function to print selected columns    
                def get_selected_checkboxes():
                    return [i.replace('dynamic_checkbox_','') for i in st.session_state.keys() if i.startswith('dynamic_checkbox_') and st.session_state[i]]

                checkbox_container(df_columns)
                new_data = st.text_input('You selected',get_selected_checkboxes())
                #st.write(get_selected_checkboxes())

                selected_column = get_selected_checkboxes()

                #to preview the data for selected columns
                #try:
                if True:
                    appended_data = []
                    df_table_format = pd.DataFrame()
                    for values in selected_column:
                        #sql query to preview the data for selected columns
                        # to show the distinct records
                        #select_sql = f"select count(*) from {table_name} where {values} ='nan'"
                        null_count = dataframe_select[values].isna().sum()
                        total_count = dataframe_select.shape[0]
                        with st.container():
                            #df_table_format=pd.DataFrame({'COLUMN_NAME':[values],'NULL_COUNT':[null_count]})
                            df_table_format = df_table_format._append(pd.DataFrame({"COLUMN_NAME":[values],"NULL_COUNT":[null_count]}),ignore_index=True)
                            #st.write(f"Null Count of selected column {values} :", null_count)
                    #st.write("Total count of the file is :",total_count)
                    s = f"<p style='font-size:26px;'>Total count of the selected file is :{total_count}</p>"
                    st.markdown(s, unsafe_allow_html=True)
                    st.markdown(df_table_format.to_html(escape=False),unsafe_allow_html=True)
                    #st.write(df_table_format)
                        #collect_select_sql = session.sql(select_sql).collect()
                        # df_select_sql = pd.DataFrame(collect_select_sql)
                        # appended_data.append(df_select_sql)
                        # st.write(values) 
                    # df2 = pd.concat(appended_data, axis=1,ignore_index=True)
                    # df2.columns = selected_column
                    #st.write(values)
                    #st.markdown(df2.to_html(escape=False),unsafe_allow_html=True)
                #except:
                #    st.write("Please select any one column from the checkbox to profile the data:")

                st.caption("Data Profiling Table :")
                #code to show data profiling
                desc = dataframe_select.describe(include="all")
                st.write(desc.transpose())

                # df4 = pd.DataFrame(df2)
                # st.write(df4.describe(include=all))

            st.markdown("""<hr style="height:2px;border:none;color:#1E96DE;background-color:#1E96DE;" /> """, unsafe_allow_html=True)

            st.subheader("Data Ingestion :")
            #edited_df = st.data_editor(dataframe_select)

            #Data Ingestion into snowflake based on user selection
            with st.expander("Data Ingestion into Snowflake"):
                #Function to create a dataframe which contains the user selected data
                def dataframe_with_selections(dataset):
                    df_with_selections = dataset.copy()
                    df_with_selections.insert(0, "Select", False)

                    # Get dataframe row-selections from user with st.data_editor
                    edited_df = st.data_editor(
                        df_with_selections,
                        hide_index=True,
                        column_config={"Select": st.column_config.CheckboxColumn(required=True)},
                        disabled=dataset.columns,
                    )

                    # Filter the dataframe using the temporary column, then drop the column
                    selected_rows = edited_df[edited_df.Select]
                    return selected_rows.drop('Select', axis=1)

                #call the function dataframe_with_selection
                selection = dataframe_with_selections(dataframe_select)
                st.write("Your selection:")
                st.write(selection)
                #adding datetime to the dataframe 
                today = datetime.today()
                selection['LOAD_DATE']=pd.to_datetime(today)
                selection['LOAD_DATE'] =selection['LOAD_DATE'].dt.strftime("%Y-%m-%d %H:%M:%S")
                #st.write(selection.dtypes)
                #st.write(selection)
                submit_button = st.button('❄️ Ingest Data into Snowflake')
                if submit_button:
                    with st.spinner("Making snowflakes..."):
                        column_names=selection.columns
                        insert_df=pd.DataFrame(selection, columns=column_names)
                        session.write_pandas(insert_df, f"{table_name}_STG")  
                        st.success("Loaded the requested data Successfully")
            
#st.session_state.clicked = False 

        

       
#Footer
footer="""<style>
a:link , a:visited{
color: #FFFFFF;
background-color: transparent;
text-decoration: underline;
}
.footer {
position: fixed;
left: 0;
bottom: 0;
width: 100%;
background-color: #3A3A3A;
color: black;
text-align: center;
}
</style>
<div class="footer">
<p>© Copyright 2024 Saama Technologies LLC. All Rights Reserved. Privacy Policy <a style='display: block; text-align: center;</a></p>
</div>
"""
st.markdown(footer,unsafe_allow_html=True)