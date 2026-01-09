import pandas as pd

POLLS_FILE = "polls.csv"
POLL_TYPES_FILE = "poll_types.csv"
CANDIDATES_FILE = "candidates.csv"


def load_data(file_path):
    return pd.read_csv(file_path)


def get_poll_file_path(poll, population):
    return f"{poll['folder']}/{poll['poll_id']}_{population}.csv"


def add_poll_metadata(poll_df, poll):
    for col, value in poll.items():
        poll_df[col] = value
    return poll_df


def add_poll_type_metadata(poll_df, poll_type):
    for col, value in poll_type.items():
        poll_df[col] = value
    return poll_df


def merge_candidate_metadata(poll_df, candidates):

    candidates = candidates.copy()

    # create a new column with the name and surname of the candidate
    candidates["candidate"] = candidates["name"] + " " + candidates["surname"]

    #  keep only the candidate_id in the poll_df
    candidates = candidates[candidates["candidate_id"].isin(poll_df["candidate_id"].unique())]

    # If poll_df already has 'candidate', drop it to avoid candidate_x/candidate_y
    poll_df = poll_df.drop(columns=["candidate"], errors="ignore")

    return poll_df.merge(candidates, on="candidate_id", how="right")


def process_polls(polls, poll_types, candidates, population):
    merged_df = pd.DataFrame()

    for i, poll in polls.iterrows():
        print(poll)
        poll_file_path = get_poll_file_path(poll, population)
        poll_df = load_data(poll_file_path)
        poll_type_id = poll_df["poll_type_id"].unique()[0]

        poll_df = add_poll_metadata(poll_df, poll)
        poll_type = poll_types[poll_types["id"] == poll_type_id].iloc[0]
        poll_df = add_poll_type_metadata(poll_df, poll_type)
        poll_df = merge_candidate_metadata(poll_df, candidates)

        merged_df = pd.concat([merged_df, poll_df], ignore_index=True)

    return merged_df


def main():

    POPULATIONS = ["all", "left", "farright", "macron", "absentionists"]

    for POPULATION in POPULATIONS:
        print(POPULATION)
        OUTPUT_FILE = f"mj2027_{POPULATION}.csv" if POPULATION != "all" else "mj2027.csv"

        print(POLLS_FILE)
        polls = load_data(POLLS_FILE)
        polls = polls[polls["population"] == POPULATION]

        poll_types = load_data(POLL_TYPES_FILE)
        candidates = load_data(CANDIDATES_FILE)

        print(polls)

        merged_df = process_polls(polls, poll_types, candidates, POPULATION)
        merged_df.to_csv(OUTPUT_FILE, index=False)


if __name__ == "__main__":
    main()
