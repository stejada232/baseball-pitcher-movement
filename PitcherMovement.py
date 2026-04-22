from pybaseball import  playerid_lookup, statcast_pitcher
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from datetime import date

pitch_dict = {
    'FF': 'Four-Seam Fastball',
    'SI': 'Sinker',
    'FC': 'Cutter',
    'SL': 'Slider',
    'ST': 'Sweeper',
    'CH': 'Changeup',
    'CU': 'Curveball',
    'KC': 'Knuckle Curve',
    'FS': 'Splitter',
    'SV': 'Slurve',
    'KN': 'Knuckleball',
    'EP': 'Eephus',
    'FO': 'Forkball',
    'PO': 'Pitchout'
}

with st.form("pitcher_lookup_form"):

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Name", "Paul Skenes").lower()
        
    with col2:
        season = st.number_input(
            "Season", 
            min_value=2008,
            max_value= date.today().year,
            value= date.today().year,
            step=1
        )

    if " " in name:
        fst_name, lst_name = name.split(" ", 1)
    else:
        fst_name, lst_name = name, ""

    plyr_res = playerid_lookup(lst_name,fst_name)

    submitted = st.form_submit_button("Generate Pitching Graph")

    fst_name, lst_name = fst_name.capitalize(), lst_name.capitalize()

    if submitted:
        if not plyr_res.empty: 
            plyr_id = plyr_res['key_mlbam'].values[0]

            plyr_ptch = statcast_pitcher(f"{season}-01-01", f"{season}-12-31", plyr_id)

            df = pd.DataFrame(plyr_ptch)
            df = df[df['game_type'] == 'R']
            df['pfx_x_in'] = df['pfx_x'] * 12
            df['pfx_z_in'] = df['pfx_z'] * 12
            df['pitch_name'] = df['pitch_type'].map(pitch_dict).fillna(df['pitch_type'])

            if not df.empty:

                fig,ax = plt.subplots()
                sns.scatterplot(data=df, x='pfx_x_in', y='pfx_z_in', hue='pitch_name', alpha=0.7, ax=ax)
                ax.axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
                ax.axvline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
                ax.set(xlabel='Horizontal Movement (inches)', ylabel='Vertical Movement (inches)', title=f"{fst_name} {lst_name} Pitch Movement")

                plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0.)

                st.pyplot(fig)
            else:
                st.error(f"{fst_name} {lst_name} did not pitch in {season}.")
        else:
            st.error(f"{fst_name} {lst_name} not found.")

