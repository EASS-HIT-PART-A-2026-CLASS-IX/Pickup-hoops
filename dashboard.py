import streamlit as st
import requests
from datetime import datetime

# API Configuration
API_URL = "http://localhost:8000"

# Page Configuration
st.set_page_config(page_title="Pick-Up Hoops", page_icon="🏀", layout="wide")
st.title("🏀 Pick-Up Hoops Dashboard")

st.subheader("League Overview")

try:
    courts_response = requests.get(f"{API_URL}/courts/")
    players_response = requests.get(f"{API_URL}/players/")
    games_response = requests.get(f"{API_URL}/games/")

    courts_count = len(courts_response.json()) if courts_response.status_code == 200 else 0
    players_count = len(players_response.json()) if players_response.status_code == 200 else 0
    games_count = len(games_response.json()) if games_response.status_code == 200 else 0
except requests.RequestException:
    courts_count = 0
    players_count = 0
    games_count = 0

summary_col_1, summary_col_2, summary_col_3 = st.columns(3)

with summary_col_1:
    st.metric("Total Courts", courts_count)

with summary_col_2:
    st.metric("Registered Players", players_count)

with summary_col_3:
    st.metric("Scheduled Games", games_count)

# Create navigation tabs
tab_courts, tab_players, tab_games = st.tabs(["Courts 🏟️", "Players ⛹️‍♂️", "Games 📅"])


def build_partial_payload(original_item, field_values):
    payload = {}
    for field_name, field_value in field_values.items():
        if field_value != original_item.get(field_name):
            payload[field_name] = field_value
    return payload


def safe_index(options, value):
    try:
        return options.index(value)
    except ValueError:
        return 0


def rerun_with_refresh():
    st.session_state["data_loaded"] = False
    st.rerun()


def fetch_collection(resource_name):
    try:
        response = requests.get(f"{API_URL}/{resource_name}/?limit=200")
        if response.status_code == 200:
            return response.json(), None
        return [], f"Could not load {resource_name}: {response.text}"
    except requests.RequestException as exc:
        return [], f"Cannot connect to API for {resource_name}: {exc}"


if st.button("🔄 Refresh Data"):
    for cache_key in ["courts_data", "players_data", "games_data", "data_errors", "data_loaded"]:
        st.session_state.pop(cache_key, None)
    rerun_with_refresh()


if not st.session_state.get("data_loaded", False):
    data_errors = []

    courts_data, courts_error = fetch_collection("courts")
    if courts_error:
        data_errors.append(courts_error)

    players_data, players_error = fetch_collection("players")
    if players_error:
        data_errors.append(players_error)

    games_data, games_error = fetch_collection("games")
    if games_error:
        data_errors.append(games_error)

    st.session_state["courts_data"] = courts_data
    st.session_state["players_data"] = players_data
    st.session_state["games_data"] = games_data
    st.session_state["data_errors"] = data_errors
    st.session_state["data_loaded"] = True


for data_error in st.session_state.get("data_errors", []):
    st.error(data_error)


courts_data = st.session_state.get("courts_data", [])
players_data = st.session_state.get("players_data", [])
games_data = st.session_state.get("games_data", [])
court_names_by_id = {court["id"]: court["name"] for court in courts_data}

