import streamlit as st
import pandas as pd
import numpy as np
import db_dtypes as db
import plotly.express as px
from google.oauth2 import service_account
from google.cloud import bigquery
import time
import geopandas as gpd
import plotly.graph_objects as go


st.set_page_config(layout="wide", initial_sidebar_state='expanded')
credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
client = bigquery.Client(credentials=credentials)

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

query = ("SELECT * FROM `projet-prello.transform_prello.score_table_full` ")

query_job = client.query(query)
query_result = query_job.result()
data = query_result.to_dataframe()



image = "https://i.goopics.net/an3xxk.png"
container = st.container()
container.markdown(
        f'<div style="display: flex; justify-content: center; margin-top: 0px; margin-bot: 0px;">'
        f'<img src="{image}" style="width: 5;">'
        f'</div>',
        unsafe_allow_html=True
    )


#Création d'une variable pour chaque critère. Par défaut sur False, elle sera changée en True si un critère est selectionné dans la selectbox.
logement_selected = False
location_selected = False
geographie_selected = False
ete_selected = False
hiver_selected = False
sites_selected = False


st.markdown(
    '<h1 style="text-align: center; margin-top: 0px">Ça n\'a jamais été aussi simple de <em>partager</em> !</h1>',
    unsafe_allow_html=True
)
st.markdown(" ")
st.markdown(
    """
    <div style="height: 4px; background-color: #113f60;"></div>
    """,
    unsafe_allow_html=True
)
st.markdown(" ")
with st.sidebar:
    st.header("Choix des critères")

# Type logement
# On vient supprimer les colonnes qui ne correspondent pas au choix de l'utilisateur (pour ne pas impacter le score).
with st.sidebar:
    logement_choice = st.selectbox(
            'Quel type de logement?',
            ('Maison', 'Appartement', 'Sans importance'), 
            index=None, 
            placeholder="Choisir une option..",
            disabled=False,)
    data["prix_carre"] = 0
    data["sales_choice"] = 0
    if logement_choice == "Maison":
            data["prix_carre"] = data["prix_m2_maison"]
            data["sales_choice"] = data["avg_sales_maison"]
            data = data.drop(columns=["avg_sales_all", "avg_surface_appt_m2",
                                     "tier_avg_surface_appt_m2", "avg_surface_all", "tier_avg_surface_all", 
                                      "avg_location_appart", "tier_avg_location_appart", 
                                       "prix_m2_appt", "tier_prix_m2_appt", "tier_prix_m2_all", "prix_m2_all"])
    elif logement_choice == "Appartement":
             data["prix_carre"] = data["prix_m2_appt"]
             data["sales_choice"] = data["avg_sales_appt"]
             data = data.drop(columns=["avg_sales_all", "avg_surface_maison_m2",
                                      "tier_avg_surface_maison_m2", "avg_surface_all", "tier_avg_surface_all", 
                                      "avg_location_maison", "tier_avg_location_maison", 
                                      "prix_m2_maison", "tier_prix_m2_maison", "tier_prix_m2_all", "prix_m2_all"])
    elif logement_choice == "Les deux!":
              data["prix_carre"] = data["prix_m2_all"]
              data["sales_choice"] = data["avg_sales_all"]
              data = data.drop(columns=["avg_surface_maison_m2", "avg_surface_appt_m2",
                                     "tier_surface_appt", "tier_surface_maison", "tier_avg_surface_maison_m2", "tier_avg_surface_appt_m2",
                                     "prix_m2_appt", "tier_prix_m2_appt", "prix_m2_maison", "tier_prix_m2_maison"])

# Si le logement_choice n'est pas égal à sa valeur placeholder (donc aucune selection), alors elle devient True.    
    if logement_choice and logement_choice != "Choisir une option..":
        logement_selected = True

# Location 
# On vient supprimer les colonnes en rapport avec la location du bien immobilier (pour ne pas impacter le score).
with st.sidebar:
    location_choice = st.selectbox(
                'On fait louer, ou pas ?',
                 ('Oui !', 'Non !'), 
                 index=None, 
                 placeholder="Choisir une option..",
                 disabled=False,)

    if location_choice == "Non !": 
                if "avg_location_maison" in data.columns:
                    data = data.drop(columns=["avg_location_maison", "tier_avg_location_maison"])
                if "avg_location_appart" in data.columns:
                    data = data.drop(columns=["avg_location_appart", "tier_avg_location_appart"])
    elif logement_choice == "Oui !":
                pass

# Voir logement_choice
    if location_choice and location_choice != "Choisir une option..":
        location_selected = True

