import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
from scipy.stats import poisson

# Set up the Streamlit app title and layout
st.set_page_config(page_title='Premier League 2024-25 Points Prediction', layout='wide')

page_bg_img = '''
<style>
.stApp {

    background-size: cover;
    background-repeat: no-repeat;
    background-attachment: fixed;
    color: white;
}
table {
    border-collapse: collapse;
    width: 100%;
    background-color: rgba(0, 0, 0, 0.6);
    color: white;
}
th, td {
    text-align: left;
    padding: 8px;
}
th {
    background-color: #4CAF50;
    color: white;
}
tr:nth-child(even) {
    background-color: rgba(255, 255, 255, 0.2);
}
tr:hover {
    background-color: rgba(255, 255, 255, 0.3);
}
</style>
'''

# Inject the custom CSS
st.markdown(page_bg_img, unsafe_allow_html=True)

# Title of the app
st.title('Premier League 2024-25 Points Prediction')

# Load the previous matches data
prev_matches = pd.read_csv('premier-league-matches.csv')

# Load the current points table and upcoming matches
dict_table = pd.read_excel('pl_table.xlsx')
matches = pd.read_excel('pl_matches.xlsx')

# Process previous matches data
df_home = prev_matches[['Home Team', 'Home Goals', 'Away Goals']]
df_away = prev_matches[['Away Team', 'Home Goals', 'Away Goals']]
df_home = df_home.rename(columns={'Home Team': 'Team', 'Home Goals': 'GoalsScored', 'Away Goals': 'GoalsConceded'})
df_away = df_away.rename(columns={'Away Team': 'Team', 'Home Goals': 'GoalsConceded', 'Away Goals': 'GoalsScored'})
df_team_strength = pd.concat([df_home, df_away], ignore_index=True).groupby('Team').mean()

# Predict points function
def predict_points(home, away):
    if home in df_team_strength.index and away in df_team_strength.index:
        lamb_home = df_team_strength.at[home, 'GoalsScored'] * df_team_strength.at[away, 'GoalsConceded']
        lamb_away = df_team_strength.at[away, 'GoalsScored'] * df_team_strength.at[home, 'GoalsConceded']
        
        prob_home, prob_away, prob_draw = 0, 0, 0
        
        for x in range(0, 11):
            for y in range(0, 11):
                p = poisson.pmf(x, lamb_home) * poisson.pmf(y, lamb_away)
                if x == y:
                    prob_draw += p
                elif x > y:
                    prob_home += p
                else:
                    prob_away += p

        points_home = 3 * prob_home + prob_draw
        points_away = 3 * prob_away + prob_draw
        
        return points_home, points_away
    else:
        return 0, 0

# Convert points to integer
dict_table['Points'] = dict_table['Points'].round().astype(int)

# Initialize the points dictionary with additional columns for simulation
final_team_stats = {team: {'Points': points, 'Played': 0, 'Won': 0, 'Drawn': 0, 'Lost': 0} for team, points in dict_table.set_index('Team')['Points'].to_dict().items()}

# Simulate the remaining matches
for index, row in matches.iterrows():
    home_team = row['Home Team']
    away_team = row['Away Team']
    
    points_home, points_away = predict_points(home_team, away_team)
    points_home = int(round(points_home))
    points_away = int(round(points_away))
    
    if home_team in final_team_stats:
        final_team_stats[home_team]['Points'] += points_home
        final_team_stats[home_team]['Played'] += 1
        if points_home > points_away:
            final_team_stats[home_team]['Won'] += 1
        elif points_home < points_away:
            final_team_stats[home_team]['Lost'] += 1
        else:
            final_team_stats[home_team]['Drawn'] += 1
    
    if away_team in final_team_stats:
        final_team_stats[away_team]['Points'] += points_away
        final_team_stats[away_team]['Played'] += 1
        if points_away > points_home:
            final_team_stats[away_team]['Won'] += 1
        elif points_away < points_home:
            final_team_stats[away_team]['Lost'] += 1
        else:
            final_team_stats[away_team]['Drawn'] += 1

# Correcting the points calculation based on wins, draws, and losses
for team in final_team_stats:
    final_team_stats[team]['Points'] = (final_team_stats[team]['Won'] * 3) + final_team_stats[team]['Drawn']

# Convert the points dictionary to a DataFrame
final_table = pd.DataFrame.from_dict(final_team_stats, orient='index')

# Sort the final table to determine the winner
final_table = final_table.sort_values(by='Points', ascending=False)

# Display the final points table
st.subheader('Final Points Table')
st.dataframe(final_table.style.set_table_styles(
    [{'selector': 'thead th', 'props': [('background-color', '#4CAF50'), ('color', 'white')]},
     {'selector': 'tbody tr:nth-child(even)', 'props': [('background-color', 'rgba(255, 255, 255, 0.2)')]},
     {'selector': 'tbody tr:hover', 'props': [('background-color', 'rgba(255, 255, 255, 0.3)')]}]
))

# Plot the final points table using Plotly
fig = px.bar(final_table.reset_index(), x='index', y='Points', title='Premier League 2024-25 Points Prediction', labels={'index': 'Team'})
st.plotly_chart(fig)

# Add interactive team selection
st.sidebar.header('Predict Match Outcome')
home_team = st.sidebar.selectbox('Select Home Team', final_table.index)
away_team = st.sidebar.selectbox('Select Away Team', final_table.index)

if home_team and away_team and home_team != away_team:
    points_home, points_away = predict_points(home_team, away_team)
    points_home = int(round(points_home))
    points_away = int(round(points_away))
    
    st.sidebar.subheader('Prediction')
    st.sidebar.write(f'{home_team} {points_home} - {points_away} {away_team}')

    if points_home > points_away:
        result = f'**{home_team}** is more likely to win.'
    elif points_home < points_away:
        result = f'**{away_team}** is more likely to win.'
    else:
        result = 'The match is likely to end in a draw.'
    
    st.sidebar.write(result)
else:
    st.sidebar.warning('Please select different teams for prediction.')

most_home_goals = df_home.groupby('Team')['GoalsScored'].sum().idxmax()
most_away_goals = df_away.groupby('Team')['GoalsScored'].sum().idxmax()
most_home_goals_conceded = df_home.groupby('Team')['GoalsConceded'].sum().idxmax()
most_away_goals_conceded = df_away.groupby('Team')['GoalsConceded'].sum().idxmax()

# Display additional statistics
st.subheader('Team Statistics')
st.write(f"**Team with Most Home Goals:** {most_home_goals}")
st.write(f"**Team with Most Away Goals:** {most_away_goals}")
st.write(f"**Team with Most Home Goals Conceded:** {most_home_goals_conceded}")
st.write(f"**Team with Most Away Goals Conceded:** {most_away_goals_conceded}")
