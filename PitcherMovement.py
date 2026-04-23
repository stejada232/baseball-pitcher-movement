from pybaseball import  playerid_lookup, statcast_pitcher
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from datetime import date

pitch_dict = {
    'FF': ('Four-Seam Fastball', '#D22D49'),
    'SI': ('Sinker', '#FE9D00'),
    'FC': ('Cutter', '#933F2C'),
    'SL': ('Slider', '#EEE716'),
    'ST': ('Sweeper', '#FDD26E'),
    'CH': ('Changeup', '#1DBE3A'),
    'CU': ('Curveball', '#00D1ED'),
    'KC': ('Knuckle Curve', '#6236CD'),
    'FS': ('Splitter', '#3BACAC'),
    'SV': ('Slurve', '#D09ECC'),
    'KN': ('Knuckleball', '#8A8A8A'),
    'EP': ('Eephus', '#52AF56'),
    'FO': ('Forkball', '#55CCAB'),
    'PO': ('Pitchout', '#292929')
}

@st.cache_data
def load_pitcher_data(season_year, player_id):
    # This will only run ONCE per player/season combination
    return statcast_pitcher(f"{season_year}-01-01", f"{season_year}-12-31", player_id)

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

    batter_handedness = st.selectbox("Filter by Batter Handedness", ('All Batters', 'RHB', 'LHB'))
    strikeouts_only = st.checkbox("Strikeouts Only")

    submitted = st.form_submit_button("Generate Pitching Graph")

    fst_name, lst_name = fst_name.capitalize(), lst_name.capitalize()

    if submitted:
        if not plyr_res.empty: 
            plyr_id = plyr_res['key_mlbam'].values[0]

            plyr_ptch = load_pitcher_data(season, plyr_id)

            df = pd.DataFrame(plyr_ptch)
            df = df[df['game_type'] == 'R']
            match batter_handedness:
                case 'All Batters':
                    pass
                case 'RHB':
                    df = df[df['stand'] == 'R']
                case 'LHB':
                    df = df[df['stand'] == 'L']
                case _:
                    pass

            if strikeouts_only:
                df = df[df['events'] == 'strikeout']

            df['pfx_x_in'] = df['pfx_x'] * 12
            df['pfx_z_in'] = df['pfx_z'] * 12
            
            df['pitch_name'] = df['pitch_type'].apply(lambda x: pitch_dict.get(x, (x, '#000000'))[0])
            df['pitch_color'] = df['pitch_type'].apply(lambda x: pitch_dict.get(x, (x, '#000000'))[1])

            stats = df.groupby(['pitch_name', 'pitch_color']).agg(
                count=('pitch_name', 'count'),
                avg_velo=('release_speed', 'mean'),
                avg_spin=('release_spin_rate', 'mean')
            ).reset_index().sort_values(by='count', ascending=False).reset_index(drop=True)

            total_pitches = len(df)
            
            stats['legend_label'] = stats.apply(lambda x: f"{x['pitch_name']} ({((x['count'] / total_pitches) * 100):.1f}% | {x['avg_velo']:.1f} mph | {x['avg_spin']:.0f} rpm)", axis=1)            
            
            ordered_labels = stats['legend_label'].tolist()
            dynamic_colors = dict(zip(stats['legend_label'], stats['pitch_color']))
            
            df = df.merge(stats[['pitch_name', 'legend_label']], on='pitch_name', how='left')
            
            if not df.empty:

                fig,ax = plt.subplots()
                sns.scatterplot(data=df, x='pfx_x_in', y='pfx_z_in', hue='legend_label', palette=dynamic_colors, hue_order=ordered_labels, alpha=0.7, ax=ax)
                ax.axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
                ax.axvline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
                ax.set(xlabel='Horizontal Movement (inches)', ylabel='Vertical Movement (inches)', title=f"{fst_name} {lst_name} {season} Pitch Movement ({batter_handedness}) ({total_pitches} Pitches)")

                plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0.)

                st.pyplot(fig)
            else:
                st.error(f"{fst_name} {lst_name} did not pitch in {season} against {batter_handedness}.")
        else:
            st.error(f"{fst_name} {lst_name} not found.")