# Geographie 
# On re-enregistre notre dataframe avec les lignes qui correspondent au choix de l'utilisateur.
with st.sidebar:
    geographie_choice = st.selectbox(
                "Tu es plutôt..",
                ("Mer !", "Montagne !", "Plaine !", "Tout me va !"),
                index=None, 
                placeholder="Choisir une option..",
                disabled=False,)

    if geographie_choice == "Mer !":
                data = data[data['geographie'] == 'Mer']
    elif geographie_choice == "Montagne !":
                data = data[data['geographie'] == 'Montagne']
    elif geographie_choice == "Plaine !":
                data = data[data['geographie'] == 'Plaine']
    elif geographie_choice == "Tout me va !":
                pass

# Voir logement_choice   
    if geographie_choice and geographie_choice != "Choisir une option..":
        geographie_selected = True
            

# Temp. ete
# On cree une colonne score temperature ete, avec par defaut une valeur de 0.
# En fonction du choix de l'utilisateur, on vient remplacer les 0 des deux colonnes concernées par 5 ou 6.
with st.sidebar:
    ete_choice = st.selectbox(
                "En été, tu préfères..",
                ("Avoir chaud !", "Normal", "Être au frais !"), 
                index=None, 
                placeholder="Choisir une option..",
                disabled=False,)
        
    data['score_temp_ete'] = 0          
    if ete_choice == "Avoir chaud !":
                data.loc[data['tier_temp_ete'] == 6, 'score_temp_ete'] = 6
                data.loc[data['tier_temp_ete'] == 5, 'score_temp_ete'] = 5
    elif ete_choice == "Normal":
                data.loc[data['tier_temp_ete'] == 4, 'score_temp_ete'] = 6
                data.loc[data['tier_temp_ete'] == 3, 'score_temp_ete'] = 5
    elif ete_choice == "Être au frais":
                data.loc[data['tier_temp_ete'] == 2, 'score_temp_ete'] = 6
                data.loc[data['tier_temp_ete'] == 1, 'score_temp_ete'] = 5

# Voir logement_choice
    if ete_choice and ete_choice != "Choisir une option..":
        ete_selected = True

# Temp. hiver
# On cree une colonne score temperature hiver, avec par defaut une valeur de 0.
# En fonction du choix de l'utilisateur, on remplace les 0 des deux colonnes concernées par 5 ou 6.
with st.sidebar:
    hiver_choice = st.selectbox(
                "En hiver, tu préfères une temperature..",
                ("Douce !", "Fraiche !", "Glaciale !"),
                index=None, 
                placeholder="Choisir une option..",
                disabled=False,)

    data['score_temp_hiver'] = 0
    if hiver_choice == "Douce !":
                data.loc[data['tier_temp_hiver'] == 6, 'score_temp_hiver'] = 6
                data.loc[data['tier_temp_hiver'] == 5, 'score_temp_hiver'] = 5
    elif hiver_choice == "Fraiche !":
                data.loc[data['tier_temp_hiver'] == 4, 'score_temp_hiver'] = 6
                data.loc[data['tier_temp_hiver'] == 3, 'score_temp_hiver'] = 5
    elif hiver_choice == "Glaciale !": 
                data.loc[data['tier_temp_hiver'] == 2, 'score_temp_hiver'] = 6
                data.loc[data['tier_temp_hiver'] == 1, 'score_temp_hiver'] = 5

# Voir logement_choice
    if hiver_choice and hiver_choice != "Choisir une option..":
        hiver_selected = True

# Sites touristiques 
# On cree une colonne score sites, avec par defaut une valeur de 0.
# En fonction du choix de l'utilisateur, on remplace les 0 des deux colonnes concernées par 5 ou 6.
with st.sidebar:           
    sites_choice = st.selectbox(
                "Tu souhaites visiter des sites touristiques..",
                ("Tous les jours !", "De temps en temps", "Jamais !"),
                index=None, 
                placeholder="Choisir une option..",
                disabled=False,)
        
    data['score_sites'] = 0
    if sites_choice == "Tous les jours !":
                data.loc[data["tier_nb_sites"] == 6, "score_sites"] = 6
                data.loc[data["tier_nb_sites"] == 5, "score_sites"] = 5
    elif sites_choice == "De temps en temps":
                data.loc[data["tier_nb_sites"] == 4, "score_sites"] = 6
                data.loc[data["tier_nb_sites"] == 3, "score_sites"] = 5
    elif sites_choice == "Jamais !":
                data = data.drop(columns= ["nb_sites", "tier_nb_sites"])

# Voir logement_choice
    if sites_choice and sites_choice != "Choisir une option..":
        sites_selected = True