# ==========================================
# TAB 1: COURTS
# ==========================================
with tab_courts:
    st.header("Courts Management")
    
    with st.expander("➕ Add a New Court", expanded=False):
        with st.form("form_add_court"):
            c_name = st.text_input("Court Name", placeholder="e.g., Rucker Park")
            c_address = st.text_input("Address")
            c_city = st.text_input("City")
            c_num_courts = st.number_input("Number of Courts (Baskets)", min_value=1, value=1)
            c_lighting = st.checkbox("Has Lighting?")
            
            submit_court = st.form_submit_button("Create Court")
            
            if submit_court:
                if not c_name.strip() or not c_address.strip() or not c_city.strip():
                    st.error("Please fill in all required fields.")
                else:
                    try:
                        payload = {
                            "name": c_name,
                            "address": c_address,
                            "city": c_city,
                            "num_courts": c_num_courts,
                            "has_lighting": c_lighting,
                        }
                        res = requests.post(f"{API_URL}/courts/", json=payload)
                        if res.status_code == 200:
                            st.success("Court added successfully!")
                            rerun_with_refresh()
                        else:
                            st.error(f"Error: {res.text}")
                    except requests.RequestException as exc:
                        st.error(f"Request failed: {exc}")

    with st.expander("✏️ Update Court", expanded=False):
        if not courts_data:
            st.warning("No courts available to update.")
        else:
            court_options = {
                f"{court['name']} - {court['city']} (ID {court['id']})": court
                for court in courts_data
            }
            selected_court_label = st.selectbox(
                "Select Court",
                list(court_options.keys()),
                key="court_update_select",
            )
            selected_court = court_options[selected_court_label]

            with st.form("form_update_court"):
                updated_name = st.text_input(
                    "Court Name",
                    value=selected_court["name"],
                    key=f"court_update_name_{selected_court['id']}",
                )
                updated_address = st.text_input(
                    "Address",
                    value=selected_court["address"],
                    key=f"court_update_address_{selected_court['id']}",
                )
                updated_city = st.text_input(
                    "City",
                    value=selected_court["city"],
                    key=f"court_update_city_{selected_court['id']}",
                )
                updated_num_courts = st.number_input(
                    "Number of Courts (Baskets)",
                    min_value=1,
                    value=int(selected_court["num_courts"]),
                    key=f"court_update_num_courts_{selected_court['id']}",
                )
                updated_has_lighting = st.checkbox(
                    "Has Lighting?",
                    value=bool(selected_court["has_lighting"]),
                    key=f"court_update_has_lighting_{selected_court['id']}",
                )

                submit_update_court = st.form_submit_button("Update Court")

                if submit_update_court:
                    try:
                        payload = build_partial_payload(
                            selected_court,
                            {
                                "name": updated_name,
                                "address": updated_address,
                                "city": updated_city,
                                "num_courts": updated_num_courts,
                                "has_lighting": updated_has_lighting,
                            },
                        )

                        if not payload:
                            st.info("No changes were made.")
                        else:
                            res = requests.patch(
                                f"{API_URL}/courts/{selected_court['id']}",
                                json=payload,
                            )
                            if res.status_code == 200:
                                st.success("Court updated successfully!")
                                rerun_with_refresh()
                            else:
                                st.error(f"Update failed: {res.text}")
                    except requests.RequestException as exc:
                        st.error(f"Request failed: {exc}")

    with st.expander("🗑️ Delete Court", expanded=False):
        if not courts_data:
            st.warning("No courts available to delete.")
        else:
            court_options = {f"{court['name']} - {court['city']} (ID {court['id']})": court["id"] for court in courts_data}
            with st.form("form_delete_court"):
                selected_court_label = st.selectbox(
                    "Select Court to Delete",
                    list(court_options.keys()),
                    key="court_delete_select",
                )
                confirm_delete_court = st.checkbox("I understand this action cannot be undone")
                submit_delete_court = st.form_submit_button("Delete Court")

                if submit_delete_court:
                    if not confirm_delete_court:
                        st.warning("Please confirm before deleting.")
                    else:
                        try:
                            court_id = court_options[selected_court_label]
                            res = requests.delete(f"{API_URL}/courts/{court_id}")
                            if res.status_code == 200:
                                st.success("Court deleted successfully!")
                                rerun_with_refresh()
                            else:
                                st.error(f"Delete failed: {res.text}")
                        except requests.RequestException as exc:
                            st.error(f"Request failed: {exc}")

    st.subheader("Current Courts")
    if courts_data:
        st.dataframe(courts_data, use_container_width=True)
    else:
        st.info("No courts found.")