# Calcul "basique" du score final.
data["final_score"] = 0
final_score = (data['score_temp_ete'] + data['score_temp_hiver'])
if "score_sites" in data.columns:
            final_score += data['score_sites']

# Ajout des scores de surfaces en fonction du type de logement choisit plus haut.
if "tier_avg_surface_maison_m2" in data.columns:
            final_score += data["tier_avg_surface_maison_m2"]
elif "tier_avg_surface_appt_m2" in data.columns:
            final_score += data["tier_avg_surface_appt_m2"]
elif "tier_avg_surface_all" in data.columns:
            final_score += data["tier_avg_surface_all"]

# Ajout des scores de locations en fonction de la reponse Oui ou Non plus haut. 
if "score_location_maison" in data.columns:
            final_score += data["score_location_maison"]
elif "score_location_appart" in data.columns:
            final_score += data["score_location_appart"]

# Ajout des scores des prix m2. 
if "tier_prix_m2_all" in data.columns:
            final_score += data["tier_prix_m2_all"]
elif "tier_prix_m2_appt" in data.columns:
            final_score += data["tier_prix_m2_appt"]
elif "tier_prix_m2_maison" in data.columns:
            final_score += data["tier_prix_m2_maison"]

# Ajout du score nb_medecins et jours de soleil
final_score += data["tier_nb_medecins"]
final_score += data["tier_jours_soleil"]

# Soustraction des scores de catastrophes Nat. et scores de cambriolage.
final_score -= data["tier_nb_catastrophes"] / 2
final_score -= data["tier_avg_ratio_camb"] / 2

data["Note"] = final_score * 2
data["ratiocamb_10"] = data["avg_ratio_camb"].apply(lambda x: x * 10)
data = data[["department_code", "department_name", "avg_sales_appt", "avg_sales_maison", 'geographie', "prix_carre", "jours_soleil", "sales_choice", "ratiocamb_10","Note"]]


# Selection du TOP 10, et reset de l'index pour qu'il commence a partir de 1 jusque 10.
top_10 = data.nlargest(10, 'Note')

top_10 = top_10.reset_index(drop=True).reset_index()
top_10['index'] += 1
top_10 = top_10.set_index('index')
top_10["colorank"] = top_10.index.astype(str)

# Verifie si chaque variable "selected" est active, donc True. Si chaque valeur est True, alors le 'not' vient inverser le résultat,
# qui sera donc False. Si rerun_button_disabled est égal à False, alors le parametre du bouton "disabled" est égal à False, donc bouton actif.
rerun_button_disabled = not (logement_selected and location_selected and geographie_selected and ete_selected and hiver_selected and sites_selected)

with st.sidebar:  
    rerun_button = st.button("Lancer la recherche", disabled=rerun_button_disabled)
    st.info('Le classement est défini en fonction des notes de chaque département.', icon="ℹ️")

color_dict = {"0":"#FFA082","1":"#559BA3", "2":"#8EAD72", "3":"#FFECB3", "4":"#E1DCCA", "5":"#113F60", "6":"#ffd351", 
              "7":"#D1E8BD", "8":"#FF693A", "9":"#8C9BA6"}
# Quand le bouton "Résultat" est activé, une petite roue vient tourner en mode chargement, puis affiche le top 10 des dpmts en fonction de 
# tous les critères.

geodata = gpd.read_file('data_geo/departements.geojson')
df_geo = pd.merge(geodata, top_10, left_on='code', right_on='department_code', how='inner')
df_geo = df_geo.drop(['code', 'nom'], axis=1)

col1, inter_space, col2 = st.columns((0.45,0.05, 0.50), gap='small')



if rerun_button : 
    with st.spinner('Nos experts sont sur le coup...'):
        time.sleep(2)

    with col1 :
        st.header("C'est à peu près là, ou là.")

# Création d'une map "choropleth", elle affichera les 10 départements selectionnés.
        fig = px.choropleth_mapbox(df_geo, 
                                geojson=df_geo.geometry, 
                                locations=df_geo.index,  
                                mapbox_style="carto-positron", 
                                hover_name='department_name',
                                color= "colorank",  
                                color_discrete_map=color_dict, 
                                center={ "lat": 46.8, "lon": 1.8}, 
                                custom_data=['department_name', 'geographie'], 
                                zoom=4.2, 
                                opacity=0.9) 
                                

        fig.update_traces(
        hovertemplate=
            "<b>%{customdata[0]}</b><br>Relief: %{customdata[1]}"
        )

        fig.update_layout(margin={"r": 0, "t": 10, "l": 0, "b": 0}, showlegend=False, legend_itemwidth=35, width=650)
        col1.plotly_chart(fig, use_container_width=True)

        st.header("Au voleur !")
        st.subheader("En France, le taux moyen de cambriolage est de 3 personnes sur 1000 par an.")