# ==========================================
# TAB 2: PLAYERS
# ==========================================
with tab_players:
    st.header("Players Management")
    
    with st.expander("➕ Add a New Player", expanded=False):
        with st.form("form_add_player"):
            p_name = st.text_input("Player Name")
            p_city = st.text_input("City")
            p_skill = st.selectbox("Skill Level", ["beginner", "intermediate", "advanced"])
            
            submit_player = st.form_submit_button("Create Player")
            
            if submit_player:
                if not p_name.strip() or not p_city.strip():
                    st.error("Please fill in all required fields.")
                else:
                    try:
                        payload = {
                            "name": p_name,
                            "city": p_city,
                            "skill_level": p_skill,
                        }
                        res = requests.post(f"{API_URL}/players/", json=payload)
                        if res.status_code == 200:
                            st.success("Player added successfully!")
                            rerun_with_refresh()
                        else:
                            st.error(f"Error: {res.text}")
                    except requests.RequestException as exc:
                        st.error(f"Request failed: {exc}")

    with st.expander("✏️ Update Player", expanded=False):
        if not players_data:
            st.warning("No players available to update.")
        else:
            player_options = {
                f"{player['name']} ({player['skill_level']}) [ID {player['id']}]": player
                for player in players_data
            }
            selected_player_label = st.selectbox(
                "Select Player",
                list(player_options.keys()),
                key="player_update_select",
            )
            selected_player = player_options[selected_player_label]

            with st.form("form_update_player"):
                updated_name = st.text_input(
                    "Player Name",
                    value=selected_player["name"],
                    key=f"player_update_name_{selected_player['id']}",
                )
                updated_city = st.text_input(
                    "City",
                    value=selected_player["city"],
                    key=f"player_update_city_{selected_player['id']}",
                )
                updated_skill = st.selectbox(
                    "Skill Level",
                    ["beginner", "intermediate", "advanced"],
                    index=safe_index(
                        ["beginner", "intermediate", "advanced"],
                        selected_player["skill_level"],
                    ),
                    key=f"player_update_skill_{selected_player['id']}",
                )

                submit_update_player = st.form_submit_button("Update Player")

                if submit_update_player:
                    try:
                        payload = build_partial_payload(
                            selected_player,
                            {
                                "name": updated_name,
                                "city": updated_city,
                                "skill_level": updated_skill,
                            },
                        )

                        if not payload:
                            st.info("No changes were made.")
                        else:
                            res = requests.patch(
                                f"{API_URL}/players/{selected_player['id']}",
                                json=payload,
                            )
                            if res.status_code == 200:
                                st.success("Player updated successfully!")
                                rerun_with_refresh()
                            else:
                                st.error(f"Update failed: {res.text}")
                    except requests.RequestException as exc:
                        st.error(f"Request failed: {exc}")

    with st.expander("🗑️ Delete Player", expanded=False):
        if not players_data:
            st.warning("No players available to delete.")
        else:
            player_options = {f"{player['name']} ({player['skill_level']}) [ID {player['id']}]": player["id"] for player in players_data}
            with st.form("form_delete_player"):
                selected_player_label = st.selectbox(
                    "Select Player to Delete",
                    list(player_options.keys()),
                    key="player_delete_select",
                )
                confirm_delete_player = st.checkbox("I understand this action cannot be undone")
                submit_delete_player = st.form_submit_button("Delete Player")

                if submit_delete_player:
                    if not confirm_delete_player:
                        st.warning("Please confirm before deleting.")
                    else:
                        try:
                            player_id = player_options[selected_player_label]
                            res = requests.delete(f"{API_URL}/players/{player_id}")
                            if res.status_code == 200:
                                st.success("Player deleted successfully!")
                                rerun_with_refresh()
                            else:
                                st.error(f"Delete failed: {res.text}")
                        except requests.RequestException as exc:
                            st.error(f"Request failed: {exc}")

    st.subheader("Current Players")
    if players_data:
        st.dataframe(players_data, use_container_width=True)
    else:
        st.info("No players found.")

# ==========================================
# TAB 3: GAMES
# ==========================================
with tab_games:
    st.header("Games Management")
    
    with st.expander("➕ Schedule a New Game", expanded=False):
        if not courts_data:
            st.warning("Please create a Court first before scheduling a game.")
        else:
            with st.form("form_add_game"):
                g_date = st.date_input("Date", min_value=datetime.today())
                g_time = st.time_input("Time")
                
                court_options = {f"{c['name']} ({c['city']})": c['id'] for c in courts_data}
                selected_court_label = st.selectbox("Select Court", list(court_options.keys()))
                
                g_skill = st.selectbox("Target Skill Level", ["beginner", "intermediate", "advanced"])
                g_max_players = st.number_input("Max Players", min_value=2, max_value=20, value=10)
                
                submit_game = st.form_submit_button("Schedule Game")
                
                if submit_game:
                    try:
                        dt_combined = datetime.combine(g_date, g_time).isoformat()
                        court_id = court_options[selected_court_label]

                        payload = {
                            "scheduled_time": dt_combined,
                            "court_id": court_id,
                            "skill_level": g_skill,
                            "max_players": g_max_players,
                            "status": "open",
                        }
                        res = requests.post(f"{API_URL}/games/", json=payload)
                        if res.status_code == 200:
                            st.success("Game scheduled successfully!")
                            rerun_with_refresh()
                        else:
                            st.error(f"Error: {res.text}")
                    except requests.RequestException as exc:
                        st.error(f"Request failed: {exc}")

    with st.expander("🤝 Register Player to Game", expanded=False):
        open_games_data = [game for game in games_data if game["status"] == "open"]
        if not players_data:
            st.warning("You need at least one game and one player to register.")
        elif not open_games_data:
            st.warning("No open games available for registration.")
        else:
            with st.form("form_register_player"):
                game_options = {
                    f"Game ID {game['id']} - {game['scheduled_time'][:10]}": game['id']
                    for game in open_games_data
                }
                player_options = {
                    f"{player['name']} ({player['skill_level']}) [ID {player['id']}]": player['id']
                    for player in players_data
                }
                
                selected_game = st.selectbox("Select Game", list(game_options.keys()), key="game_register_select")
                selected_player = st.selectbox("Select Player", list(player_options.keys()), key="player_register_select")
                
                submit_registration = st.form_submit_button("Register Player")
                
                if submit_registration:
                    try:
                        g_id = game_options[selected_game]
                        p_id = player_options[selected_player]

                        res = requests.post(f"{API_URL}/games/{g_id}/players/{p_id}")
                        if res.status_code == 200:
                            st.success("Player successfully registered to the game!")
                            rerun_with_refresh()
                        elif res.status_code == 400:
                            st.error("Player is already registered to this game!")
                        else:
                            st.error(f"Registration failed: {res.text}")
                    except requests.RequestException as exc:
                        st.error(f"Request failed: {exc}")

    with st.expander("🗑️ Delete Game", expanded=False):
        if not games_data:
            st.warning("No games available to delete.")
        else:
            game_options = {
                f"Game ID {game['id']} - {game['scheduled_time'][:10]}": game['id']
                for game in games_data
            }
            with st.form("form_delete_game"):
                selected_game = st.selectbox(
                    "Select Game to Delete",
                    list(game_options.keys()),
                    key="game_delete_select",
                )
                confirm_delete_game = st.checkbox("I understand this action cannot be undone")
                submit_delete_game = st.form_submit_button("Delete Game")

                if submit_delete_game:
                    if not confirm_delete_game:
                        st.warning("Please confirm before deleting.")
                    else:
                        try:
                            game_id = game_options[selected_game]
                            res = requests.delete(f"{API_URL}/games/{game_id}")
                            if res.status_code == 200:
                                st.success("Game deleted successfully!")
                                rerun_with_refresh()
                            else:
                                st.error(f"Delete failed: {res.text}")
                        except requests.RequestException as exc:
                            st.error(f"Request failed: {exc}")

    with st.expander("✏️ Update Game", expanded=False):
        if not games_data:
            st.warning("No games available to update.")
        elif not courts_data:
            st.warning("No courts available to update game details.")
        else:
            game_options = {
                f"Game ID {game['id']} - {game['scheduled_time'][:10]}": game
                for game in games_data
            }
            selected_game_label = st.selectbox(
                "Select Game",
                list(game_options.keys()),
                key="game_update_select",
            )
            selected_game = game_options[selected_game_label]
            selected_game_dt = datetime.fromisoformat(selected_game["scheduled_time"])
            court_options = {
                f"{court['name']} ({court['city']}) [ID {court['id']}]": court["id"]
                for court in courts_data
            }
            court_labels = list(court_options.keys())
            current_court_label = next(
                (
                    label
                    for label, court_id in court_options.items()
                    if court_id == selected_game["court_id"]
                ),
                court_labels[0],
            )

            with st.form("form_update_game"):
                updated_date = st.date_input(
                    "Scheduled Date",
                    value=selected_game_dt.date(),
                    key=f"game_update_date_{selected_game['id']}",
                )
                updated_time = st.time_input(
                    "Scheduled Time",
                    value=selected_game_dt.time().replace(second=0, microsecond=0),
                    key=f"game_update_time_{selected_game['id']}",
                )
                updated_court_label = st.selectbox(
                    "Court",
                    court_labels,
                    index=safe_index(court_labels, current_court_label),
                    key=f"game_update_court_{selected_game['id']}",
                )
                updated_skill = st.selectbox(
                    "Skill Level",
                    ["beginner", "intermediate", "advanced"],
                    index=safe_index(
                        ["beginner", "intermediate", "advanced"],
                        selected_game["skill_level"],
                    ),
                    key=f"game_update_skill_{selected_game['id']}",
                )
                updated_max_players = st.number_input(
                    "Max Players",
                    min_value=2,
                    max_value=20,
                    value=int(selected_game["max_players"]),
                    key=f"game_update_max_players_{selected_game['id']}",
                )
                updated_status = st.selectbox(
                    "Status",
                    ["open", "full", "cancelled", "completed"],
                    index=safe_index(
                        ["open", "full", "cancelled", "completed"],
                        selected_game["status"],
                    ),
                    key=f"game_update_status_{selected_game['id']}",
                )

                submit_update = st.form_submit_button("Update Game")

                if submit_update:
                    try:
                        selected_court_id = court_options[updated_court_label]
                        updated_scheduled_time = datetime.combine(
                            updated_date,
                            updated_time,
                        ).isoformat()

                        normalized_selected_game = {
                            **selected_game,
                            "scheduled_time": datetime.fromisoformat(
                                selected_game["scheduled_time"]
                            ).isoformat(),
                        }

                        payload = build_partial_payload(
                            normalized_selected_game,
                            {
                                "scheduled_time": updated_scheduled_time,
                                "court_id": selected_court_id,
                                "skill_level": updated_skill,
                                "max_players": updated_max_players,
                                "status": updated_status,
                            },
                        )

                        if not payload:
                            st.info("No changes were made.")
                        else:
                            res = requests.patch(
                                f"{API_URL}/games/{selected_game['id']}",
                                json=payload,
                            )

                            if res.status_code == 200:
                                st.success("Game updated successfully!")
                                rerun_with_refresh()
                            else:
                                st.error(f"Update failed: {res.text}")
                    except requests.RequestException as exc:
                        st.error(f"Request failed: {exc}")

    st.subheader("Upcoming Games")
    if games_data:
        display_games = []
        now_iso = datetime.now().isoformat()
        for game in games_data:
            if game["status"] != "open" or game["scheduled_time"] <= now_iso:
                continue

            current_players = len(game.get("players", []))

            display_games.append(
                {
                    "ID": game["id"],
                    "Court": court_names_by_id.get(game["court_id"], f"Court ID {game['court_id']}"),
                    "Date": game["scheduled_time"][:10],
                    "Time": game["scheduled_time"][11:16],
                    "Skill Level": game["skill_level"],
                    "Status": game["status"],
                    "Occupancy": f"{current_players}/{game['max_players']} Players",
                }
            )

        if display_games:
            st.dataframe(display_games, use_container_width=True)
        else:
            st.info("No upcoming open games at the moment.")
    else:
        st.info("No games scheduled yet.")