# Création d'un graph en barre, qui affiche le ration de cambriolage par département, avec la moyenne française.
        fig_10 = px.bar(top_10, 
                   x='department_name', y='ratiocamb_10',                   
                   color= "colorank",
                   color_discrete_map=color_dict,
                   custom_data=['department_name', 'ratiocamb_10'],
                   labels={'ratiocamb_10': 'Logements cambriolés sur 1000/an', 'department_name': 'Départements'})

        fig_10.update_traces(
            hovertemplate=
            "<b>%{customdata[0]}</b><br>Sécurité domiciliaire: %{customdata[1]}",
            texttemplate='%{y:.2f}',
            textposition="outside"
        )
        top_10['cambriolage_fr'] = 3
        fig_10.add_trace(go.Scatter(x=top_10.department_name, 
                                    y=top_10.cambriolage_fr, 
                                    mode='lines', 
                                    line=dict(color='red'), 
                                    name='Moyenne francaise'))
        
        fig_10.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E1DCCA')
        fig_10.update_layout(margin={"r": 170, "t": 10, "l": 0, "b": 0}, showlegend=False, legend_itemwidth=35, width=650)
        col1.plotly_chart(fig_10, use_container_width=False)
        


    with inter_space:
            st.write(" ")

    
# Création d'un tableau, qui affiche le TOP 10, ainsi que le prix moyen d'achat d'une maison ou d'un appartement, par département.
    with col2: 
            st.header("Voilà nos vainqueurs !")

            top_10["avg_sales_maison"] = top_10["avg_sales_maison"].round(decimals=0)
            top_10["avg_sales_maison"] = top_10["avg_sales_maison"].astype(int)
            top_10["avg_sales_appt"] = top_10["avg_sales_appt"].round(decimals=0)
            top_10["avg_sales_appt"] = top_10["avg_sales_appt"].astype(int)

            def add_euro_symbol(value):
                return f"{value} €"

            top_10["avg_sales_maison"] = top_10["avg_sales_maison"].map(add_euro_symbol)
            top_10["avg_sales_appt"] = top_10["avg_sales_appt"].map(add_euro_symbol)

            top_10_renamed = top_10[["department_code", "department_name", "avg_sales_maison", "avg_sales_appt"]].rename(
                    columns={"department_code": "Numéros", "department_name": "Départements", "avg_sales_maison":"Prix moyen d'une maison",
                             "avg_sales_appt":"Prix moyen d'un appart"})

            top_10_no_index = top_10_renamed.reset_index(drop=True)
            table_html = top_10_no_index.to_html(index=False)

            style_css = """
                <style>
                th {
                    background-color: #E1DCCA; 
                }
                th:nth-child(1) {
                text-align: center; 
                  }
                th:nth-child(2) {
                text-align: center;
                }
                }
                th:nth-child(3) {
                text-align: center;
                }
                }
                th:nth-child(4) {
                text-align: center;
                }
                td {
                text-align: center; 
                }
                </style>
            """

            # Afficher le style CSS et le tableau HTML dans Streamlit
            st.write(style_css, unsafe_allow_html=True)
            st.write(table_html, unsafe_allow_html=True)


            st.write(" ")
            st.write(" ")

            st.header("Mon bon Roi !")
            st.subheader("Impact du soleil sur les ventes immobilières")

# Création d'un scatter plot, basé sur le nombre de jours ensoleillés, et le prix d'achat. 
            size_values = top_10['jours_soleil'].tolist()
            color_mapping = {'Plaine': '#8EAD72', 'Montagne': '#FFA082', 'Mer': '#559BA3'}
            fig_7 = px.scatter(top_10, x='sales_choice', y='jours_soleil', 
                               color="colorank", 
                               color_discrete_map=color_dict, 
                               size=size_values, 
                               labels={'department_name': 'Département', 'jours_soleil': 'Nombre de jours ensoleillés /an', 'sales_choice': "Prix moyen d'achat"}, 
                               custom_data=['department_name', 'jours_soleil'])
            fig_7.update_traces(
            textposition='top right',
            hovertemplate=
            "<b>%{customdata[0]}</b><br>Nombre de jours ensoleillés: %{customdata[1]}"
             )
            fig_7.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E1DCCA')
            fig_7.update_layout(margin={"r": 0, "t": 10, "l": 0, "b": 0}, showlegend=False, legend_itemwidth=35, width=650)
            col2.plotly_chart(fig_7, use_container_width=False)